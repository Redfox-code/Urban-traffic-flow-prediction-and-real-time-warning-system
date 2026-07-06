"""KNN回归预测器 — Agent-Algorithm"""
from sklearn.neighbors import KNeighborsRegressor
from sklearn.model_selection import GridSearchCV
from prediction.base_model import BaseTrafficPredictor
import joblib


class KNNPredictor(BaseTrafficPredictor):
    def __init__(self):
        self.model = None
        self.best_params = None

    def train(self, X, y):
        param_grid = {'n_neighbors': [3, 5, 7, 10, 15], 'weights': ['uniform', 'distance'], 'metric': ['euclidean', 'manhattan']}
        grid = GridSearchCV(KNeighborsRegressor(), param_grid, cv=5, scoring='neg_mean_absolute_error', n_jobs=-1)
        grid.fit(X, y)
        self.model = grid.best_estimator_
        self.best_params = grid.best_params_

    def predict(self, X):
        return self.model.predict(X)

    def get_params(self):
        return self.best_params
