"""模型训练管道 — 从DB读取数据 → 特征工程 → 训练KNN+RF → 保存pickle

用法:
    cd algorithm && python -m prediction.train_model
    cd algorithm && python -m prediction.train_model --horizon 5
"""

import sys
import os
import argparse
import joblib
import numpy as np
import pandas as pd
from datetime import datetime

# 确保能导入 backend 和 algorithm
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from prediction.preprocessing import (
    load_traffic_data, build_features, train_test_split_time
)
from prediction.knn_predictor import KNNPredictor
from prediction.rf_predictor import RFPredictor
from prediction.evaluator import evaluate_models


def train_models(save_dir=None, days=None, horizon_minutes=5):
    """主训练管道

    Args:
        save_dir: 模型保存目录（默认 backend/saved_models）
        days: 仅使用最近N天数据（默认全部）
        horizon_minutes: 预测粒度（分钟），默认5

    Returns:
        dict: 训练结果指标
    """
    if save_dir is None:
        save_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'backend', 'saved_models')
    os.makedirs(save_dir, exist_ok=True)

    print("=" * 60)
    print(f"  流量预测模型训练管道 — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  预测粒度: {horizon_minutes}min | 模型保存: {save_dir}")
    print("=" * 60)

    # Step 1: 加载数据
    print("\n[1/5] 加载数据…")
    df = load_traffic_data(days=days)
    print(f"  共 {len(df)} 条记录, {df['section_id'].nunique()} 个路段")

    # Step 2: 特征工程
    print(f"\n[2/5] 特征工程 (滞后窗口=3, 即{horizon_minutes*3}min)…")
    X, y, df_feat = build_features(df, window=3)
    print(f"  特征矩阵: {X.shape}")

    # Step 3: 按时间划分训练/测试集
    print(f"\n[3/5] 数据划分 (8:2 时间顺序)…")
    X_train, X_test, y_train, y_test = train_test_split_time(X, y, test_ratio=0.2)
    print(f"  训练集: {len(X_train)} | 测试集: {len(X_test)}")

    # Step 4: 训练KNN和RF
    print(f"\n[4/5] 训练模型…")

    # KNN
    print("  训练 KNN…")
    knn = KNNPredictor()
    knn.train(X_train.values, y_train)
    print(f"    KNN 最优参数: {knn.get_params()}")
    knn_path = os.path.join(save_dir, f'knn_model_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pkl')
    knn.save(knn_path)
    print(f"    KNN 已保存: {knn_path}")
    # 同时保存一份 latest 副本
    knn_latest = os.path.join(save_dir, 'knn_latest.pkl')
    joblib.dump(knn, knn_latest)
    # 也保存底层 sklearn 模型（避免pickle依赖prediction包路径）
    joblib.dump(knn.model, os.path.join(save_dir, 'knn_sklearn_latest.pkl'))
    print(f"    KNN latest: {knn_latest}")

    # RF
    print("  训练 随机森林…")
    rf = RFPredictor()
    rf.train(X_train, y_train)
    print(f"    RF 最优参数: {rf.get_params()}")
    if rf.feature_importance:
        print("    RF 特征重要性 (Top 5):")
        for feat, imp in list(rf.feature_importance.items())[:5]:
            print(f"      {feat}: {imp:.4f}")
    rf_path = os.path.join(save_dir, f'rf_model_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pkl')
    rf.save(rf_path)
    print(f"    RF 已保存: {rf_path}")
    rf_latest = os.path.join(save_dir, 'rf_latest.pkl')
    joblib.dump(rf, rf_latest)
    # 也保存底层 sklearn 模型
    joblib.dump(rf.model, os.path.join(save_dir, 'rf_sklearn_latest.pkl'))
    print(f"    RF latest: {rf_latest}")

    # Step 5: 评估
    print(f"\n[5/5] 评估模型…")
    models = {'KNN': knn, 'RF': rf}
    eval_df = evaluate_models(X, y, models)
    if eval_df is not None and len(eval_df) > 0:
        numeric_cols = ['MAE', 'RMSE', 'MAPE', 'R2']
        summary = eval_df.groupby('model')[numeric_cols].mean().round(2)
        print("\n  评估结果汇总 (5-Fold TimeSeriesCV):")
        print(f"  {'模型':<6} {'MAE':<8} {'RMSE':<8} {'MAPE':<8} {'R2':<8}")
        print(f"  {'-'*40}")
        for model_name, row in summary.iterrows():
            mape_str = f"{row['MAPE']:<8.2f}" if not pd.isna(row['MAPE']) else "N/A     "
            print(f"  {model_name:<6} {row['MAE']:<8.2f} {row['RMSE']:<8.2f} "
                  f"{mape_str} {row['R2']:<8.3f}")

    # 保存评估指标
    best_model = 'RF'  # 默认RF最好
    if eval_df is not None and len(eval_df) > 0:
        rf_avg = eval_df[eval_df['model'] == 'RF']['R2'].mean()
        knn_avg = eval_df[eval_df['model'] == 'KNN']['R2'].mean()
        best_model = 'RF' if rf_avg >= knn_avg else 'KNN'

    metrics = {
        'best_model': best_model,
        'training_date': datetime.now().isoformat(),
        'total_records': len(df),
        'train_samples': len(X_train),
        'test_samples': len(X_test),
        'feature_count': X.shape[1],
    }
    if eval_df is not None and len(eval_df) > 0:
        for model_name in ['KNN', 'RF']:
            m = eval_df[eval_df['model'] == model_name][numeric_cols].mean()
            metrics[f'{model_name}_mae'] = round(m['MAE'], 2) if not pd.isna(m['MAE']) else 0
            metrics[f'{model_name}_rmse'] = round(m['RMSE'], 2) if not pd.isna(m['RMSE']) else 0
            metrics[f'{model_name}_mape'] = round(m['MAPE'], 2) if not pd.isna(m['MAPE']) else 0
            metrics[f'{model_name}_r2'] = round(m['R2'], 3) if not pd.isna(m['R2']) else 0

    metrics_path = os.path.join(save_dir, 'metrics.json')
    import json
    with open(metrics_path, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)
    print(f"\n  评估指标已保存: {metrics_path}")

    print("\n" + "=" * 60)
    print(f"  训练完成! 最优模型: {best_model}")
    print("=" * 60)

    return metrics


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='训练交通流量预测模型')
    parser.add_argument('--days', type=int, default=None, help='仅使用最近N天数据')
    parser.add_argument('--horizon', type=int, default=5, help='预测粒度(分钟)')
    args = parser.parse_args()

    train_models(days=args.days, horizon_minutes=args.horizon)
