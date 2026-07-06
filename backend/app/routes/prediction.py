"""预测模块 — /api/v1/predict/* — Agent-Algorithm"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.services.prediction_service import PredictionService

prediction_bp = Blueprint('prediction', __name__)
service = PredictionService()


@prediction_bp.route('/forecast', methods=['GET'])
@jwt_required()
def forecast():
    section_id = request.args.get('section_id', type=int)
    horizon = request.args.get('horizon', 15, type=int)
    model = request.args.get('model', 'RF')
    if not section_id:
        return jsonify({'code': 400, 'data': None, 'message': '缺少section_id参数'}), 400
    if model not in ('KNN', 'RF'):
        return jsonify({'code': 400, 'data': None, 'message': f'不支持的模型：{model}'}), 400
    result = service.predict(section_id, model, horizon)
    if 'error' in result:
        return jsonify({'code': result['code'], 'data': None, 'message': result['error']}), result['code']
    return jsonify({'code': 200, 'data': result, 'message': 'ok'})


@prediction_bp.route('/accuracy', methods=['GET'])
@jwt_required()
def accuracy():
    section_id = request.args.get('section_id', type=int)
    result = service.get_accuracy(section_id)
    return jsonify({'code': 200, 'data': result, 'message': 'ok'})


@prediction_bp.route('/analysis', methods=['GET'])
@jwt_required()
def analysis():
    """预测分析报告 — 趋势/峰值/拥堵风险/模型可靠性/模型对比"""
    section_id = request.args.get('section_id', type=int)
    horizon = request.args.get('horizon', 15, type=int)
    if not section_id:
        return jsonify({'code': 400, 'data': None, 'message': '缺少section_id参数'}), 400
    result = service.analyze(section_id, horizon)
    if 'error' in result:
        return jsonify({'code': result['code'], 'data': None, 'message': result['error']}), result['code']
    return jsonify({'code': 200, 'data': result, 'message': 'ok'})
