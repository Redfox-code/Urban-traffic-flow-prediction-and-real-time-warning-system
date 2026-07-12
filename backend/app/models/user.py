"""用户模型"""
from app import db
from datetime import datetime


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='traveler')  # admin / analyst / traveler
    preferences = db.Column(db.Text, default='{}')  # JSON: {defaultTime,commuteAlert,alertBefore}
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    route_records = db.relationship('RouteRecord', backref='user', lazy=True)
    system_logs = db.relationship('SystemLog', backref='user', lazy=True)
