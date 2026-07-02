"""流量模块 — /api/v1/traffic/* — Agent-Algorithm"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

traffic_bp = Blueprint('traffic', __name__)


@traffic_bp.route('/current', methods=['GET'])
def current_traffic():
    section_id = request.args.get('section_id', type=int)
    # TODO D9: 从Redis/DB查询实时路况
    data = [{'section_id': 1, 'section_name': '主干道-南北1', 'vehicle_count': 85,
             'avg_speed': 42.5, 'occupancy': 35.2, 'level': 'slow',
             'timestamp': '2026-07-02T10:00:00'}]
    if section_id:
        data = [d for d in data if d['section_id'] == section_id]
    return jsonify({'code': 200, 'data': data, 'message': 'ok'})


@traffic_bp.route('/history', methods=['GET'])
def history_traffic():
    # TODO D9: 数据库分页查询
    return jsonify({'code': 200, 'data': {'items': [], 'total': 0, 'page': 1, 'page_size': 20, 'total_pages': 0}, 'message': 'ok'})
