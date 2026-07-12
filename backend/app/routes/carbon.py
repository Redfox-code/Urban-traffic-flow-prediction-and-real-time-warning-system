"""碳排放API — /api/v1/carbon/* — Agent-Lead"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.services.carbon_service import get_current_carbon, get_carbon_trend, get_section_carbon_top, estimate_co2

carbon_bp = Blueprint('carbon', __name__)


@carbon_bp.route('/current', methods=['GET'])
@jwt_required()
def current():
    """实时全城碳排放数据。"""
    result = get_current_carbon()
    return jsonify({'code': 200, 'data': result, 'message': 'ok'})


@carbon_bp.route('/trend', methods=['GET'])
@jwt_required()
def trend():
    """碳排放趋势数据。"""
    period = request.args.get('period', 'day')
    if period not in ('day', 'week', 'month'):
        period = 'day'
    result = get_carbon_trend(period)
    return jsonify({'code': 200, 'data': {'period': period, 'items': result}, 'message': 'ok'})


@carbon_bp.route('/sections/top', methods=['GET'])
@jwt_required()
def sections_top():
    """路段碳排放排行Top N。"""
    limit = request.args.get('limit', 10, type=int)
    result = get_section_carbon_top(limit)
    return jsonify({'code': 200, 'data': {'items': result}, 'message': 'ok'})


@carbon_bp.route('/estimate', methods=['POST'])
@jwt_required()
def estimate():
    """估算指定路段的CO2排放。"""
    data = request.get_json(silent=True) or {}
    speed = data.get('avg_speed_kmh', 30)
    count = data.get('vehicle_count', 100)
    result = estimate_co2(speed, count)
    return jsonify({'code': 200, 'data': result, 'message': 'ok'})


@carbon_bp.route('/comparison', methods=['GET'])
@jwt_required()
def comparison():
    """信号优化前后碳排放对比。"""
    from app.models.signal_optimization import SignalOptimization

    opts = SignalOptimization.query.filter_by(is_applied=True).order_by(
        SignalOptimization.applied_at.desc()
    ).limit(10).all()

    return jsonify({'code': 200, 'data': {
        'items': [{
            'intersection_name': o.intersection_name,
            'co2_reduction_kg': o.co2_reduction_kg or 0,
            'efficiency_gain_pct': o.efficiency_gain_pct,
            'applied_at': o.applied_at.isoformat() if o.applied_at else None
        } for o in opts]
    }, 'message': 'ok'})
