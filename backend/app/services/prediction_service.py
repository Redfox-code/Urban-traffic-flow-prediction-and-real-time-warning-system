"""预测服务 — 单例模式 — Agent-Algorithm"""
import os
import glob
import joblib
import numpy as np


class PredictionService:
    """预测模型单例（禁忌#1：不在请求中加载模型，启动时预加载）"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._models = {'KNN': None, 'RF': None}
            cls._instance._load_models()
        return cls._instance

    def _load_models(self):
        model_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'saved_models')
        for name in ['KNN', 'RF']:
            pattern = os.path.join(model_dir, f'*{name.lower()}*.pkl')
            files = sorted(glob.glob(pattern))
            if files:
                self._models[name] = joblib.load(files[-1])

    def predict(self, section_id, model_type='RF', horizon=15):
        model = self._models.get(model_type)
        if model is None:
            return {'error': f'模型 {model_type} 未加载，请先训练模型', 'code': 500}
        # TODO D8-D9: 接入真实模型预测
        predicted = 120.0 + np.random.normal(0, 5)
        return {
            'section_id': section_id, 'model': model_type, 'horizon': horizon,
            'predicted_flow': round(predicted, 1),
            'confidence_interval': {'lower': round(predicted - 10, 1), 'upper': round(predicted + 10, 1)},
            'predictions': [{'timestamp': f'2026-07-02T{10 + i}:00:00', 'predicted_flow': round(predicted + i * 2, 1)} for i in range(max(1, horizon // 5))],
            'generated_at': '2026-07-02T10:00:00',
        }
