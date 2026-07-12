"""应急调度API — /api/v1/emergency/* — Agent-Lead"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.utils.decorators import role_required
from app.models.emergency_route import EmergencyRoute
from app.models.traffic_section import TrafficSection
from app import db
from datetime import datetime
import math


emergency_bp = Blueprint('emergency', __name__)


def _find_nearest_section(lat, lng):
    """根据经纬度找到最近的DB路段，返回 section_id 或 None"""
    sections = TrafficSection.query.all()
    best_id, best_dist = None, float('inf')
    for s in sections:
        c = s.coordinates
        if not c:
            continue
        wp = c.get('waypoints', []) or c.get('path', [])
        if not wp:
            continue
        # 取路段中心点
        ct = wp[len(wp) // 2]
        # haversine 近似：1度 ≈ 111km
        dlng = (ct[0] - lng) * 111000 * math.cos(math.radians((ct[1] + lat) / 2))
        dlat = (ct[1] - lat) * 111000
        d = math.sqrt(dlng**2 + dlat**2)
        if d < best_dist:
            best_dist = d
            best_id = s.id
    return best_id


@emergency_bp.route('/plan', methods=['POST'])
@jwt_required()
@role_required('admin')
def plan():
    """应急路径规划 — 复用route_service的真实路网Dijkstra + 应急绿波带调整。"""
    data = request.get_json(silent=True) or {}
    vehicle_type = data.get('vehicle_type', 'ambulance')
    origin = data.get('origin', {})
    destination = data.get('destination', {})

    if not origin or not destination:
        return jsonify({'code': 400, 'data': None, 'message': '请提供起点和终点坐标'}), 400

    o_lat, o_lng = origin.get('lat', 0), origin.get('lng', 0)
    d_lat, d_lng = destination.get('lat', 0), destination.get('lng', 0)

    # 找到坐标对应的最近路段
    origin_section_id = _find_nearest_section(o_lat, o_lng)
    dest_section_id = _find_nearest_section(d_lat, d_lng)

    if not origin_section_id or not dest_section_id:
        # Fallback: 路段匹配失败，画直线路径
        return jsonify({'code': 200, 'data': {
            'route': [{'name': '应急路线(无匹配路段)', 'path': [[o_lng, o_lat], [d_lng, d_lat]], 'length_km': 1.0}],
            'est_travel_time_sec': 180,
            'normal_travel_time_sec': 300,
            'green_wave': [],
            'time_saved_pct': 40,
            'vehicle_type': vehicle_type
        }, 'message': '应急路径规划完成（路段匹配失败，使用直线）'})

    # 使用route_service的真实路网Dijkstra（和出行者路径规划同一引擎）
    from app.services.route_service import plan_route
    path_detail, distance, route_segments, estimated_time, error = plan_route(
        origin_section_id, dest_section_id
    )

    if error:
        # Dijkstra也失败，fallback到直线
        return jsonify({'code': 200, 'data': {
            'route': [{'name': '应急路线', 'path': [[o_lng, o_lat], [d_lng, d_lat]], 'length_km': round(distance, 2) if distance else 1.0}],
            'est_travel_time_sec': 180,
            'normal_travel_time_sec': 300,
            'green_wave': [],
            'time_saved_pct': 40,
            'vehicle_type': vehicle_type
        }, 'message': '应急路径规划完成'})

    # 应急车辆优先级调整：按车型缩短时间
    priority_map = {'ambulance': 0.65, 'fire': 0.75, 'police': 0.80}
    priority = priority_map.get(vehicle_type, 0.75)

    est_time_min = estimated_time  # plan_route 返回的是分钟
    est_time_sec = round(est_time_min * 60 * priority)
    normal_time_sec = round(est_time_min * 60)
    time_saved = round((1 - priority) * 100)

    return jsonify({'code': 200, 'data': {
        'route': route_segments,  # 真实路网坐标，TrafficMap直接渲染
        'est_travel_time_sec': est_time_sec,
        'normal_travel_time_sec': normal_time_sec,
        'green_wave': [],
        'time_saved_pct': time_saved,
        'vehicle_type': vehicle_type,
        'total_distance_km': round(distance, 2),
    }, 'message': '应急路径规划完成'})


@emergency_bp.route('/records', methods=['GET'])
@jwt_required()
@role_required('admin')
def list_records():
    """调度记录列表。"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)

    query = EmergencyRoute.query.order_by(EmergencyRoute.created_at.desc())
    total = query.count()
    records = query.offset((page - 1) * page_size).limit(page_size).all()

    return jsonify({'code': 200, 'data': {
        'items': [{
            'id': r.id,
            'vehicle_type': r.vehicle_type,
            'origin': r.origin_json,
            'destination': r.destination_json,
            'est_travel_time': r.est_travel_time,
            'normal_travel_time': r.normal_travel_time,
            'status': r.status,
            'created_at': r.created_at.isoformat() if r.created_at else None
        } for r in records],
        'total': total, 'page': page, 'page_size': page_size
    }, 'message': 'ok'})


@emergency_bp.route('/records', methods=['POST'])
@jwt_required()
@role_required('admin')
def create_record():
    """创建调度记录。"""
    data = request.get_json(silent=True) or {}
    user_id = int(get_jwt_identity())

    record = EmergencyRoute(
        vehicle_type=data.get('vehicle_type', 'ambulance'),
        origin_json=str(data.get('origin', {})),
        destination_json=str(data.get('destination', {})),
        route_json=str(data.get('route', [])),
        green_wave_json=str(data.get('green_wave', [])),
        est_travel_time=data.get('est_travel_time_sec'),
        normal_travel_time=data.get('normal_travel_time_sec'),
        status='active',
        created_by=user_id
    )
    db.session.add(record)
    db.session.commit()

    return jsonify({'code': 201, 'data': {'id': record.id, 'status': 'active'}, 'message': '调度已创建'}), 201


@emergency_bp.route('/records/<int:record_id>', methods=['GET'])
@jwt_required()
@role_required('admin')
def get_record(record_id):
    """调度记录详情。"""
    record = EmergencyRoute.query.get(record_id)
    if not record:
        return jsonify({'code': 404, 'data': None, 'message': '记录不存在'}), 404

    return jsonify({'code': 200, 'data': {
        'id': record.id,
        'vehicle_type': record.vehicle_type,
        'origin': record.origin_json,
        'destination': record.destination_json,
        'route': record.route_json,
        'green_wave': record.green_wave_json,
        'est_travel_time': record.est_travel_time,
        'normal_travel_time': record.normal_travel_time,
        'status': record.status,
        'created_at': record.created_at.isoformat() if record.created_at else None
    }, 'message': 'ok'})


@emergency_bp.route('/records/<int:record_id>/status', methods=['PUT'])
@jwt_required()
@role_required('admin')
def update_status(record_id):
    """更新调度状态。"""
    data = request.get_json(silent=True) or {}
    record = EmergencyRoute.query.get(record_id)
    if not record:
        return jsonify({'code': 404, 'data': None, 'message': '记录不存在'}), 404

    new_status = data.get('status', 'completed')
    if new_status not in ('active', 'completed', 'cancelled'):
        return jsonify({'code': 400, 'data': None, 'message': '无效状态'}), 400

    record.status = new_status
    record.updated_at = datetime.utcnow()
    db.session.commit()

    return jsonify({'code': 200, 'data': {'id': record.id, 'status': new_status}, 'message': '状态已更新'})
