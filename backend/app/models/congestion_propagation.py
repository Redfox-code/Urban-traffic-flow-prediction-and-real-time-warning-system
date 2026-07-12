"""拥堵传播记录模型 — Agent-Lead"""
from app import db
from datetime import datetime


class CongestionPropagation(db.Model):
    __tablename__ = 'congestion_propagation'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    from_section_id = db.Column(db.Integer, db.ForeignKey('traffic_sections.id'), nullable=False)
    to_section_id = db.Column(db.Integer, db.ForeignKey('traffic_sections.id'), nullable=False)
    propagation_delay = db.Column(db.Integer, nullable=False, comment='传播延迟(秒)')
    probability = db.Column(db.Float, nullable=False, comment='传播概率(0-1)')
    confidence = db.Column(db.Float, comment='置信度(0-1)')
    depth = db.Column(db.Integer, default=1, comment='传播跳数')
    from_level = db.Column(db.String(20), comment='源路段拥堵等级')
    to_level = db.Column(db.String(20), comment='目标路段拥堵等级')
    is_active = db.Column(db.Boolean, default=True, comment='是否活跃传播')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    from_section = db.relationship('TrafficSection', foreign_keys=[from_section_id])
    to_section = db.relationship('TrafficSection', foreign_keys=[to_section_id])
