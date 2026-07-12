"""用户出行画像模型 — Agent-Lead"""
from app import db
from datetime import datetime


class UserTravelProfile(db.Model):
    __tablename__ = 'user_travel_profiles'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    origin_name = db.Column(db.String(100), comment='起点名称')
    origin_lat = db.Column(db.Float, comment='起点纬度')
    origin_lng = db.Column(db.Float, comment='起点经度')
    dest_name = db.Column(db.String(100), comment='终点名称')
    dest_lat = db.Column(db.Float, comment='终点纬度')
    dest_lng = db.Column(db.Float, comment='终点经度')
    route_label = db.Column(db.String(50), comment='上班路线/回家路线/周末出行/日常出行/自定义')
    depart_hour_avg = db.Column(db.Float, comment='平均出发小时(指数加权移动平均)')
    depart_dayofweek = db.Column(db.Integer, comment='主要出行星期(0=周日)')
    frequency = db.Column(db.Integer, default=0, comment='累计查询频次')
    last_used_at = db.Column(db.DateTime, comment='最后使用时间')
    is_active = db.Column(db.Boolean, default=True, comment='是否激活')
    alert_enabled = db.Column(db.Boolean, default=True, comment='是否开启提醒')
    alert_before_min = db.Column(db.Integer, default=30, comment='提醒提前分钟数')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', backref='travel_profiles')
