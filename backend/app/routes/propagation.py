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
    from propagation.diffusion_model import propagate_congestion, build_adjacency_matrix, load_road_network, build_proximity_distances

    try:
        # 1. 加载路网和DB section
        road_network = load_road_network(os.path.join(
            os.path.dirname(__file__), '..', '..', '..', 'frontend', 'src', 'data', 'roadNetwork.json'
        ))
        from app.models.traffic_section import TrafficSection
        db_section = TrafficSection.query.get(int(section_id))
        if not db_section:
            return jsonify({'code': 404, 'data': None, 'message': '路段不存在'}), 404

        # 2. DB section名 → Amap segment ID（复用route_service的匹配逻辑）
        from app.services.route_service import _match_name, _match_coord
        amap_ids = _match_name(db_section.name)
        if not amap_ids:
            amap_ids = _match_coord(db_section)
        if not amap_ids:
            return jsonify({'code': 400, 'data': None,
                           'message': f'未找到 {db_section.name} 在路网中的对应路段'}), 400
        # 取最近的Amap segment
        amap_id = amap_ids[0]

        # 3. 构建邻接矩阵
        adj_matrix = build_adjacency_matrix(road_network, proximity_threshold_m=100, cross_threshold_m=50)
        distances = build_proximity_distances(road_network, adj_matrix)

        # 4. 获取速度数据（DB记录优先，无记录时用Amap speed模拟）
        from app.models.traffic_record import TrafficRecord
        from datetime import datetime, timedelta
        import random
        cutoff = datetime.utcnow() - timedelta(minutes=time_window)
        section_speeds = {}
        latest_records = TrafficRecord.query.filter(
            TrafficRecord.section_id.in_(list(adj_matrix.keys())),
            TrafficRecord.timestamp >= cutoff,
        ).order_by(TrafficRecord.timestamp.desc()).all()
        seen = set()
        for r in latest_records:
            if r.section_id not in seen and r.avg_speed:
                section_speeds[r.section_id] = float(r.avg_speed)
                seen.add(r.section_id)
        # 无DB记录时用Amap speed字段模拟，给每个路段不同的速度
        random.seed(section_id)  # 固定种子保持一致性
        for seg in road_network:
            sid = seg['id']
            if sid not in section_speeds:
                base = float(seg.get('speed', 40) or 40)
                # 随机抖动±20%模拟真实交通波动，时间窗口越小波动越大
                jitter = 1.0 + random.uniform(-0.2, 0.2) * (30.0 / max(time_window, 1))
                section_speeds[sid] = round(base * jitter, 1)

        # 5. 执行传播分析
        # 路段实际长度（从坐标计算）
        seg_lengths = {}
        for seg in road_network:
            path = seg.get('path', [])
            if len(path) >= 2:
                total = sum(
                    ((path[i][0]-path[i-1][0])**2 + (path[i][1]-path[i-1][1])**2)**0.5 * 111.0
                    for i in range(1, len(path))
                )
                seg_lengths[seg['id']] = round(total, 3)
            else:
                seg_lengths[seg['id']] = 0.5

        result = propagate_congestion(
            source_section_id=amap_id,
            adjacency_matrix=adj_matrix,
            section_speeds=section_speeds,
            max_depth=max_depth,
            prob_threshold=min_probability,
            distances=distances,
            seg_lengths=seg_lengths,
        )

        # 5. 构建双向路段名映射（Amap ID ↔ DB section name）
        seg_to_dbname = {}
        for s in TrafficSection.query.all():
            mids = _match_name(s.name) or _match_coord(s)
            for mid in mids:
                seg_to_dbname[mid] = s.name  # 总是覆盖，最近匹配的优先
        # Amap name fallback
        seg_amap_name = {seg['id']: seg['name'] for seg in road_network}

        # 6. 格式化返回 — 根节点强制用DB路段名，子节点优先DB名兜底Amap名
        tree_dict = result.tree.to_dict() if result.tree else None
        if tree_dict:
            tree_dict['name'] = db_section.name
        def _add_child_names(node):
            if node:
                for c in node.get('children', []):
                    sid = int(c.get('section_id', 0))
                    c['name'] = seg_to_dbname.get(sid) or seg_amap_name.get(sid, f"路段{sid}")
                    _add_child_names(c)
        _add_child_names(tree_dict)

        # flat_list也加上name（优先DB名）
        flat_list = result.to_flat_list()
        for item in flat_list:
            fid = int(item.get('from', 0)) if item.get('from') else 0
            tid = int(item.get('to', 0))
            item['from_name'] = seg_to_dbname.get(fid) or seg_amap_name.get(fid, f"路段{fid}") if fid else None
            item['to_name'] = seg_to_dbname.get(tid) or seg_amap_name.get(tid, f"路段{tid}")

        return jsonify({'code': 200, 'data': {
            'source_section_id': result.root_section_id,
            'source_name': db_section.name,  # 用DB路段名，确保和下拉框一致
            'propagation_tree': tree_dict,
            'flat_list': flat_list,
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
