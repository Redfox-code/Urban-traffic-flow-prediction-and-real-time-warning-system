"""模型评估 — 时间序列交叉验证 + 各指标计算 — Agent-Algorithm

支持的指标:
    MAE  — 平均绝对误差
    RMSE — 均方根误差
    MAPE — 平均绝对百分比误差 (%)
    R²   — 决定系数
"""

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import TimeSeriesSplit


def evaluate_models(X, y, models_dict, n_splits=5):
    """时间序列交叉验证，返回评估报告DataFrame

    Args:
        X: 特征矩阵 (DataFrame 或 ndarray)
        y: 目标变量 (Series 或 ndarray)
        models_dict: {'模型名': model_instance} — 需有 .train() 和 .predict() 方法
        n_splits: 时间序列交叉验证折数

    Returns:
        pd.DataFrame: 包含 model, fold, MAE, RMSE, MAPE, R2 的评估报告
    """
    tscv = TimeSeriesSplit(n_splits=n_splits)
    results = []

    # 统一转为 numpy 以便索引
    X_arr = X.values if hasattr(X, 'values') else X
    y_arr = y.values if hasattr(y, 'values') else y

    for name, model in models_dict.items():
        print(f"    CV评估 {name}…")
        for fold, (train_idx, test_idx) in enumerate(tscv.split(X_arr)):
            X_train, X_test = X_arr[train_idx], X_arr[test_idx]
            y_train, y_test = y_arr[train_idx], y_arr[test_idx]

            # 重新训练该折
            model.train(X_train, y_train)
            y_pred = model.predict(X_test)

            mae = mean_absolute_error(y_test, y_pred)
            rmse = np.sqrt(mean_squared_error(y_test, y_pred))
            # MAPE: 过滤 y_test 接近0的点（避免除零爆炸）
            mask = y_test > 1.0
            mape_val = np.nan
            if mask.sum() > 0:
                mape_val = np.mean(np.abs((y_test[mask] - y_pred[mask]) / y_test[mask])) * 100
            r2 = r2_score(y_test, y_pred)

            results.append({
                'model': name, 'fold': fold + 1,
                'MAE': round(mae, 2), 'RMSE': round(rmse, 2),
                'MAPE': round(mape_val, 2) if not np.isnan(mape_val) else None,
                'R2': round(r2, 4),
            })

    return pd.DataFrame(results)


def calculate_metrics(y_true, y_pred):
    """单次评估，返回指标字典"""
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    mask = y_true > 1.0
    mape = np.nan
    if mask.sum() > 0:
        mape = np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100
    r2 = r2_score(y_true, y_pred)
    return {
        'mae': round(mae, 2),
        'rmse': round(rmse, 2),
        'mape': round(mape, 2) if not np.isnan(mape) else None,
        'r2': round(r2, 3),
    }
