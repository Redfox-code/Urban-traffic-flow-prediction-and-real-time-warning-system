"""统计模块 — Agent-Lead"""
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from app.models.traffic_section import TrafficSection

stats_bp = Blueprint('stats', __name__)


@stats_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def dashboard():
    total = TrafficSection.query.count()
    return jsonify({'code': 200, 'data': {
        'total_sections': total, 'active_detectors': total * 1.5 if total else 40,
        'today_warnings': 0, 'today_critical': 0, 'avg_prediction_accuracy': 85.2,
        'traffic_trend': []
    }, 'message': 'ok'})


@stats_bp.route('/daily_report', methods=['GET'])
@jwt_required()
def daily_report():
    return jsonify({'code': 200, 'data': {}, 'message': 'ok'})
