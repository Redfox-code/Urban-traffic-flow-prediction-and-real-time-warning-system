"""路径规划模块 — /api/v1/route/* — Agent-Lead 负责"""
from flask import Blueprint, jsonify

route_bp = Blueprint('route', __name__)


@route_bp.route('/plan', methods=['POST'])
def plan_route():
    """POST /api/v1/route/plan — 计算最优路径"""
    # TODO D9: 实现Dijkstra路径规划
    return jsonify({'code': 200, 'data': {}, 'message': 'ok'})


@route_bp.route('/<int:route_id>', methods=['GET'])
def get_route(route_id):
    """GET /api/v1/route/{id} — 查询历史路径"""
    # TODO D9: 实现查询
    return jsonify({'code': 200, 'data': {}, 'message': 'ok'})
