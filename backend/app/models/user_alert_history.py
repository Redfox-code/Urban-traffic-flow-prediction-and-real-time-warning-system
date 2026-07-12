"""用户提醒历史模型 — Agent-Lead"""
from app import db
from datetime import datetime


class UserAlertHistory(db.Model):
    __tablename__ = 'user_alert_history'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    route_profile_id = db.Column(db.Integer, db.ForeignKey('user_travel_profiles.id'), comment='关联路线画像')
    alert_type = db.Column(db.String(30), nullable=False, comment='congestion_warning/info/emergency')
    title = db.Column(db.String(200), comment='推送标题')
    message = db.Column(db.Text, comment='推送详细内容')
    suggested_action = db.Column(db.String(300), comment='建议操作')
    alternative_route_id = db.Column(db.Integer, comment='备选路线ID')
    is_read = db.Column(db.Boolean, default=False, comment='是否已读')
    is_clicked = db.Column(db.Boolean, default=False, comment='是否点击')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user = db.relationship('User', backref='alert_history')
