"""统计模块 — /api/v1/stats/* — Agent-Lead 负责"""
from flask import Blueprint, jsonify

stats_bp = Blueprint('stats', __name__)


@stats_bp.route('/dashboard', methods=['GET'])
def dashboard():
    """GET /api/v1/stats/dashboard — Dashboard概览"""
    # TODO D8: 实现统计查询
    return jsonify({'code': 200, 'data': {
        'total_sections': 0, 'active_detectors': 0,
        'today_warnings': 0, 'today_critical': 0,
        'avg_prediction_accuracy': 0, 'traffic_trend': []
    }, 'message': 'ok'})


@stats_bp.route('/daily_report', methods=['GET'])
def daily_report():
    """GET /api/v1/stats/daily_report — 日报"""
    # TODO D8: 实现日报生成
    return jsonify({'code': 200, 'data': {}, 'message': 'ok'})
