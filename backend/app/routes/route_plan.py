"""路径规划模块 — Agent-Lead"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.route_service import plan_route
from app.models.traffic_section import TrafficSection
from app.models.traffic_record import TrafficRecord
from app.models.route_record import RouteRecord
from app import db
from datetime import datetime, timedelta

route_bp = Blueprint('route', __name__)


def _get_latest_traffic():
    """获取所有路段的最新实时路况数据，返回 {section_id: {...}} 字典"""
    # 取最近10分钟内的最新记录
    cutoff = datetime.utcnow() - timedelta(minutes=10)
    records = (TrafficRecord.query
               .filter(TrafficRecord.timestamp >= cutoff)
               .order_by(TrafficRecord.timestamp.desc())
               .all())
    # 每个section只取最新一条
    traffic_map = {}
    for r in records:
        if r.section_id not in traffic_map:
            traffic_map[r.section_id] = {
                'vehicle_count': r.vehicle_count,
                'avg_speed': float(r.avg_speed) if r.avg_speed else 0,
                'occupancy': float(r.occupancy) if r.occupancy else 0,
            }
    return traffic_map


@route_bp.route('/plan', methods=['POST'])
@jwt_required()
def plan():
    data = request.get_json(silent=True) or {}
    origin = data.get('origin_section_id')
    dest = data.get('dest_section_id')
    if not origin or not dest:
        return jsonify({'code': 400, 'data': None, 'message': '缺少起终点路段ID'}), 400

    if origin == dest:
        return jsonify({'code': 422, 'data': None, 'message': '起点和终点不能相同'}), 422

    path_detail, distance, route_segments, estimated_time, error = plan_route(origin, dest)
    if error:
        return jsonify({'code': 422, 'data': None, 'message': error}), 422

    # 获取实时路况数据，注入到路径详情中
    traffic_map = _get_latest_traffic()
    total_weighted_speed = 0
    total_length = 0

    for step in path_detail:
        sid = step['section_id']
        td = traffic_map.get(sid)
        if td:
            step['occupancy'] = td['occupancy']
            step['avg_speed'] = td['avg_speed']
            step['vehicle_count'] = td['vehicle_count']
            seg_len = step.get('length', 0) or 0
            step_speed = td['avg_speed'] if td['avg_speed'] > 0 else 30
            total_weighted_speed += step_speed * seg_len
            total_length += seg_len

    # 动态计算预估时间：优先用实时路况速度加权平均，fallback用Dijkstra时间成本
    if total_length > 0 and total_weighted_speed > 0:
        avg_speed = total_weighted_speed / total_length
        estimated_time = max(1, int(distance / avg_speed * 60))
    # else: 使用plan_route返回的estimated_time（已基于Amap speed计算）

    # 保存到数据库
    user_id = get_jwt_identity()
    record = RouteRecord(
        user_id=int(user_id),
        origin_section_id=origin,
        dest_section_id=dest,
        route_path=path_detail,
        total_distance=round(distance, 2),
        estimated_time=estimated_time,
    )
    db.session.add(record)
    db.session.commit()

    return jsonify({'code': 200, 'data': {
        'route_id': record.id,
        'path': path_detail,
        'total_distance': round(distance, 2),
        'estimated_time': estimated_time,
        'route_segments': route_segments,  # 每个路段独立坐标，前端分段绘制
    }, 'message': 'ok'})


@route_bp.route('/<int:route_id>', methods=['GET'])
@jwt_required()
def get_route(route_id):
    record = RouteRecord.query.get(route_id)
    if not record:
        return jsonify({'code': 404, 'data': None, 'message': '路径记录不存在'}), 404

    return jsonify({'code': 200, 'data': {
        'route_id': record.id,
        'origin_section_id': record.origin_section_id,
        'dest_section_id': record.dest_section_id,
        'path': record.route_path,
        'total_distance': float(record.total_distance),
        'estimated_time': record.estimated_time,
        'created_at': record.created_at.isoformat(),
    }, 'message': 'ok'})
