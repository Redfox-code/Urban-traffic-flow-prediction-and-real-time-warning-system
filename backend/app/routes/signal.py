"""信号优化API — /api/v1/signal/* — Agent-Lead"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.utils.decorators import role_required
from app.services.signal_service import calculate_webster, get_intersection_list
from app.models.signal_optimization import SignalOptimization
from app import db
from datetime import datetime

signal_bp = Blueprint('signal', __name__)


@signal_bp.route('/intersections', methods=['GET'])
@jwt_required()
def intersections():
    """获取路口列表（按优化潜力降序）。"""
    result = get_intersection_list()
    return jsonify({'code': 200, 'data': {'intersections': result}, 'message': 'ok'})


@signal_bp.route('/calculate', methods=['POST'])
@jwt_required()
@role_required('admin', 'analyst')
def calculate():
    """计算单个路口的Webster最优配时。"""
    data = request.get_json(silent=True) or {}
    intersection_id = data.get('intersection_id', 'unknown')
    result = calculate_webster(data)

    if 'error' in result:
        return jsonify({'code': 400, 'data': None, 'message': result['error']}), 400

    # 保存优化记录
    optimization = SignalOptimization(
        intersection_id=str(intersection_id),
        intersection_name=data.get('intersection_name', ''),
        current_cycle=data.get('current_cycle', 120),
        suggested_cycle=result['optimal_cycle'],
        green_split_json=str(result['green_splits']),
        efficiency_gain_pct=result.get('efficiency_gain_pct', 0),
        delay_reduction_sec=result.get('delay_reduction_sec', 0)
    )
    db.session.add(optimization)
    db.session.commit()

    return jsonify({'code': 200, 'data': {
        'optimization_id': optimization.id,
        **result
    }, 'message': 'Webster配时计算完成'})


@signal_bp.route('/apply', methods=['POST'])
@jwt_required()
@role_required('admin')
def apply():
    """应用建议配时方案。"""
    data = request.get_json(silent=True) or {}
    opt_id = data.get('optimization_id')

    opt = SignalOptimization.query.get(opt_id)
    if not opt:
        return jsonify({'code': 404, 'data': None, 'message': '优化记录不存在'}), 404

    opt.is_applied = True
    opt.applied_at = datetime.utcnow()
    db.session.commit()

    return jsonify({'code': 200, 'data': {
        'optimization_id': opt.id,
        'applied_at': opt.applied_at.isoformat()
    }, 'message': '配时方案已应用'})


@signal_bp.route('/history', methods=['GET'])
@jwt_required()
def history():
    """优化历史记录。"""
    records = SignalOptimization.query.order_by(
        SignalOptimization.created_at.desc()
    ).limit(50).all()

    return jsonify({'code': 200, 'data': {
        'items': [{
            'id': r.id,
            'intersection_name': r.intersection_name,
            'current_cycle': r.current_cycle,
            'suggested_cycle': r.suggested_cycle,
            'efficiency_gain_pct': r.efficiency_gain_pct,
            'delay_reduction_sec': r.delay_reduction_sec,
            'is_applied': r.is_applied,
            'created_at': r.created_at.isoformat() if r.created_at else None
        } for r in records]
    }, 'message': 'ok'})


@signal_bp.route('/stats', methods=['GET'])
@jwt_required()
def stats():
    """信号优化效果统计。"""
    total = SignalOptimization.query.count()
    applied = SignalOptimization.query.filter_by(is_applied=True).count()
    avg_gain = db.session.query(
        db.func.avg(SignalOptimization.efficiency_gain_pct)
    ).scalar() or 0

    return jsonify({'code': 200, 'data': {
        'total_optimizations': total,
        'applied_count': applied,
        'average_efficiency_gain_pct': round(avg_gain, 1)
    }, 'message': 'ok'})
