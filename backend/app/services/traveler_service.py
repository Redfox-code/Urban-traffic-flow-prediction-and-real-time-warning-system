"""出行者服务（画像+提醒+历史）— Agent-Lead"""
from app import db
from app.models.user_travel_profile import UserTravelProfile
from app.models.user_alert_history import UserAlertHistory
from app.models.route_record import RouteRecord
from datetime import datetime


# ========== 画像管理 ==========

def get_user_profiles(user_id):
    """获取用户的所有出行画像（常用路线）。"""
    profiles = UserTravelProfile.query.filter_by(
        user_id=user_id, is_active=True
    ).order_by(UserTravelProfile.frequency.desc()).all()

    return [{
        'id': p.id,
        'origin_name': p.origin_name,
        'origin_lat': p.origin_lat,
        'origin_lng': p.origin_lng,
        'dest_name': p.dest_name,
        'dest_lat': p.dest_lat,
        'dest_lng': p.dest_lng,
        'route_label': p.route_label or '常用路线',
        'depart_hour_avg': round(p.depart_hour_avg, 1) if p.depart_hour_avg else None,
        'frequency': p.frequency,
        'last_used_at': p.last_used_at.isoformat() if p.last_used_at else None,
        'alert_enabled': p.alert_enabled,
        'alert_before_min': p.alert_before_min
    } for p in profiles]


def save_route_profile(user_id, data):
    """保存/更新常用路线画像。

    Args:
        data: {origin_name, origin_lat, origin_lng, dest_name, dest_lat, dest_lng, depart_hour}
    """
    # 查找是否已存在匹配的OD对（容差0.001≈100m）
    existing = UserTravelProfile.query.filter(
        UserTravelProfile.user_id == user_id,
        UserTravelProfile.is_active == True
    ).all()

    matched = None
    for p in existing:
        if (abs((p.origin_lat or 0) - (data.get('origin_lat') or 0)) < 0.001 and
                abs((p.origin_lng or 0) - (data.get('origin_lng') or 0)) < 0.001 and
                abs((p.dest_lat or 0) - (data.get('dest_lat') or 0)) < 0.001 and
                abs((p.dest_lng or 0) - (data.get('dest_lng') or 0)) < 0.001):
            matched = p
            break

    depart_hour = data.get('depart_hour')
    if depart_hour is None and data.get('depart_time'):
        try:
            dt = datetime.fromisoformat(str(data['depart_time']).replace('Z', '+00:00'))
            depart_hour = dt.hour + dt.minute / 60.0
        except (ValueError, TypeError):
            depart_hour = 8.0  # 默认早上8点

    if matched:
        # EWMA更新
        if depart_hour is not None:
            old_avg = matched.depart_hour_avg or depart_hour
            matched.depart_hour_avg = 0.7 * old_avg + 0.3 * depart_hour
        matched.frequency = (matched.frequency or 0) + 1
        matched.last_used_at = datetime.utcnow()
        # 频次>=3自动打标签
        if matched.frequency >= 3 and not matched.route_label:
            matched.route_label = _auto_label(depart_hour or 8.0)
        db.session.commit()
        return matched.id, 'updated'
    else:
        profile = UserTravelProfile(
            user_id=user_id,
            origin_name=data.get('origin_name', ''),
            origin_lat=data.get('origin_lat'),
            origin_lng=data.get('origin_lng'),
            dest_name=data.get('dest_name', ''),
            dest_lat=data.get('dest_lat'),
            dest_lng=data.get('dest_lng'),
            depart_hour_avg=depart_hour or 8.0,
            frequency=1,
            last_used_at=datetime.utcnow()
        )
        db.session.add(profile)
        db.session.commit()
        return profile.id, 'created'


def delete_route_profile(user_id, profile_id):
    """软删除路线画像。"""
    profile = UserTravelProfile.query.filter_by(id=profile_id, user_id=user_id).first()
    if profile:
        profile.is_active = False
        db.session.commit()
        return True
    return False


def update_route_label(user_id, profile_id, label):
    """自定义路线标签。"""
    profile = UserTravelProfile.query.filter_by(id=profile_id, user_id=user_id).first()
    if profile:
        profile.route_label = label
        db.session.commit()
        return True
    return False


def _auto_label(depart_hour):
    """根据出发时间自动打标签。"""
    h = depart_hour
    from datetime import date
    weekday = date.today().weekday()  # 0=周一, 6=周日
    if weekday >= 5:
        return '周末出行'
    if 7.0 <= h <= 9.5:
        return '上班路线'
    if 17.0 <= h <= 19.5:
        return '回家路线'
    if 9.5 < h < 17.0:
        return '日常出行'
    return '常用路线'


# ========== 提醒管理 ==========

def get_user_alerts(user_id, page=1, page_size=20):
    """获取用户提醒历史（分页）。"""
    query = UserAlertHistory.query.filter_by(user_id=user_id).order_by(
        UserAlertHistory.created_at.desc()
    )
    total = query.count()
    alerts = query.offset((page - 1) * page_size).limit(page_size).all()

    return {
        'items': [{
            'id': a.id,
            'alert_type': a.alert_type,
            'title': a.title,
            'message': a.message,
            'suggested_action': a.suggested_action,
            'alternative_route_id': a.alternative_route_id,
            'is_read': a.is_read,
            'is_clicked': a.is_clicked,
            'created_at': a.created_at.isoformat() if a.created_at else None
        } for a in alerts],
        'total': total,
        'page': page,
        'page_size': page_size
    }


def mark_alert_read(user_id, alert_id):
    """标记提醒已读。"""
    alert = UserAlertHistory.query.filter_by(id=alert_id, user_id=user_id).first()
    if alert:
        alert.is_read = True
        db.session.commit()
        return True
    return False


def batch_mark_read(user_id, alert_ids):
    """批量标记已读。"""
    count = UserAlertHistory.query.filter(
        UserAlertHistory.id.in_(alert_ids),
        UserAlertHistory.user_id == user_id
    ).update({'is_read': True}, synchronize_session=False)
    db.session.commit()
    return count


def update_alert_settings(user_id, profile_id, data):
    """更新提醒偏好。"""
    profile = UserTravelProfile.query.filter_by(id=profile_id, user_id=user_id).first()
    if not profile:
        return False
    if 'alert_enabled' in data:
        profile.alert_enabled = data['alert_enabled']
    if 'alert_before_min' in data:
        profile.alert_before_min = data['alert_before_min']
    db.session.commit()
    return True


# ========== 历史记录 ==========

def get_route_history(user_id, page=1, page_size=20):
    """获取路线查询历史。"""
    query = RouteRecord.query.filter_by(user_id=user_id).order_by(
        RouteRecord.created_at.desc()
    )
    total = query.count()
    records = query.offset((page - 1) * page_size).limit(page_size).all()

    return {
        'items': [{
            'id': r.id,
            'origin_section_id': r.origin_section_id,
            'dest_section_id': r.dest_section_id,
            'distance': r.distance,
            'estimated_time': r.estimated_time,
            'created_at': r.created_at.isoformat() if r.created_at else None
        } for r in records],
        'total': total,
        'page': page,
        'page_size': page_size
    }


def delete_route_history(user_id, record_id=None):
    """删除历史记录。不传record_id则清空全部。"""
    query = RouteRecord.query.filter_by(user_id=user_id)
    if record_id:
        query = query.filter_by(id=record_id)
    count = query.delete()
    db.session.commit()
    return count
