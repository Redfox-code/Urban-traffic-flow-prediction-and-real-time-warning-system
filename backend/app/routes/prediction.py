"""预测模块 — /api/v1/predict/* — Agent-Algorithm"""
from flask import Blueprint, request, jsonify
from app.services.prediction_service import PredictionService

prediction_bp = Blueprint('prediction', __name__)
service = PredictionService()


@prediction_bp.route('/forecast', methods=['GET'])
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
def accuracy():
    section_id = request.args.get('section_id', type=int)
    # TODO D9: 接入真实评估数据
    return jsonify({'code': 200, 'data': {
        'section_id': section_id, 'best_model': 'RF',
        'models': {'KNN': {'mae': 12.3, 'rmse': 18.5, 'mape': 15.2, 'r2': 0.78},
                   'RF': {'mae': 8.7, 'rmse': 13.2, 'mape': 10.8, 'r2': 0.85}},
    }, 'message': 'ok'})
