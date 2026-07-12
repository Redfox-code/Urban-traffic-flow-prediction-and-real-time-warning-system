"""预测服务 — 单例模式 — 加载真实模型进行预测

禁忌#1 遵守: 不在请求中加载模型文件，应用启动时预加载到内存
"""

import os
import glob
import joblib
import numpy as np
import pandas as pd
from datetime import datetime, timedelta


class PredictionService:
    """预测模型单例 — 启动时预加载KNN+RF"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._models = {'KNN': None, 'RF': None}
            cls._instance._feature_cols = [
                'section_id', 'hour', 'day_of_week', 'is_weekend',
                'avg_speed_lag_1', 'occupancy_lag_1',
                'vehicle_count_lag_1'
            ]
            cls._instance._load_models()
        return cls._instance

    def _get_model_dir(self):
        """定位 saved_models 目录"""
        return os.path.join(os.path.dirname(__file__), '..', '..', 'saved_models')

    def _load_models(self):
        """启动时预加载模型文件（单例模式）

        优先加载 sklearn 原生模型文件（*_sklearn_latest.pkl），
        避免 pickle 反序列化对 prediction 包路径的依赖。
        """
        model_dir = self._get_model_dir()
        for name in ['KNN', 'RF']:
            # 优先加载 sklearn 原生模型
            sklearn_latest = os.path.join(model_dir, f'{name.lower()}_sklearn_latest.pkl')
            if os.path.exists(sklearn_latest):
                self._models[name] = joblib.load(sklearn_latest)
                print(f"[PredictionService] 已加载 {name} sklearn 模型: {sklearn_latest}")
            else:
                pattern = os.path.join(model_dir, f'*{name.lower()}*.pkl')
                files = sorted(glob.glob(pattern))
                if files:
                    self._models[name] = joblib.load(files[-1])
                    print(f"[PredictionService] 已加载 {name} 模型: {files[-1]}")

        loaded_any = any(v is not None for v in self._models.values())
        if not loaded_any:
            print("[PredictionService] 警告: 未找到任何已训练模型，将回退到模拟数据")

    def is_model_loaded(self, model_type='RF'):
        """检查模型是否已加载"""
        return self._models.get(model_type) is not None

    def _get_latest_observation(self, section_id):
        """从数据库获取路段最近的观测数据以构建特征

        Returns:
            dict: 最新观测值，或 None
        """
        try:
            from app import create_app, db
            from app.models import TrafficRecord
            from sqlalchemy import text

            records = db.session.query(
                TrafficRecord.vehicle_count,
                TrafficRecord.avg_speed,
                TrafficRecord.occupancy,
                TrafficRecord.timestamp
            ).filter(
                TrafficRecord.section_id == section_id
            ).order_by(
                TrafficRecord.timestamp.desc()
            ).limit(3).all()

            if records and len(records) >= 3:
                return {
                    'timestamp': records[0].timestamp,
                    'vehicle_count': float(records[0].vehicle_count),
                    'avg_speed': float(records[0].avg_speed),
                    'occupancy': float(records[0].occupancy),
                    'lag_1': float(records[0].vehicle_count),
                    'lag_2': float(records[1].vehicle_count) if len(records) > 1 else float(records[0].vehicle_count),
                    'lag_3': float(records[2].vehicle_count) if len(records) > 2 else float(records[1].vehicle_count) if len(records) > 1 else float(records[0].vehicle_count),
                }
            elif records:
                val = float(records[0].vehicle_count)
                return {
                    'timestamp': records[0].timestamp,
                    'vehicle_count': val,
                    'avg_speed': float(records[0].avg_speed),
                    'occupancy': float(records[0].occupancy),
                    'lag_1': val,
                    'lag_2': val,
                    'lag_3': val,
                }
            return None

        except Exception as e:
            print(f"[PredictionService] 数据库查询失败: {e}")
            return None

    def _get_section_name(self, section_id):
        """获取路段名称"""
        try:
            from app import create_app, db
            from app.models import TrafficSection
            section = db.session.query(TrafficSection).filter_by(id=section_id).first()
            return section.name if section else f'路段{section_id}'
        except Exception:
            return f'路段{section_id}'

    def _build_feature_vector(self, section_id, timestamp):
        """为指定路段和时间点构建特征向量

        Returns:
            (features_DataFrame, has_real_data): 特征矩阵 + 是否有真实DB数据
        """
        obs = self._get_latest_observation(section_id)
        now = timestamp or datetime.utcnow()
        has_real_data = obs is not None  # True=高德真实数据, False=默认值

        # 默认值（当数据库不可用时）
        lag_1 = 50
        lag_2 = 45
        lag_3 = 40
        avg_speed = 45.0
        occupancy = 25.0

        if obs:
            lag_1 = obs.get('lag_1', 50)
            lag_2 = obs.get('lag_2', 45)
            lag_3 = obs.get('lag_3', 40)
            avg_speed = obs.get('avg_speed', 45.0)
            occupancy = obs.get('occupancy', 25.0)

        features = {
            'section_id': section_id,
            'hour': now.hour,
            'day_of_week': now.weekday(),
            'is_weekend': 1 if now.weekday() >= 5 else 0,
            'avg_speed_lag_1': avg_speed,
            'occupancy_lag_1': occupancy,
            'vehicle_count_lag_1': lag_1,
            'vehicle_count_lag_2': lag_2,
            'vehicle_count_lag_3': lag_3,
        }

        return pd.DataFrame([[features[col] for col in self._feature_cols]], columns=self._feature_cols), has_real_data

    def predict(self, section_id, model_type='RF', horizon=15):
        """执行预测

        Args:
            section_id: 路段ID
            model_type: 'KNN' 或 'RF'
            horizon: 预测窗口（分钟），可选 5/15/30

        Returns:
            dict: 预测结果（符合API契约格式）
        """
        model = self._models.get(model_type)
        now = datetime.utcnow()

        # 如果模型未加载，回退到模拟数据
        if model is None:
            return self._fallback_predict(section_id, model_type, horizon, now)

        try:
            section_name = self._get_section_name(section_id)

            # 构建特征并预测 (has_real_data=True表示使用了高德真实数据)
            features, has_real_data = self._build_feature_vector(section_id, now)
            predicted = float(model.predict(features)[0])
            predicted = max(0, predicted)  # 流量不能为负

            # 根据预测窗口生成时序预测点
            predictions = []
            current_feat = features.copy()
            n_points = max(1, horizon // 5)

            for i in range(n_points):
                t = now + timedelta(minutes=i * 5)
                pred_val = float(model.predict(current_feat)[0])
                pred_val = max(0, pred_val)
                predictions.append({
                    'timestamp': t.isoformat(),
                    'predicted_flow': round(pred_val, 1),
                })

                # 多步预测：用预测值更新滞后特征
                if i < n_points - 1:
                    new_feat = current_feat.copy()
                    new_feat.iloc[0, 6] = pred_val  # vehicle_count_lag_1 (window=1)
                    current_feat = new_feat

            return {
                'section_id': section_id,
                'section_name': section_name,
                'model': model_type,
                'horizon': horizon,
                'using_trained_model': True,
                'data_source': 'amap' if has_real_data else 'default',
                'predicted_flow': round(predicted, 1),
                'confidence_interval': {
                    'lower': round(predicted * 0.85, 1),
                    'upper': round(predicted * 1.15, 1),
                },
                'predictions': predictions,
                'generated_at': now.isoformat(),
            }

        except Exception as e:
            print(f"[PredictionService] 预测失败: {e}")
            return self._fallback_predict(section_id, model_type, horizon, now)

    def _fallback_predict(self, section_id, model_type, horizon, now):
        """模型未加载时的回退方案：基于历史均值估算"""
        print(f"[PredictionService] 回退模式: section_id={section_id}, model={model_type}")
        np.random.seed(section_id * 42)

        # 尝试从数据库取历史均值
        avg_flow = 80
        try:
            from app import create_app, db
            from app.models import TrafficRecord
            from sqlalchemy import func
            result = db.session.query(func.avg(TrafficRecord.vehicle_count)).filter(
                TrafficRecord.section_id == section_id
            ).scalar()
            if result:
                avg_flow = float(result)
        except Exception:
            pass

        section_name = self._get_section_name(section_id)

        n_points = max(1, horizon // 5)
        predictions = []
        for i in range(n_points):
            t = now + timedelta(minutes=i * 5)
            pred_val = avg_flow * (1 + np.random.normal(0, 0.08))
            predictions.append({
                'timestamp': t.isoformat(),
                'predicted_flow': round(max(0, pred_val), 1),
            })

        return {
            'section_id': section_id,
            'section_name': section_name,
            'model': model_type,
            'horizon': horizon,
            'using_trained_model': False,
            'data_source': 'fallback',
            'predicted_flow': round(avg_flow, 1),
            'confidence_interval': {
                'lower': round(avg_flow * 0.85, 1),
                'upper': round(avg_flow * 1.15, 1),
            },
            'predictions': predictions,
            'generated_at': now.isoformat(),
        }

    def analyze(self, section_id, horizon=15):
        """生成预测分析报告

        Args:
            section_id: 路段ID
            horizon: 预测窗口（分钟）

        Returns:
            dict: 分析报告（符合API契约格式）
        """
        now = datetime.utcnow()
        section_name = self._get_section_name(section_id)

        # 1. 同时获取RF和KNN预测
        rf_result = self.predict(section_id, 'RF', horizon)
        knn_result = self.predict(section_id, 'KNN', horizon)

        rf_predictions = rf_result.get('predictions', [])
        knn_predictions = knn_result.get('predictions', [])

        # 2. 趋势分析（基于RF预测序列）
        trend = self._analyze_trend(rf_predictions)

        # 3. 峰值分析
        peak = self._analyze_peak(rf_predictions)

        # 4. 拥堵风险评估
        congestion_risk = self._analyze_congestion(rf_predictions, section_name, horizon)

        # 5. 模型可靠性（从metrics.json读取）
        model_reliability = self._get_model_reliability()

        # 6. 模型对比（RF vs KNN）
        comparison = self._compare_models(rf_result, knn_result)

        return {
            'section_id': section_id,
            'section_name': section_name,
            'horizon': horizon,
            'generated_at': now.isoformat(),
            'trend': trend,
            'peak': peak,
            'congestion_risk': congestion_risk,
            'model_reliability': model_reliability,
            'comparison': comparison,
        }

    def _analyze_trend(self, predictions):
        """分析预测序列趋势"""
        if not predictions or len(predictions) < 2:
            return {'direction': '平稳', 'change_percent': 0, 'start_flow': 0, 'end_flow': 0}

        start_flow = predictions[0].get('predicted_flow', 0)
        end_flow = predictions[-1].get('predicted_flow', 0)

        if start_flow == 0:
            change_percent = 0
        else:
            change_percent = round((end_flow - start_flow) / start_flow * 100, 1)

        if change_percent > 5:
            direction = '上升'
        elif change_percent < -5:
            direction = '下降'
        else:
            direction = '平稳'

        return {
            'direction': direction,
            'change_percent': change_percent,
            'start_flow': start_flow,
            'end_flow': end_flow,
        }

    def _analyze_peak(self, predictions):
        """分析预测序列中的峰值"""
        if not predictions:
            return {'max_flow': 0, 'max_time': '', 'min_flow': 0, 'min_time': ''}

        max_point = max(predictions, key=lambda p: p.get('predicted_flow', 0))
        min_point = min(predictions, key=lambda p: p.get('predicted_flow', 0))

        return {
            'max_flow': max_point.get('predicted_flow', 0),
            'max_time': max_point.get('timestamp', ''),
            'min_flow': min_point.get('predicted_flow', 0),
            'min_time': min_point.get('timestamp', ''),
        }

    def _analyze_congestion(self, predictions, section_name, horizon):
        """评估拥堵风险

        假设路段容量 = 60 veh/h，计算超过85%容量（51 veh/h）的概率。
        """
        capacity = 60  # 假设路段容量 60 veh/h
        threshold_warning = capacity * 0.85  # 51 veh/h
        threshold_critical = capacity * 0.95  # 57 veh/h

        if not predictions:
            return {
                'level': '低', 'probability': 0, 'trigger_sections': [],
                'description': '无预测数据，无法评估拥堵风险',
            }

        # 统计超过阈值的数据点比例
        n_points = len(predictions)
        n_warning = sum(1 for p in predictions if p.get('predicted_flow', 0) >= threshold_warning)
        n_critical = sum(1 for p in predictions if p.get('predicted_flow', 0) >= threshold_critical)

        probability = round(n_warning / n_points, 2) if n_points > 0 else 0

        # 确定风险等级
        max_flow = max(p.get('predicted_flow', 0) for p in predictions)
        if n_critical > 0:
            level = '严重'
        elif probability >= 0.5:
            level = '高'
        elif probability >= 0.2:
            level = '中'
        else:
            level = '低'

        level_text = {'低': 'Low', '中': 'Medium', '高': 'High', '严重': 'Critical'}
        description = (
            f"预测窗口内流量峰值{max_flow:.1f}veh/h，"
            f"超过路段容量{int(capacity)}veh/h的85%阈值概率{probability:.0%}"
        )
        if n_critical > 0:
            description += f"，其中{n_critical}个时间点超过95%严重阈值"

        return {
            'level': level,
            'probability': probability,
            'trigger_sections': [section_name],
            'description': description,
        }

    def _get_model_reliability(self):
        """获取模型可靠性指标"""
        import json
        model_dir = self._get_model_dir()
        metrics_path = os.path.join(model_dir, 'metrics.json')

        if os.path.exists(metrics_path):
            with open(metrics_path, 'r') as f:
                metrics = json.load(f)

            rf_mae = metrics.get('RF_mae', 0)
            rf_r2 = metrics.get('RF_r2', 0)
            knn_mae = metrics.get('KNN_mae', 0)
            knn_r2 = metrics.get('KNN_r2', 0)
            best_model = metrics.get('best_model', 'RF')

            # 根据R²生成推荐建议
            best_r2 = max(rf_r2, knn_r2)
            training_date = metrics.get('training_date', 'unknown')
            total_records = metrics.get('total_records', 0)

            if best_r2 > 0.5:
                recommendation = (f"模型可解释性较好（{best_model} R²={best_r2:.2f}，MAE={min(rf_mae, knn_mae):.1f}veh/h）。"
                                  f"训练数据{total_records}条({training_date[:10]})。")
            elif best_r2 > 0:
                recommendation = (f"模型有一定预测能力（{best_model} R²={best_r2:.2f}，MAE={min(rf_mae, knn_mae):.1f}veh/h）。"
                                  f"建议结合实时路况综合判断。训练数据{total_records}条。")
            else:
                recommendation = (f"[注意] 当前模型R²为负值（{best_model} R²={best_r2:.2f}），预测精度不如简单均值。"
                                  f"原因：训练数据仅{total_records}条高德实时数据，时间跨度不足，滞后特征价值有限。"
                                  f"请以实时路况数据为准。积累更多时段数据后可改善。")

            return {
                'best_model': best_model,
                'rf_mae': rf_mae,
                'rf_r2': rf_r2,
                'knn_mae': knn_mae,
                'knn_r2': knn_r2,
                'training_date': training_date,
                'total_records': total_records,
                'recommendation': recommendation,
            }

        # 回退默认值
        return {
            'best_model': 'RF',
            'rf_mae': 0, 'rf_r2': 0,
            'knn_mae': 0, 'knn_r2': 0,
            'recommendation': '暂无模型评估数据',
        }

    def _compare_models(self, rf_result, knn_result):
        """对比RF和KNN预测结果"""
        rf_flow = rf_result.get('predicted_flow', 0)
        knn_flow = knn_result.get('predicted_flow', 0)
        difference = round(abs(rf_flow - knn_flow), 1)

        import json
        model_dir = self._get_model_dir()
        metrics_path = os.path.join(model_dir, 'metrics.json')
        rf_mae = None
        knn_mae = None
        if os.path.exists(metrics_path):
            with open(metrics_path, 'r') as f:
                metrics = json.load(f)
            rf_mae = metrics.get('RF_mae')
            knn_mae = metrics.get('KNN_mae')

        if rf_mae is not None and knn_mae is not None:
            max_mae = max(rf_mae, knn_mae)
            if difference <= max_mae:
                note = f"RF预测值略{'高' if rf_flow > knn_flow else '低'}于KNN，差异在模型MAE范围内(±{max_mae:.1f}veh/h)"
            else:
                note = f"RF与KNN预测差异{difference:.1f}veh/h，超出模型MAE范围(±{max_mae:.1f}veh/h)，建议检查输入数据"
        else:
            note = f"RF({rf_flow:.0f})与KNN({knn_flow:.0f})预测差异{difference:.1f}veh/h（无历史metrics数据对比）"

        return {
            'rf_predicted': rf_flow,
            'knn_predicted': knn_flow,
            'difference': difference,
            'note': note,
            'rf_mae': rf_mae,
            'knn_mae': knn_mae,
        }

    def get_accuracy(self, section_id=None):
        """获取模型评估精度指标"""
        model_dir = self._get_model_dir()
        metrics_path = os.path.join(model_dir, 'metrics.json')

        if os.path.exists(metrics_path):
            import json
            with open(metrics_path, 'r') as f:
                metrics = json.load(f)
            return {
                'section_id': section_id,
                'best_model': metrics.get('best_model', 'RF'),
                'models': {
                    'KNN': {
                        'mae': metrics.get('KNN_mae', 0),
                        'rmse': metrics.get('KNN_rmse', 0),
                        'mape': metrics.get('KNN_mape', 0),
                        'r2': metrics.get('KNN_r2', 0),
                    },
                    'RF': {
                        'mae': metrics.get('RF_mae', 0),
                        'rmse': metrics.get('RF_rmse', 0),
                        'mape': metrics.get('RF_mape', 0),
                        'r2': metrics.get('RF_r2', 0),
                    },
                },
                'updated_at': metrics.get('training_date', ''),
            }

        # 回退默认值
        return {
            'section_id': section_id,
            'best_model': 'RF',
            'models': {
                'KNN': {'mae': 0, 'rmse': 0, 'mape': 0, 'r2': 0},
                'RF': {'mae': 0, 'rmse': 0, 'mape': 0, 'r2': 0},
            },
            'updated_at': '',
        }
