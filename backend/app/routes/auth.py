"""认证模块 — /api/v1/auth/* — Agent-Lead"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt
from app.services.auth_service import register_user, authenticate, VALID_ROLES

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}
    user, error = authenticate(data.get('username'), data.get('password'))
    if error:
        return jsonify({'code': error[1], 'data': None, 'message': error[0]}), error[1]
    token = create_access_token(
        identity=str(user.id),
        additional_claims={'role': user.role, 'username': user.username}
    )
    return jsonify({'code': 200, 'data': {
        'token': token, 'user': {'id': user.id, 'username': user.username, 'role': user.role},
        'expires_in': 86400
    }, 'message': '登录成功'})


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json(silent=True) or {}
    user, error = register_user(data.get('username'), data.get('password'), data.get('role', 'traveler'))
    if error:
        return jsonify({'code': error[1], 'data': None, 'message': error[0]}), error[1]
    return jsonify({'code': 201, 'data': {'id': user.id, 'username': user.username, 'role': user.role},
                    'message': '注册成功'}), 201


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required()
def refresh():
    user_id = get_jwt_identity()
    claims = get_jwt()
    token = create_access_token(
        identity=user_id,
        additional_claims={'role': claims.get('role', 'traveler'), 'username': claims.get('username', '')}
    )
    return jsonify({'code': 200, 'data': {'token': token, 'expires_in': 86400}, 'message': 'Token已刷新'})


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    """获取当前用户信息（含角色）"""
    user_id = get_jwt_identity()
    claims = get_jwt()
    from app.models.user import User
    user = User.query.get(int(user_id))
    if not user:
        return jsonify({'code': 404, 'data': None, 'message': '用户不存在'}), 404
    return jsonify({'code': 200, 'data': {
        'id': user.id,
        'username': user.username,
        'role': user.role,
        'created_at': user.created_at.isoformat() if user.created_at else None
    }, 'message': 'ok'})


@auth_bp.route('/roles', methods=['GET'])
def available_roles():
    """获取可用角色列表"""
    return jsonify({'code': 200, 'data': {'roles': sorted(VALID_ROLES)}, 'message': 'ok'})
