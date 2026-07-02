"""模型评估 — Agent-Algorithm"""
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import TimeSeriesSplit


def evaluate_models(X, y, models_dict, n_splits=5):
    """时间序列交叉验证，返回评估报告DataFrame"""
    tscv = TimeSeriesSplit(n_splits=n_splits)
    results = []
    for name, model in models_dict.items():
        for fold, (train_idx, test_idx) in enumerate(tscv.split(X)):
            X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
            y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
            model.train(X_train.values, y_train.values)
            y_pred = model.predict(X_test.values)
            results.append({
                'model': name, 'fold': fold + 1,
                'MAE': mean_absolute_error(y_test, y_pred),
                'RMSE': np.sqrt(mean_squared_error(y_test, y_pred)),
                'MAPE': np.mean(np.abs((y_test - y_pred) / (y_test + 1e-6))) * 100,
                'R2': r2_score(y_test, y_pred),
            })
    return pd.DataFrame(results)
