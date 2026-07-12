"""应急调度记录模型 — Agent-Lead"""
from app import db
from datetime import datetime


class EmergencyRoute(db.Model):
    __tablename__ = 'emergency_routes'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    vehicle_type = db.Column(db.String(20), nullable=False, comment='ambulance/fire/police/other')
    origin_json = db.Column(db.Text, nullable=False, comment='起点JSON: {lat, lng, name}')
    destination_json = db.Column(db.Text, nullable=False, comment='终点JSON: {lat, lng, name}')
    route_json = db.Column(db.Text, comment='最优路径JSON: [{section_id, name, ...}]')
    green_wave_json = db.Column(db.Text, comment='绿波带建议JSON: [{intersection_id, direction, green_start, green_end}]')
    est_travel_time = db.Column(db.Float, comment='预计通行时间(秒)')
    normal_travel_time = db.Column(db.Float, comment='常规通行时间(秒)')
    status = db.Column(db.String(20), default='active', comment='active/completed/cancelled')
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), comment='调度员ID')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    creator = db.relationship('User', backref='emergency_routes')
