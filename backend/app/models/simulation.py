"""仿真提交记录模型"""
from app import db
from datetime import datetime


class Simulation(db.Model):
    __tablename__ = 'simulations'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(200), nullable=False, comment='提交名称')
    sim_type = db.Column(db.String(20), nullable=False, default='batch', comment='batch/realtime')
    file_path = db.Column(db.String(500), nullable=True, comment='上传文件路径')
    file_content = db.Column(db.Text, nullable=True, comment='文件内容(小文件直接存)')
    records_imported = db.Column(db.Integer, default=0, comment='导入记录数')
    status = db.Column(db.String(20), default='uploaded', comment='uploaded/running/completed/stopped/failed')
    error_log = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
