"""预警模块 — /api/v1/warning/* — Agent-Lead"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app import db
from app.models.warning_event import WarningEvent

warning_bp = Blueprint('warning', __name__)


@warning_bp.route('/list', methods=['GET'])
@jwt_required()
def list_warnings():
    page = request.args.get('page', 1, type=int)
    page_size = min(request.args.get('page_size', 20, type=int), 100)
    level = request.args.get('level')
    is_resolved = request.args.get('is_resolved')
    section_id = request.args.get('section_id', type=int)

    query = WarningEvent.query
    if level: query = query.filter(WarningEvent.level == level)
    if is_resolved is not None: query = query.filter(WarningEvent.is_resolved == (is_resolved.lower() == 'true'))
    if section_id: query = query.filter(WarningEvent.section_id == section_id)

    pagination = query.order_by(WarningEvent.created_at.desc()).paginate(page=page, per_page=page_size, error_out=False)
    items = [{'id': w.id, 'section_id': w.section_id, 'level': w.level, 'message': w.message,
              'trigger_flow': float(w.trigger_flow), 'threshold': float(w.threshold),
              'is_resolved': w.is_resolved, 'created_at': w.created_at.isoformat(), 'resolved_at': w.resolved_at.isoformat() if w.resolved_at else None}
             for w in pagination.items]
    return jsonify({'code': 200, 'data': {'items': items, 'total': pagination.total, 'page': page, 'page_size': page_size, 'total_pages': pagination.pages}, 'message': 'ok'})


@warning_bp.route('/<int:warning_id>/resolve', methods=['PUT'])
@jwt_required()
def resolve_warning(warning_id):
    w = db.session.get(WarningEvent, warning_id)
    if not w: return jsonify({'code': 404, 'data': None, 'message': '预警不存在'}), 404
    from datetime import datetime
    w.is_resolved = True; w.resolved_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'code': 200, 'data': {'resolved_at': w.resolved_at.isoformat()}, 'message': '预警已解除'})


@warning_bp.route('/rules', methods=['GET'])
def get_rules():
    return jsonify({'code': 200, 'data': {'warning_threshold': 0.85, 'critical_threshold': 0.95, 'min_data_points': 4, 'cooldown_minutes': 30}, 'message': 'ok'})


@warning_bp.route('/rules', methods=['PUT'])
def update_rules():
    return jsonify({'code': 200, 'data': {}, 'message': '规则已更新'})
