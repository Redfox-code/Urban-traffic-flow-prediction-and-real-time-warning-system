"""流量模块 — /api/v1/traffic/* — Agent-Algorithm + Agent-Lead"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from sqlalchemy import func
from app import db
from app.models.traffic_section import TrafficSection
from app.models.traffic_record import TrafficRecord
import random

traffic_bp = Blueprint('traffic', __name__)


def _mock_traffic(section):
    """Fallback: 无数据库记录时生成mock数据(带时序波动)"""
    import time
    hour = 10
    peak = 1.8 if hour in [7, 8, 17, 18] else 1.0
    # 基于时间种子产生自然波动，每秒数据都不同
    t = int(time.time())
    wave = random.uniform(-15, 15) * peak
    capacity = section.capacity or 1500
    occupancy = min(95, abs(random.uniform(15, 85) * peak + wave))
    avg_speed = max(5, section.max_speed * (1 - occupancy / 100) * random.uniform(0.8, 1.2))
    vehicle_count = int(capacity * occupancy / 100 * random.uniform(0.8, 1.2))
    if occupancy < 30: level = 'smooth'
    elif occupancy < 60: level = 'slow'
    elif occupancy < 85: level = 'congested'
    else: level = 'jammed'
    return {'section_id': section.id, 'section_name': section.name,
            'vehicle_count': vehicle_count, 'avg_speed': round(avg_speed, 1),
            'occupancy': round(occupancy, 1), 'level': level,
            'timestamp': '2026-07-02T10:00:00', 'source': 'mock'}


def _real_traffic(section):
    """从数据库读取该路段最新流量记录"""
    record = TrafficRecord.query \
        .filter_by(section_id=section.id) \
        .order_by(TrafficRecord.timestamp.desc()) \
        .first()
    if not record:
        return None
    occ = float(record.occupancy)
    if occ < 30: level = 'smooth'
    elif occ < 60: level = 'slow'
    elif occ < 85: level = 'congested'
    else: level = 'jammed'
    return {'section_id': section.id, 'section_name': section.name,
            'vehicle_count': record.vehicle_count,
            'avg_speed': float(record.avg_speed),
            'occupancy': occ, 'level': level,
            'timestamp': record.timestamp.isoformat(),
            'source': 'db'}


@traffic_bp.route('/current', methods=['GET'])
@jwt_required()
def current_traffic():
    section_id = request.args.get('section_id', type=int)
    sections = TrafficSection.query.all()
    if section_id:
        sections = [s for s in sections if s.id == section_id]

    # 优先从数据库读取，空则fallback到mock
    has_db_data = TrafficRecord.query.first() is not None
    data = []
    for s in sections:
        if has_db_data:
            real = _real_traffic(s)
            data.append(real if real else _mock_traffic(s))
        else:
            data.append(_mock_traffic(s))

    return jsonify({'code': 200, 'data': data, 'message': 'ok'})


@traffic_bp.route('/history', methods=['GET'])
@jwt_required()
def history_traffic():
    section_id = request.args.get('section_id', type=int)
    page = request.args.get('page', 1, type=int)
    page_size = min(request.args.get('page_size', 20, type=int), 100)

    query = TrafficRecord.query
    if section_id:
        query = query.filter_by(section_id=section_id)
    pagination = query.order_by(TrafficRecord.timestamp.desc()) \
        .paginate(page=page, per_page=page_size, error_out=False)

    items = [{'id': r.id, 'section_id': r.section_id, 'detector_id': r.detector_id,
              'vehicle_count': r.vehicle_count, 'avg_speed': float(r.avg_speed),
              'occupancy': float(r.occupancy), 'timestamp': r.timestamp.isoformat()}
             for r in pagination.items]
    return jsonify({'code': 200, 'data': {
        'items': items, 'total': pagination.total,
        'page': page, 'page_size': page_size, 'total_pages': pagination.pages
    }, 'message': 'ok'})
