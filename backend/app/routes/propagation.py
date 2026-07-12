"""拥堵传播API — /api/v1/propagation/* — Agent-Lead"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.utils.decorators import role_required
from app.models.congestion_propagation import CongestionPropagation
from app.models.traffic_section import TrafficSection
from app import db
from datetime import datetime


propagation_bp = Blueprint('propagation', __name__)


@propagation_bp.route('/analyze', methods=['POST'])
@jwt_required()
@role_required('admin', 'analyst')
def analyze():
    """执行拥堵传播分析。"""
    data = request.get_json(silent=True) or {}
    section_id = data.get('section_id')
    max_depth = data.get('max_depth', 3)
    min_probability = data.get('min_probability', 0.3)
    time_window = data.get('time_window', 30)  # 分钟

    if not section_id:
        return jsonify({'code': 400, 'data': None, 'message': '请指定起始路段ID'}), 400

    # 调用算法模块
    import sys, os, json
    algo_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'algorithm'))
    if algo_dir not in sys.path:
        sys.path.insert(0, algo_dir)
    from propagation.diffusion_model import propagate_congestion, build_adjacency_matrix, load_road_network

    try:
        # 1. 从roadNetwork.json构建邻接矩阵
        road_network = load_road_network()
        adj_matrix = build_adjacency_matrix(road_network)

        # 2. 从数据库获取各路段最新速度
        from app.models.traffic_record import TrafficRecord
        from sqlalchemy import func
        section_speeds = {}
        latest_records = TrafficRecord.query.filter(
            TrafficRecord.section_id.in_(list(adj_matrix.keys()))
        ).order_by(TrafficRecord.timestamp.desc()).limit(500).all()

        seen = set()
        for r in latest_records:
            if r.section_id not in seen and r.avg_speed:
                section_speeds[r.section_id] = float(r.avg_speed)
                seen.add(r.section_id)

        # 3. 对没有数据的路段使用默认速度
        for sid in adj_matrix:
            if sid not in section_speeds:
                section_speeds[sid] = 40.0

        # 4. 执行传播分析
        sid = int(section_id)
        if sid not in adj_matrix:
            return jsonify({'code': 400, 'data': None,
                           'message': f'路段{sid}不在路网中，可用范围: {min(adj_matrix.keys())}-{max(adj_matrix.keys())}'}), 400

        result = propagate_congestion(
            source_section_id=sid,
            adjacency_matrix=adj_matrix,
            section_speeds=section_speeds,
            max_depth=max_depth,
            prob_threshold=min_probability,
        )

        # 5. 格式化返回
        return jsonify({'code': 200, 'data': {
            'source_section_id': result.root_section_id,
            'propagation_tree': result.tree.to_dict() if result.tree else None,
            'flat_list': result.to_flat_list(),
            'total_nodes': result.total_nodes,
            'max_depth': result.max_depth,
        }, 'message': '传播分析完成'})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'code': 500, 'data': None, 'message': f'传播分析失败: {str(e)}'}), 500


@propagation_bp.route('/active', methods=['GET'])
@jwt_required()
def active():
    """获取当前活跃的传播链。"""
    propagations = CongestionPropagation.query.filter_by(is_active=True).order_by(
        CongestionPropagation.created_at.desc()
    ).limit(50).all()

    chains = {}
    for p in propagations:
        key = p.from_section_id
        if key not in chains:
            from_sec = TrafficSection.query.get(p.from_section_id)
            chains[key] = {
                'source_section_id': p.from_section_id,
                'source_name': from_sec.name if from_sec else f'路段{p.from_section_id}',
                'targets': []
            }
        to_sec = TrafficSection.query.get(p.to_section_id)
        chains[key]['targets'].append({
            'section_id': p.to_section_id,
            'section_name': to_sec.name if to_sec else f'路段{p.to_section_id}',
            'probability': p.probability,
            'delay_minutes': round(p.propagation_delay / 60, 1) if p.propagation_delay else 0,
            'depth': p.depth,
            'confidence': p.confidence
        })

    return jsonify({'code': 200, 'data': {'chains': list(chains.values())}, 'message': 'ok'})


@propagation_bp.route('/history', methods=['GET'])
@jwt_required()
def history():
    """历史传播事件列表。"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)

    query = CongestionPropagation.query.order_by(CongestionPropagation.created_at.desc())
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    return jsonify({'code': 200, 'data': {
        'items': [{
            'id': p.id,
            'from_section_id': p.from_section_id,
            'to_section_id': p.to_section_id,
            'probability': p.probability,
            'propagation_delay': p.propagation_delay,
            'depth': p.depth,
            'confidence': p.confidence,
            'is_active': p.is_active,
            'created_at': p.created_at.isoformat() if p.created_at else None
        } for p in items],
        'total': total, 'page': page, 'page_size': page_size
    }, 'message': 'ok'})


@propagation_bp.route('/history/<int:event_id>', methods=['GET'])
@jwt_required()
def history_detail(event_id):
    """传播事件详情（含传播树）。"""
    event = CongestionPropagation.query.get(event_id)
    if not event:
        return jsonify({'code': 404, 'data': None, 'message': '传播事件不存在'}), 404

    # 获取该事件的完整传播链
    chain = CongestionPropagation.query.filter_by(
        from_section_id=event.from_section_id,
    ).filter(
        CongestionPropagation.created_at >= event.created_at
    ).order_by(CongestionPropagation.depth.asc()).all()

    from_sec = TrafficSection.query.get(event.from_section_id)
    return jsonify({'code': 200, 'data': {
        'event': {
            'id': event.id,
            'source': {'section_id': event.from_section_id,
                       'name': from_sec.name if from_sec else f'路段{event.from_section_id}'},
            'created_at': event.created_at.isoformat() if event.created_at else None
        },
        'chain': [{
            'from_section_id': c.from_section_id,
            'to_section_id': c.to_section_id,
            'probability': c.probability,
            'delay_minutes': round(c.propagation_delay / 60, 1) if c.propagation_delay else 0,
            'depth': c.depth,
            'confidence': c.confidence
        } for c in chain]
    }, 'message': 'ok'})
