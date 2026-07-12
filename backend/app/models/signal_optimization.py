"""信号配时优化模型 — Agent-Lead"""
from app import db
from datetime import datetime


class SignalOptimization(db.Model):
    __tablename__ = 'signal_optimizations'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    intersection_id = db.Column(db.String(50), nullable=False, comment='路口标识(对应SUMO junction ID)')
    intersection_name = db.Column(db.String(100), comment='路口名称')
    current_cycle = db.Column(db.Float, comment='当前信号周期(秒)')
    suggested_cycle = db.Column(db.Float, comment='建议信号周期(Webster公式)')
    green_split_json = db.Column(db.Text, comment='各相位绿灯时间(JSON): {phase_id: green_sec}')
    efficiency_gain_pct = db.Column(db.Float, comment='通行效率提升百分比')
    delay_reduction_sec = db.Column(db.Float, comment='延误减少(秒)')
    co2_reduction_kg = db.Column(db.Float, comment='CO2减排量(kg/h)')
    is_applied = db.Column(db.Boolean, default=False, comment='是否已应用')
    applied_at = db.Column(db.DateTime, comment='应用时间')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
