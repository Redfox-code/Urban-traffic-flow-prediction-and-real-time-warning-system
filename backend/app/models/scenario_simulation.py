"""What-If场景仿真模型 — Agent-Lead"""
from app import db
from datetime import datetime


class ScenarioSimulation(db.Model):
    __tablename__ = 'scenario_simulations'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False, comment='场景名称')
    description = db.Column(db.Text, comment='场景描述')
    intervention_type = db.Column(db.String(30), nullable=False, comment='limit_flow/reroute/signal_adjust/road_closure')
    intervention_area_json = db.Column(db.Text, comment='干预区域JSON: {section_ids: [], region_name}')
    params_json = db.Column(db.Text, comment='干预参数JSON')
    baseline_result_json = db.Column(db.Text, comment='基线仿真结果JSON')
    intervention_result_json = db.Column(db.Text, comment='干预仿真结果JSON')
    improvement_pct = db.Column(db.Float, comment='综合改善百分比')
    status = db.Column(db.String(20), default='pending', comment='pending/running/completed/failed')
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), comment='创建者ID')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, comment='完成时间')

    creator = db.relationship('User', backref='scenarios')
