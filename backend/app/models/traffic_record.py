"""流量记录模型 — 核心数据表"""
from app import db
from datetime import datetime


class TrafficRecord(db.Model):
    __tablename__ = 'traffic_records'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    section_id = db.Column(db.Integer, db.ForeignKey('traffic_sections.id'), nullable=False)
    detector_id = db.Column(db.Integer, db.ForeignKey('traffic_detectors.id'), nullable=False)
    vehicle_count = db.Column(db.Integer, nullable=False, comment='通过车辆数')
    avg_speed = db.Column(db.Numeric(5, 2), nullable=False, comment='平均车速(km/h)')
    occupancy = db.Column(db.Numeric(5, 2), nullable=False, comment='时间占有率(%)')
    timestamp = db.Column(db.DateTime, nullable=False, comment='采集时间')

    __table_args__ = (
        db.Index('idx_record_section_time', 'section_id', 'timestamp'),
    )
