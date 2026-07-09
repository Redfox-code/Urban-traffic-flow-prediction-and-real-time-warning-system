"""路径规划模块 — Agent-Lead"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.route_service import plan_route
from app.models.traffic_section import TrafficSection
from app.models.route_record import RouteRecord
from app import db

route_bp = Blueprint('route', __name__)


@route_bp.route('/plan', methods=['POST'])
@jwt_required()
def plan():
    data = request.get_json(silent=True) or {}
    origin = data.get('origin_section_id')
    dest = data.get('dest_section_id')
    if not origin or not dest:
        return jsonify({'code': 400, 'data': None, 'message': '缺少起终点路段ID'}), 400

    path, distance, error = plan_route(origin, dest)
    if error:
        return jsonify({'code': 422, 'data': None, 'message': error}), 422

    sections = {s.id: s for s in TrafficSection.query.filter(TrafficSection.id.in_(path)).all()}
    path_detail = []
    for sid in path:
        s = sections.get(sid)
        path_detail.append({
            'section_id': sid,
            'name': s.name if s else str(sid),
            'length': float(s.length) if s else 0,
        })

    estimated_time = int(distance / 30 * 60)  # 平均30km/h

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
