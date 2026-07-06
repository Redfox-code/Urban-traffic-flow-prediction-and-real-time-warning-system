"""数据预处理与特征工程 — 从DB读取流量数据并生成训练特征

特征方案：
- 时间特征: hour, day_of_week, is_weekend
- 滞后特征: 前1/2/3个时间窗口的 vehicle_count（5min粒度）
- 辅助特征: avg_speed_lag_1, occupancy_lag_1
- 路段特征: section_id（类别编码）
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

import numpy as np
import pandas as pd
from datetime import datetime, timedelta


def load_traffic_data(db_uri=None, days=None):
    """从数据库加载流量数据，若不可用则加载CSV缓存或生成示例数据

    Returns:
        pd.DataFrame: 包含 section_id, vehicle_count, avg_speed, occupancy, timestamp 的DataFrame
    """
    try:
        from app import create_app, db
        from app.models import TrafficRecord
        from sqlalchemy import text

        app = create_app()
        with app.app_context():
            query = db.session.query(
                TrafficRecord.section_id,
                TrafficRecord.vehicle_count,
                TrafficRecord.avg_speed,
                TrafficRecord.occupancy,
                TrafficRecord.timestamp
            )
            if days:
                cutoff = datetime.utcnow() - timedelta(days=days)
                query = query.filter(TrafficRecord.timestamp >= cutoff)

            records = query.order_by(
                TrafficRecord.section_id,
                TrafficRecord.timestamp
            ).all()

            df = pd.DataFrame(records, columns=[
                'section_id', 'vehicle_count', 'avg_speed',
                'occupancy', 'timestamp'
            ])
            print(f"[preprocessing] 从数据库加载 {len(df)} 条记录")
            return df

    except Exception as e:
        print(f"[preprocessing] 数据库加载失败 ({e})，尝试加载CSV…")
        csv_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'traffic_records.csv')
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path, parse_dates=['timestamp'])
            print(f"[preprocessing] 从CSV加载 {len(df)} 条记录")
            return df
        raise RuntimeError(f"无法加载流量数据: {e}")


def create_lag_features(df, window=3):
    """为每个路段创建滞后特征

    Args:
        df: 按 section_id + timestamp 排序的DataFrame
        window: 滞后窗口数（默认3，即前15分钟）

    Returns:
        DataFrame with lag features added
    """
    df = df.sort_values(['section_id', 'timestamp']).reset_index(drop=True)

    for i in range(1, window + 1):
        df[f'vehicle_count_lag_{i}'] = df.groupby('section_id')['vehicle_count'].shift(i)
        if i == 1:
            df['avg_speed_lag_1'] = df.groupby('section_id')['avg_speed'].shift(1)
            df['occupancy_lag_1'] = df.groupby('section_id')['occupancy'].shift(1)

    return df


def create_time_features(df):
    """从timestamp提取时间特征"""
    df = df.copy()
    df['hour'] = df['timestamp'].dt.hour
    df['day_of_week'] = df['timestamp'].dt.dayofweek
    df['is_weekend'] = df['day_of_week'].apply(lambda x: 1 if x >= 5 else 0)
    return df


def build_features(df, window=3):
    """完整特征工程管道

    Args:
        df: 原始流量数据 (columns: section_id, vehicle_count, avg_speed, occupancy, timestamp)
        window: 滞后窗口数

    Returns:
        X: 特征矩阵 (DataFrame)
        y: 目标变量 (Series) — 当前时间步的 vehicle_count
    """
    # 确保按时间排序
    df = df.sort_values(['section_id', 'timestamp']).reset_index(drop=True)
    df = create_time_features(df)
    df = create_lag_features(df, window=window)

    # 目标：预测下一时间步的流量，所以y是下一个窗口的vehicle_count
    df['target'] = df.groupby('section_id')['vehicle_count'].shift(-1)

    # 删除包含NaN的行（滞后特征导致的边界值）
    feature_cols = ['section_id', 'hour', 'day_of_week', 'is_weekend',
                    'avg_speed_lag_1', 'occupancy_lag_1']
    for i in range(1, window + 1):
        feature_cols.append(f'vehicle_count_lag_{i}')

    df_clean = df.dropna(subset=feature_cols + ['target']).copy()

    # 路段ID用原始数值（树模型能处理）
    X = df_clean[feature_cols].copy()
    y = df_clean['target']  # 保留为Series，便于iloc索引

    print(f"[preprocessing] 特征工程完成: {X.shape[0]} 样本, {X.shape[1]} 特征")
    print(f"[preprocessing] 特征列: {feature_cols}")
    print(f"[preprocessing] 目标统计: min={y.min():.0f}, max={y.max():.0f}, "
          f"mean={y.mean():.1f}, std={y.std():.1f}")

    return X, y, df_clean


def train_test_split_time(X, y, test_ratio=0.2):
    """按时间顺序划分训练/测试集（时间序列不走random shuffle）"""
    n = len(X)
    split_idx = int(n * (1 - test_ratio))
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]
    print(f"[preprocessing] 数据划分: 训练 {len(X_train)} 条, 测试 {len(X_test)} 条 "
          f"(时间顺序, test_ratio={test_ratio})")
    return X_train, X_test, y_train, y_test
