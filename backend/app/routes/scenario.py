"""场景仿真API — /api/v1/scenario/* — Agent-Lead"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.utils.decorators import role_required
from app.models.scenario_simulation import ScenarioSimulation
from app import db
from datetime import datetime


scenario_bp = Blueprint('scenario', __name__)


@scenario_bp.route('/scenarios', methods=['GET'])
@jwt_required()
def list_scenarios():
    """场景列表。"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)

    query = ScenarioSimulation.query.order_by(ScenarioSimulation.created_at.desc())
    total = query.count()
    scenarios = query.offset((page - 1) * page_size).limit(page_size).all()

    return jsonify({'code': 200, 'data': {
        'items': [{
            'id': s.id,
            'name': s.name,
            'description': s.description,
            'intervention_type': s.intervention_type,
            'status': s.status,
            'improvement_pct': s.improvement_pct,
            'created_at': s.created_at.isoformat() if s.created_at else None,
            'completed_at': s.completed_at.isoformat() if s.completed_at else None
        } for s in scenarios],
        'total': total, 'page': page, 'page_size': page_size
    }, 'message': 'ok'})


@scenario_bp.route('/create', methods=['POST'])
@jwt_required()
@role_required('analyst')
def create():
    """创建场景。"""
    data = request.get_json(silent=True) or {}
    user_id = int(get_jwt_identity())

    scenario = ScenarioSimulation(
        name=data.get('name', '未命名场景'),
        description=data.get('description', ''),
        intervention_type=data.get('intervention_type', 'limit_flow'),
        intervention_area_json=str(data.get('intervention_area', {})),
        params_json=str(data.get('params', {})),
        status='pending',
        created_by=user_id
    )
    db.session.add(scenario)
    db.session.commit()

    return jsonify({'code': 201, 'data': {'id': scenario.id, 'status': 'pending'}, 'message': '场景已创建'}), 201


@scenario_bp.route('/<int:scenario_id>', methods=['GET'])
@jwt_required()
def get_scenario(scenario_id):
    """场景详情。"""
    scenario = ScenarioSimulation.query.get(scenario_id)
    if not scenario:
        return jsonify({'code': 404, 'data': None, 'message': '场景不存在'}), 404

    return jsonify({'code': 200, 'data': {
        'id': scenario.id,
        'name': scenario.name,
        'description': scenario.description,
        'intervention_type': scenario.intervention_type,
        'intervention_area': scenario.intervention_area_json,
        'params': scenario.params_json,
        'baseline_result': scenario.baseline_result_json,
        'intervention_result': scenario.intervention_result_json,
        'improvement_pct': scenario.improvement_pct,
        'status': scenario.status,
        'created_at': scenario.created_at.isoformat() if scenario.created_at else None,
        'completed_at': scenario.completed_at.isoformat() if scenario.completed_at else None
    }, 'message': 'ok'})


@scenario_bp.route('/<int:scenario_id>/run', methods=['POST'])
@jwt_required()
@role_required('analyst')
def run_scenario(scenario_id):
    """运行场景仿真。"""
    scenario = ScenarioSimulation.query.get(scenario_id)
    if not scenario:
        return jsonify({'code': 404, 'data': None, 'message': '场景不存在'}), 404

    scenario.status = 'running'
    db.session.commit()

    try:
        import sys, os, json
        algo_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'algorithm'))
        if algo_dir not in sys.path:
            sys.path.insert(0, algo_dir)
        from scenario.whatif_engine import run_comparison

        params = json.loads(scenario.params_json) if scenario.params_json else {}
        result = run_comparison(
            intervention_type=scenario.intervention_type,
            params=params
        )

        scenario.baseline_result_json = str(result.get('baseline', {}))
        scenario.intervention_result_json = str(result.get('intervention', {}))
        scenario.improvement_pct = result.get('improvement_pct', 0)
        scenario.status = 'completed'
        scenario.completed_at = datetime.utcnow()
        db.session.commit()

        return jsonify({'code': 200, 'data': result, 'message': '仿真完成'})
    except Exception as e:
        scenario.status = 'failed'
        db.session.commit()
        return jsonify({'code': 500, 'data': None, 'message': f'仿真失败: {str(e)}'}), 500


@scenario_bp.route('/<int:scenario_id>/result', methods=['GET'])
@jwt_required()
def get_result(scenario_id):
    """获取仿真结果。"""
    scenario = ScenarioSimulation.query.get(scenario_id)
    if not scenario:
        return jsonify({'code': 404, 'data': None, 'message': '场景不存在'}), 404

    if scenario.status != 'completed':
        return jsonify({'code': 200, 'data': {'status': scenario.status}, 'message': '仿真未完成'})

    return jsonify({'code': 200, 'data': {
        'baseline': scenario.baseline_result_json,
        'intervention': scenario.intervention_result_json,
        'improvement_pct': scenario.improvement_pct,
        'status': scenario.status
    }, 'message': 'ok'})


@scenario_bp.route('/<int:scenario_id>', methods=['DELETE'])
@jwt_required()
@role_required('analyst')
def delete_scenario(scenario_id):
    """删除场景。"""
    scenario = ScenarioSimulation.query.get(scenario_id)
    if not scenario:
        return jsonify({'code': 404, 'data': None, 'message': '场景不存在'}), 404

    db.session.delete(scenario)
    db.session.commit()
    return jsonify({'code': 200, 'data': None, 'message': '已删除'})
