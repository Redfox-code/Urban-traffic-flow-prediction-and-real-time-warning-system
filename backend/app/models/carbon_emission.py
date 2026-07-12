"""碳排放记录模型 — Agent-Lead"""
from app import db
from datetime import datetime


class CarbonEmission(db.Model):
    __tablename__ = 'carbon_emissions'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    section_id = db.Column(db.Integer, db.ForeignKey('traffic_sections.id'), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, comment='记录时间')
    avg_speed = db.Column(db.Float, comment='平均速度(km/h)')
    vehicle_count = db.Column(db.Integer, comment='车辆数')
    total_co2_kg = db.Column(db.Float, comment='总CO2排放(kg)')
    normal_co2_kg = db.Column(db.Float, comment='正常排放量(畅通状态下)')
    extra_co2_kg = db.Column(db.Float, comment='拥堵额外排放量')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    section = db.relationship('TrafficSection', backref='carbon_emissions')
