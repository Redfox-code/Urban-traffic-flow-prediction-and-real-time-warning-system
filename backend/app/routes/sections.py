"""路段模块 — /api/v1/sections/* — Agent-Lead"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app import db
from app.models.traffic_section import TrafficSection

sections_bp = Blueprint('sections', __name__)


@sections_bp.route('', methods=['GET'])
def list_sections():
    page = request.args.get('page', 1, type=int)
    page_size = min(request.args.get('page_size', 20, type=int), 100)
    query = TrafficSection.query
    if name := request.args.get('name'):
        query = query.filter(TrafficSection.name.contains(name))
    pagination = query.paginate(page=page, per_page=page_size, error_out=False)
    items = [{'id': s.id, 'name': s.name, 'capacity': s.capacity, 'length': float(s.length),
              'max_speed': s.max_speed, 'coordinates': s.coordinates, 'created_at': s.created_at.isoformat()}
             for s in pagination.items]
    return jsonify({'code': 200, 'data': {'items': items, 'total': pagination.total, 'page': page, 'page_size': page_size, 'total_pages': pagination.pages}, 'message': 'ok'})


@sections_bp.route('/<int:section_id>', methods=['GET'])
@jwt_required()
def get_section(section_id):
    s = db.session.get(TrafficSection, section_id)
    if not s: return jsonify({'code': 404, 'data': None, 'message': '路段不存在'}), 404
    return jsonify({'code': 200, 'data': {'id': s.id, 'name': s.name, 'capacity': s.capacity, 'length': float(s.length), 'max_speed': s.max_speed, 'coordinates': s.coordinates}, 'message': 'ok'})


@sections_bp.route('', methods=['POST'])
@jwt_required()
def create_section():
    data = request.get_json(silent=True) or {}
    if not data.get('name'): return jsonify({'code': 400, 'data': None, 'message': '路段名称不能为空'}), 400
    s = TrafficSection(name=data['name'], capacity=data.get('capacity', 1000), length=data.get('length', 1.0), max_speed=data.get('max_speed', 60), coordinates=data.get('coordinates', {}))
    db.session.add(s); db.session.commit()
    return jsonify({'code': 201, 'data': {'id': s.id}, 'message': '创建成功'}), 201


@sections_bp.route('/<int:section_id>', methods=['PUT'])
@jwt_required()
def update_section(section_id):
    s = db.session.get(TrafficSection, section_id)
    if not s: return jsonify({'code': 404, 'data': None, 'message': '路段不存在'}), 404
    data = request.get_json(silent=True) or {}
    for attr in ['name', 'capacity', 'length', 'max_speed', 'coordinates']:
        if attr in data: setattr(s, attr, data[attr])
    db.session.commit()
    return jsonify({'code': 200, 'data': None, 'message': '更新成功'})


@sections_bp.route('/<int:section_id>', methods=['DELETE'])
@jwt_required()
def delete_section(section_id):
    s = db.session.get(TrafficSection, section_id)
    if not s: return jsonify({'code': 404, 'data': None, 'message': '路段不存在'}), 404
    db.session.delete(s); db.session.commit()
    return jsonify({'code': 200, 'data': None, 'message': '删除成功'})
