"""流量数据模块 — /api/v1/traffic/* — Agent-Algorithm 负责"""
from flask import Blueprint, jsonify

traffic_bp = Blueprint('traffic', __name__)


@traffic_bp.route('/current', methods=['GET'])
def current_traffic():
    """GET /api/v1/traffic/current — 实时路况"""
    # TODO D7-D8: Agent-Algorithm 实现
    return jsonify({'code': 200, 'data': [], 'message': 'ok'})


@traffic_bp.route('/history', methods=['GET'])
def history_traffic():
    """GET /api/v1/traffic/history — 历史流量记录"""
    # TODO D7-D8: Agent-Algorithm 实现
    return jsonify({'code': 200, 'data': {'items': [], 'total': 0, 'page': 1, 'page_size': 20}, 'message': 'ok'})
