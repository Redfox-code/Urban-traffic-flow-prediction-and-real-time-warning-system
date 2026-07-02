"""预测模型抽象基类 — 策略模式 — Agent-Algorithm"""
from abc import ABC, abstractmethod
import joblib


class BaseTrafficPredictor(ABC):
    @abstractmethod
    def train(self, X, y): pass
    @abstractmethod
    def predict(self, X): pass
    @abstractmethod
    def get_params(self) -> dict: pass
    def save(self, path): joblib.dump(self.model, path)
    @staticmethod
    def load(path): return joblib.load(path)
