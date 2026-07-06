"""随机森林预测器 — Agent-Algorithm"""
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GridSearchCV
from prediction.base_model import BaseTrafficPredictor


class RFPredictor(BaseTrafficPredictor):
    def __init__(self):
        self.model = None
        self.best_params = None
        self.feature_importance = None

    def train(self, X, y):
        param_grid = {'n_estimators': [100, 200], 'max_depth': [10, 15, None], 'min_samples_split': [2, 5]}
        grid = GridSearchCV(RandomForestRegressor(random_state=42, n_jobs=-1), param_grid, cv=5, scoring='neg_mean_absolute_error', n_jobs=-1)
        grid.fit(X, y)
        self.model = grid.best_estimator_
        self.best_params = grid.best_params_
        if hasattr(X, 'columns'):
            self.feature_importance = dict(sorted(zip(X.columns, self.model.feature_importances_), key=lambda x: x[1], reverse=True))

    def predict(self, X):
        return self.model.predict(X)

    def get_params(self):
        return self.best_params
