"""预警事件模型"""
from app import db
from datetime import datetime


class WarningEvent(db.Model):
    __tablename__ = 'warning_events'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    section_id = db.Column(db.Integer, db.ForeignKey('traffic_sections.id'), nullable=False)
    level = db.Column(db.Enum('WARNING', 'CRITICAL'), nullable=False)
    message = db.Column(db.String(500), nullable=False)
    trigger_flow = db.Column(db.Numeric(8, 2), nullable=False)
    threshold = db.Column(db.Numeric(8, 2), nullable=False)
    is_resolved = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)

    __table_args__ = (
        db.Index('idx_warning_resolved', 'is_resolved', 'created_at'),
    )
