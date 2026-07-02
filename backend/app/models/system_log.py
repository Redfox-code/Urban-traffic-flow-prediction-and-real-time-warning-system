"""系统日志模型"""
from app import db
from datetime import datetime


class SystemLog(db.Model):
    __tablename__ = 'system_logs'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(100), nullable=False)
    details = db.Column(db.JSON, nullable=True)
    ip_address = db.Column(db.String(45), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        db.Index('idx_log_time', 'created_at'),
    )
