"""路径规划记录模型"""
from app import db
from datetime import datetime


class RouteRecord(db.Model):
    __tablename__ = 'route_records'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    origin_section_id = db.Column(db.Integer, db.ForeignKey('traffic_sections.id'), nullable=False)
    dest_section_id = db.Column(db.Integer, db.ForeignKey('traffic_sections.id'), nullable=False)
    route_path = db.Column(db.JSON, nullable=False)
    total_distance = db.Column(db.Numeric(8, 2), nullable=False)
    estimated_time = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        db.Index('idx_route_user', 'user_id', 'created_at'),
    )
