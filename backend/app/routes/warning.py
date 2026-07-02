"""预警模块 — /api/v1/warning/* — Agent-Lead 负责"""
from flask import Blueprint, jsonify

warning_bp = Blueprint('warning', __name__)


@warning_bp.route('/list', methods=['GET'])
def list_warnings():
    """GET /api/v1/warning/list — 预警列表"""
    # TODO D8: 实现预警查询
    return jsonify({'code': 200, 'data': {'items': [], 'total': 0, 'page': 1, 'page_size': 20}, 'message': 'ok'})


@warning_bp.route('/<int:warning_id>/resolve', methods=['PUT'])
def resolve_warning(warning_id):
    """PUT /api/v1/warning/{id}/resolve — 解除预警"""
    # TODO D8: 实现预警解除
    return jsonify({'code': 200, 'data': {}, 'message': 'ok'})


@warning_bp.route('/rules', methods=['GET'])
def get_rules():
    """GET /api/v1/warning/rules — 获取预警规则"""
    # TODO D8: 返回预警阈值配置
    return jsonify({'code': 200, 'data': {
        'warning_threshold': 0.85, 'critical_threshold': 0.95,
        'min_data_points': 4, 'cooldown_minutes': 30
    }, 'message': 'ok'})


@warning_bp.route('/rules', methods=['PUT'])
def update_rules():
    """PUT /api/v1/warning/rules — 更新预警规则"""
    # TODO D8: 实现规则更新
    return jsonify({'code': 200, 'data': {}, 'message': 'ok'})
