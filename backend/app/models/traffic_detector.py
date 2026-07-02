"""检测器模型"""
from app import db
from datetime import datetime


class TrafficDetector(db.Model):
    __tablename__ = 'traffic_detectors'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    section_id = db.Column(db.Integer, db.ForeignKey('traffic_sections.id'), nullable=False)
    type = db.Column(db.Enum('e2', 'induction_loop'), nullable=False, default='e2')
    position = db.Column(db.Numeric(6, 2), nullable=False, comment='距起点距离(km)')
    status = db.Column(db.Enum('active', 'inactive', 'maintenance'), nullable=False, default='active')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    records = db.relationship('TrafficRecord', backref='detector', lazy=True)
