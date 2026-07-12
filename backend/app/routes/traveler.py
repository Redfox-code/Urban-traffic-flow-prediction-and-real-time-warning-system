"""出行者API — /api/v1/traveler/* — Agent-Lead"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.services.traveler_service import (
    get_user_profiles, save_route_profile, delete_route_profile, update_route_label,
    get_user_alerts, mark_alert_read, batch_mark_read, update_alert_settings,
    get_route_history, delete_route_history
)

traveler_bp = Blueprint('traveler', __name__)


# ========== 画像 (Profile) ==========

@traveler_bp.route('/profile', methods=['GET'])
@jwt_required()
def profile():
    """获取用户出行画像（常用路线列表）。"""
    user_id = int(get_jwt_identity())
    profiles = get_user_profiles(user_id)
    return jsonify({'code': 200, 'data': {'profiles': profiles}, 'message': 'ok'})


@traveler_bp.route('/profile/route', methods=['POST'])
@jwt_required()
def save_route():
    """保存/更新常用路线。"""
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}
    profile_id, action = save_route_profile(user_id, data)
    return jsonify({'code': 200 if action == 'updated' else 201,
                    'data': {'id': profile_id, 'action': action},
                    'message': '路线已保存' if action == 'created' else '路线已更新'})


@traveler_bp.route('/profile/route/<int:profile_id>', methods=['DELETE'])
@jwt_required()
def delete_route(profile_id):
    """删除常用路线。"""
    user_id = int(get_jwt_identity())
    ok = delete_route_profile(user_id, profile_id)
    if ok:
        return jsonify({'code': 200, 'data': None, 'message': '已删除'})
    return jsonify({'code': 404, 'data': None, 'message': '路线不存在'}), 404


@traveler_bp.route('/profile/route/<int:profile_id>/label', methods=['PUT'])
@jwt_required()
def label_route(profile_id):
    """自定义路线标签。"""
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}
    ok = update_route_label(user_id, profile_id, data.get('label', ''))
    if ok:
        return jsonify({'code': 200, 'data': None, 'message': '标签已更新'})
    return jsonify({'code': 404, 'data': None, 'message': '路线不存在'}), 404


# ========== 提醒 (Alerts) ==========

@traveler_bp.route('/alerts', methods=['GET'])
@jwt_required()
def alerts():
    """获取用户提醒列表（分页）。"""
    user_id = int(get_jwt_identity())
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    result = get_user_alerts(user_id, page, page_size)
    return jsonify({'code': 200, 'data': result, 'message': 'ok'})


@traveler_bp.route('/alerts/<int:alert_id>/read', methods=['PUT'])
@jwt_required()
def read_alert(alert_id):
    """标记提醒已读。"""
    user_id = int(get_jwt_identity())
    ok = mark_alert_read(user_id, alert_id)
    if ok:
        return jsonify({'code': 200, 'data': None, 'message': '已标记已读'})
    return jsonify({'code': 404, 'data': None, 'message': '提醒不存在'}), 404


@traveler_bp.route('/alerts/batch-read', methods=['POST'])
@jwt_required()
def batch_read():
    """批量标记已读。"""
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}
    alert_ids = data.get('alert_ids', [])
    count = batch_mark_read(user_id, alert_ids)
    return jsonify({'code': 200, 'data': {'affected': count}, 'message': f'已标记{count}条已读'})


@traveler_bp.route('/alerts/settings', methods=['PUT'])
@jwt_required()
def alert_settings():
    """更新提醒偏好。"""
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}
    profile_id = data.get('profile_id')
    ok = update_alert_settings(user_id, profile_id, data)
    if ok:
        return jsonify({'code': 200, 'data': None, 'message': '设置已更新'})
    return jsonify({'code': 404, 'data': None, 'message': '路线画像不存在'}), 404


# ========== 历史记录 (History) ==========

@traveler_bp.route('/history', methods=['GET'])
@jwt_required()
def history():
    """获取路线查询历史。"""
    user_id = int(get_jwt_identity())
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    result = get_route_history(user_id, page, page_size)
    return jsonify({'code': 200, 'data': result, 'message': 'ok'})


@traveler_bp.route('/history', methods=['POST'])
@jwt_required()
def save_history():
    """保存路线查询历史。"""
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}
    from app.models.route_record import RouteRecord
    from datetime import datetime
    record = RouteRecord(
        user_id=user_id,
        origin_section_id=data.get('origin_section_id'),
        dest_section_id=data.get('dest_section_id'),
        distance=data.get('distance'),
        estimated_time=data.get('estimated_time'),
    )
    db.session.add(record)
    db.session.commit()
    return jsonify({'code': 201, 'data': {'id': record.id}, 'message': '已保存'})


@traveler_bp.route('/history/<int:record_id>', methods=['DELETE'])
@jwt_required()
def delete_history_item(record_id):
    """删除单条历史记录。"""
    user_id = int(get_jwt_identity())
    count = delete_route_history(user_id, record_id)
    if count:
        return jsonify({'code': 200, 'data': None, 'message': '已删除'})
    return jsonify({'code': 404, 'data': None, 'message': '记录不存在'}), 404


@traveler_bp.route('/history', methods=['DELETE'])
@jwt_required()
def clear_history():
    """清空全部历史记录。"""
    user_id = int(get_jwt_identity())
    count = delete_route_history(user_id)
    return jsonify({'code': 200, 'data': {'deleted': count}, 'message': f'已清空{count}条记录'})


# ========== 偏好设置 (Preferences) ==========

@traveler_bp.route('/preferences', methods=['GET'])
@jwt_required()
def get_preferences():
    """获取用户出行偏好。"""
    import json
    from app.models.user import User
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return jsonify({'code': 404, 'data': None, 'message': '用户不存在'}), 404
    try:
        prefs = json.loads(user.preferences or '{}')
    except (json.JSONDecodeError, TypeError):
        prefs = {'defaultTime': '08:00', 'commuteAlert': True, 'alertBefore': 30}
    return jsonify({'code': 200, 'data': {'preferences': prefs}, 'message': 'ok'})


@traveler_bp.route('/preferences', methods=['PUT'])
@jwt_required()
def update_preferences():
    """更新用户出行偏好。"""
    import json
    from app.models.user import User
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return jsonify({'code': 404, 'data': None, 'message': '用户不存在'}), 404
    data = request.get_json(silent=True) or {}
    user.preferences = json.dumps(data.get('preferences', {}))
    db.session.commit()
    return jsonify({'code': 200, 'data': None, 'message': '偏好已保存'})
