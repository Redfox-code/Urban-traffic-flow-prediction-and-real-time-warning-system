"""数据预处理 Pipeline — Agent-Algorithm"""
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler


def parse_e2_output(xml_path):
    """解析 SUMO e2_output.xml → DataFrame"""
    import xml.etree.ElementTree as ET
    tree = ET.parse(xml_path)
    records = []
    for interval in tree.findall('.//interval'):
        records.append({
            'detector_id': interval.get('id'),
            'begin': float(interval.get('begin', 0)),
            'end': float(interval.get('end', 0)),
            'vehicle_count': int(float(interval.get('sampledSeconds', 0))),
            'avg_speed': float(interval.get('speed', 0)),
            'occupancy': float(interval.get('occupancy', 0)),
        })
    return pd.DataFrame(records)


def clean_data(df):
    """缺失值填充 + IQR异常值处理"""
    df = df.copy()
    for col in ['vehicle_count', 'avg_speed', 'occupancy']:
        if col in df.columns:
            df[col] = df.groupby('detector_id')[col].transform(lambda x: x.fillna(method='ffill').fillna(x.median()))
    for col in ['vehicle_count', 'avg_speed']:
        if col in df.columns:
            Q1, Q3 = df[col].quantile(0.25), df[col].quantile(0.75)
            df[col] = df[col].clip(Q1 - 1.5 * (Q3 - Q1), Q3 + 1.5 * (Q3 - Q1))
    if 'avg_speed' in df.columns:
        df['avg_speed'] = df['avg_speed'].clip(lower=0)
    if 'occupancy' in df.columns:
        df['occupancy'] = df['occupancy'].clip(0, 100)
    return df


def build_features(df):
    """特征工程：时间特征 + 滞后特征 + 滚动统计"""
    df = df.copy()
    df['timestamp'] = pd.to_datetime(df['end'], unit='s')
    df['hour'] = df['timestamp'].dt.hour
    df['day_of_week'] = df['timestamp'].dt.dayofweek
    df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
    df['is_peak'] = df['hour'].isin([7, 8, 17, 18]).astype(int)

    df = df.sort_values(['detector_id', 'timestamp'])
    for lag in [1, 2, 3]:
        df[f'flow_lag_{lag}'] = df.groupby('detector_id')['vehicle_count'].shift(lag)
    df['flow_rolling_mean_4'] = df.groupby('detector_id')['vehicle_count'].transform(lambda x: x.rolling(4, min_periods=1).mean())
    df['flow_rolling_std_4'] = df.groupby('detector_id')['vehicle_count'].transform(lambda x: x.rolling(4, min_periods=1).std().fillna(0))
    return df


def normalize(df, scaler=None):
    """归一化"""
    numeric_cols = ['vehicle_count', 'avg_speed', 'occupancy', 'hour', 'day_of_week',
                    'flow_lag_1', 'flow_lag_2', 'flow_lag_3',
                    'flow_rolling_mean_4', 'flow_rolling_std_4']
    cols = [c for c in numeric_cols if c in df.columns]
    if scaler is None:
        scaler = StandardScaler()
        df[cols] = scaler.fit_transform(df[cols])
        return df, scaler
    df[cols] = scaler.transform(df[cols])
    return df, scaler


def run_pipeline(xml_path):
    """一键执行完整数据管道"""
    raw = parse_e2_output(xml_path)
    df = clean_data(raw)
    df = build_features(df)
    feature_cols = [c for c in df.columns if c not in ['detector_id', 'timestamp', 'begin', 'end', 'vehicle_count']]
    X = df[feature_cols].dropna()
    y = df.loc[X.index, 'vehicle_count']
    X_scaled, scaler = normalize(X)
    return X_scaled, y, scaler


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        X, y, scaler = run_pipeline(sys.argv[1])
        print(f'Features: {X.shape}, Target: {y.shape}')
