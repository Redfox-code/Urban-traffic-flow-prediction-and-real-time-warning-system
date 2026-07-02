"""路段模型"""
from app import db
from datetime import datetime


class TrafficSection(db.Model):
    __tablename__ = 'traffic_sections'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    capacity = db.Column(db.Integer, nullable=False, comment='通行能力(veh/h)')
    length = db.Column(db.Numeric(6, 2), nullable=False, comment='长度(km)')
    max_speed = db.Column(db.Integer, nullable=False, default=60, comment='限速(km/h)')
    coordinates = db.Column(db.JSON, nullable=False, comment='起终点+中间点坐标')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    detectors = db.relationship('TrafficDetector', backref='section', lazy=True, cascade='all, delete-orphan')
    records = db.relationship('TrafficRecord', backref='section', lazy=True, cascade='all, delete-orphan')
    predictions = db.relationship('PredictionResult', backref='section', lazy=True, cascade='all, delete-orphan')
    warnings = db.relationship('WarningEvent', backref='section', lazy=True, cascade='all, delete-orphan')
