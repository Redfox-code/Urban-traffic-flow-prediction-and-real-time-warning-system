"""模型训练主脚本 — Agent-Algorithm"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from algorithm.prediction.knn_predictor import KNNPredictor
from algorithm.preprocessor import run_pipeline


def train_models(xml_path):
    X, y, scaler = run_pipeline(xml_path)
    knn = KNNPredictor()
    knn.train(X.values, y.values)
    print(f'KNN best params: {knn.best_params}')
    return knn


if __name__ == '__main__':
    if len(sys.argv) > 1:
        knn = train_models(sys.argv[1])
        knn.save('backend/saved_models/knn_predictor.pkl')
        print('KNN model saved.')
