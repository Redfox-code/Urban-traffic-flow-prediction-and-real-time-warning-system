"""流量模块 — /api/v1/traffic/* — Agent-Algorithm"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.models.traffic_section import TrafficSection
import random

traffic_bp = Blueprint('traffic', __name__)


def _mock_traffic(section):
    """为路段生成实时路况mock数据（课程项目：无真实SUMO数据时使用）"""
    hour = 10  # 模拟上午10点
    peak = 1.8 if hour in [7, 8, 17, 18] else 1.0
    capacity = section.capacity or 1500
    occupancy = min(95, random.uniform(15, 85) * peak)
    avg_speed = max(5, section.max_speed * (1 - occupancy / 100) * random.uniform(0.8, 1.2))
    vehicle_count = int(capacity * occupancy / 100 * random.uniform(0.8, 1.2))

    if occupancy < 30: level = 'smooth'
    elif occupancy < 60: level = 'slow'
    elif occupancy < 85: level = 'congested'
    else: level = 'jammed'

    return {
        'section_id': section.id, 'section_name': section.name,
        'vehicle_count': vehicle_count, 'avg_speed': round(avg_speed, 1),
        'occupancy': round(occupancy, 1), 'level': level,
        'timestamp': '2026-07-02T10:00:00'
    }


@traffic_bp.route('/current', methods=['GET'])
@jwt_required()
def current_traffic():
    section_id = request.args.get('section_id', type=int)
    sections = TrafficSection.query.all()
    if section_id:
        sections = [s for s in sections if s.id == section_id]
    data = [_mock_traffic(s) for s in sections]
    return jsonify({'code': 200, 'data': data, 'message': 'ok'})


@traffic_bp.route('/history', methods=['GET'])
@jwt_required()
def history_traffic():
    return jsonify({'code': 200, 'data': {'items': [], 'total': 0, 'page': 1, 'page_size': 20, 'total_pages': 0}, 'message': 'ok'})
