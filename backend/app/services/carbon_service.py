"""碳排放服务 — Agent-Lead"""
from app import db
from app.models.traffic_record import TrafficRecord
from app.models.traffic_section import TrafficSection
from app.models.carbon_emission import CarbonEmission
from sqlalchemy import func
from datetime import datetime, timedelta


# 简化COPERT排放系数（汽油乘用车）
# CO2(g/km) = a + b*v + c*v² + d/v
CO2_COEFFS = {'a': 250.0, 'b': -3.5, 'c': 0.02, 'd': 500.0}


def estimate_co2(avg_speed_kmh, vehicle_count):
    """估算单个路段的CO2排放量(kg/h)。

    Args:
        avg_speed_kmh: 平均速度(km/h)
        vehicle_count: 车辆数(veh/h)

    Returns:
        dict: {total_co2_kg, normal_co2_kg, extra_co2_kg}
    """
    v = max(avg_speed_kmh, 5.0)  # 最低速度5km/h避免除零
    co2_per_km = CO2_COEFFS['a'] + CO2_COEFFS['b'] * v + CO2_COEFFS['c'] * v * v + CO2_COEFFS['d'] / v
    co2_per_km = max(co2_per_km, 0)

    # 假设路段平均长度2km，车辆都跑完整个路段
    avg_length_km = 2.0
    total_co2_g = co2_per_km * avg_length_km * vehicle_count
    total_co2_kg = total_co2_g / 1000.0

    # 正常排放（自由流速度60km/h下）
    normal_co2_per_km = CO2_COEFFS['a'] + CO2_COEFFS['b'] * 60 + CO2_COEFFS['c'] * 3600 + CO2_COEFFS['d'] / 60
    normal_co2_g = max(normal_co2_per_km, 0) * avg_length_km * vehicle_count
    normal_co2_kg = normal_co2_g / 1000.0

    extra_co2_kg = max(total_co2_kg - normal_co2_kg, 0)

    return {
        'total_co2_kg': round(total_co2_kg, 2),
        'normal_co2_kg': round(normal_co2_kg, 2),
        'extra_co2_kg': round(extra_co2_kg, 2)
    }


def get_current_carbon():
    """获取当前全城碳排放汇总。

    Returns:
        dict: {total_co2_kg, total_extra_kg, sections_count, avg_speed, timestamp}
    """
    # 获取最新一批traffic_records（最近5分钟内的每条路段最新记录）
    subquery = db.session.query(
        TrafficRecord.section_id,
        func.max(TrafficRecord.timestamp).label('max_ts')
    ).filter(
        TrafficRecord.timestamp >= datetime.utcnow() - timedelta(minutes=30)
    ).group_by(TrafficRecord.section_id).subquery()

    records = TrafficRecord.query.join(
        subquery,
        (TrafficRecord.section_id == subquery.c.section_id) &
        (TrafficRecord.timestamp == subquery.c.max_ts)
    ).all()

    total_co2 = 0.0
    total_extra = 0.0
    total_speed = 0.0
    count = 0

    for r in records:
        if r.avg_speed and r.vehicle_count:
            est = estimate_co2(r.avg_speed, r.vehicle_count)
            total_co2 += est['total_co2_kg']
            total_extra += est['extra_co2_kg']
            total_speed += r.avg_speed
            count += 1

    return {
        'total_co2_kg': round(total_co2, 2),
        'total_extra_co2_kg': round(total_extra, 2),
        'sections_count': count,
        'avg_speed': round(total_speed / count, 1) if count > 0 else 0,
        'timestamp': datetime.utcnow().isoformat()
    }


def get_carbon_trend(period='day'):
    """获取碳排放趋势数据。

    Args:
        period: 'day' | 'week' | 'month'

    Returns:
        list: [{timestamp, total_co2_kg, normal_co2_kg, extra_co2_kg}, ...]
    """
    now = datetime.utcnow()
    if period == 'day':
        since = now - timedelta(hours=24)
        group_fmt = '%Y-%m-%d %H:00'
    elif period == 'week':
        since = now - timedelta(days=7)
        group_fmt = '%Y-%m-%d'
    else:
        since = now - timedelta(days=30)
        group_fmt = '%Y-%m-%d'

    records = CarbonEmission.query.filter(
        CarbonEmission.timestamp >= since
    ).order_by(CarbonEmission.timestamp.asc()).all()

    # 按时间段聚合
    grouped = {}
    for r in records:
        key = r.timestamp.strftime(group_fmt)
        if key not in grouped:
            grouped[key] = {'total': 0, 'normal': 0, 'extra': 0, 'count': 0}
        grouped[key]['total'] += r.total_co2_kg or 0
        grouped[key]['normal'] += r.normal_co2_kg or 0
        grouped[key]['extra'] += r.extra_co2_kg or 0
        grouped[key]['count'] += 1

    return [
        {
            'timestamp': k,
            'total_co2_kg': round(v['total'], 2),
            'normal_co2_kg': round(v['normal'], 2),
            'extra_co2_kg': round(v['extra'], 2),
            'sections_count': v['count']
        }
        for k, v in grouped.items()
    ]


def get_section_carbon_top(limit=10):
    """获取路段碳排放排行Top N。

    Returns:
        list: [{section_id, section_name, total_co2_kg, extra_co2_kg, avg_speed}, ...]
    """
    records = CarbonEmission.query.order_by(
        CarbonEmission.total_co2_kg.desc()
    ).limit(limit * 3).all()  # 多取一些去重

    seen = set()
    result = []
    for r in records:
        if r.section_id in seen:
            continue
        seen.add(r.section_id)
        section = TrafficSection.query.get(r.section_id)
        result.append({
            'section_id': r.section_id,
            'section_name': section.name if section else f'路段{r.section_id}',
            'total_co2_kg': round(r.total_co2_kg or 0, 2),
            'extra_co2_kg': round(r.extra_co2_kg or 0, 2),
            'avg_speed': round(r.avg_speed or 0, 1),
            'timestamp': r.timestamp.isoformat() if r.timestamp else None
        })
        if len(result) >= limit:
            break

    return result
