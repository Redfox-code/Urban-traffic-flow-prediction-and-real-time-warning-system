"""预测结果模型"""
from app import db
from datetime import datetime


class PredictionResult(db.Model):
    __tablename__ = 'prediction_results'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    section_id = db.Column(db.Integer, db.ForeignKey('traffic_sections.id'), nullable=False)
    model_type = db.Column(db.Enum('KNN', 'RF'), nullable=False)
    predicted_flow = db.Column(db.Numeric(8, 2), nullable=False)
    confidence_lower = db.Column(db.Numeric(8, 2), nullable=False)
    confidence_upper = db.Column(db.Numeric(8, 2), nullable=False)
    prediction_horizon = db.Column(db.Integer, nullable=False, default=15)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        db.Index('idx_pred_section_time', 'section_id', 'timestamp'),
    )
