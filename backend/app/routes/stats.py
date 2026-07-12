"""统计模块 — /api/v1/stats/* — Agent-Lead"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from app import db
from app.models.traffic_section import TrafficSection
from app.models.traffic_record import TrafficRecord
from app.models.warning_event import WarningEvent
from app.models.signal_optimization import SignalOptimization
from app.models.emergency_route import EmergencyRoute
from sqlalchemy import func
from datetime import datetime, timedelta

stats_bp = Blueprint('stats', __name__)


@stats_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def dashboard():
    """管理员实时监控面板 — 聚合真实DB数据。"""
    total_sections = TrafficSection.query.count()

    # 活跃预警数（未解决）
    active_warnings = WarningEvent.query.filter_by(is_resolved=False).count()
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_warnings = WarningEvent.query.filter(
        WarningEvent.created_at >= today_start
    ).count()
    today_critical = WarningEvent.query.filter(
        WarningEvent.created_at >= today_start,
        WarningEvent.level == 'critical'
    ).count()

    # 活跃应急调度数
    active_emergencies = EmergencyRoute.query.filter_by(status='active').count()

    # 信号优化统计
    total_opts = SignalOptimization.query.count()
    applied_opts = SignalOptimization.query.filter_by(is_applied=True).count()
    avg_gain = db.session.query(
        func.avg(SignalOptimization.efficiency_gain_pct)
    ).scalar() or 0

    # 实时路况聚合（最新一批记录的平均occupancy）
    latest_records = TrafficRecord.query.order_by(
        TrafficRecord.timestamp.desc()
    ).limit(100).all()
    if latest_records:
        avg_occupancy = round(sum(float(r.occupancy) for r in latest_records) / len(latest_records), 1)
        avg_speed = round(sum(float(r.avg_speed) for r in latest_records) / len(latest_records), 1)
    else:
        avg_occupancy = 0
        avg_speed = 0

    # 最近24小时流量趋势（按小时聚合）
    since_24h = datetime.utcnow() - timedelta(hours=24)
    hourly_data = db.session.query(
        func.strftime('%H', TrafficRecord.timestamp).label('hour'),
        func.avg(TrafficRecord.occupancy).label('avg_occ'),
        func.avg(TrafficRecord.avg_speed).label('avg_spd'),
        func.count(TrafficRecord.id).label('cnt')
    ).filter(
        TrafficRecord.timestamp >= since_24h
    ).group_by('hour').order_by('hour').all()

    traffic_trend = [{
        'hour': int(h.hour) if h.hour else 0,
        'avg_occupancy': round(float(h.avg_occ), 1),
        'avg_speed': round(float(h.avg_spd), 1),
        'sample_count': h.cnt
    } for h in hourly_data]

    return jsonify({'code': 200, 'data': {
        'total_sections': total_sections,
        'active_warnings': active_warnings,
        'today_warnings': today_warnings,
        'today_critical': today_critical,
        'active_emergencies': active_emergencies,
        'signal_optimizations_total': total_opts,
        'signal_optimizations_applied': applied_opts,
        'avg_efficiency_gain_pct': round(avg_gain, 1),
        'avg_occupancy': avg_occupancy,
        'avg_speed': avg_speed,
        'traffic_trend': traffic_trend,
    }, 'message': 'ok'})


@stats_bp.route('/daily_report', methods=['GET'])
@jwt_required()
def daily_report():
    """日报统计（指定日期或默认今天）。"""
    date_str = request.args.get('date')
    if date_str:
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            return jsonify({'code': 400, 'data': None, 'message': '日期格式错误，需 YYYY-MM-DD'}), 400
    else:
        target_date = datetime.utcnow()

    day_start = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = day_start + timedelta(days=1)

    day_records = TrafficRecord.query.filter(
        TrafficRecord.timestamp >= day_start,
        TrafficRecord.timestamp < day_end
    ).count()

    day_warnings = WarningEvent.query.filter(
        WarningEvent.created_at >= day_start,
        WarningEvent.created_at < day_end
    ).count()

    congested = TrafficRecord.query.filter(
        TrafficRecord.timestamp >= day_start,
        TrafficRecord.timestamp < day_end,
        TrafficRecord.occupancy > 60
    ).count()

    return jsonify({'code': 200, 'data': {
        'date': day_start.strftime('%Y-%m-%d'),
        'total_records': day_records,
        'total_warnings': day_warnings,
        'congested_records': congested,
        'congestion_rate_pct': round(congested / day_records * 100, 1) if day_records else 0,
    }, 'message': 'ok'})
