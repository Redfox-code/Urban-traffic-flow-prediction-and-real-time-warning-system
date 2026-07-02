"""路径规划模块 — Agent-Lead"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.services.route_service import plan_route
from app.models.traffic_section import TrafficSection
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
        path_detail.append({'section_id': sid, 'name': s.name if s else str(sid), 'length': float(s.length) if s else 0})

    return jsonify({'code': 200, 'data': {
        'route_id': hash((origin, dest)) % 10000,
        'path': path_detail, 'total_distance': round(distance, 2), 'estimated_time': int(distance / 30 * 60)
    }, 'message': 'ok'})


@route_bp.route('/<int:route_id>', methods=['GET'])
@jwt_required()
def get_route(route_id):
    # TODO D10: 数据库查询历史路径
    return jsonify({'code': 200, 'data': {}, 'message': 'ok'})
