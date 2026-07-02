"""认证模块 — /api/v1/auth/* — Agent-Lead"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app.services.auth_service import register_user, authenticate

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}
    user, error = authenticate(data.get('username'), data.get('password'))
    if error:
        return jsonify({'code': error[1], 'data': None, 'message': error[0]}), error[1]
    token = create_access_token(identity=str(user.id))
    return jsonify({'code': 200, 'data': {
        'token': token, 'user': {'id': user.id, 'username': user.username, 'role': user.role},
        'expires_in': 86400
    }, 'message': '登录成功'})


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json(silent=True) or {}
    user, error = register_user(data.get('username'), data.get('password'), data.get('role', 'analyst'))
    if error:
        return jsonify({'code': error[1], 'data': None, 'message': error[0]}), error[1]
    return jsonify({'code': 201, 'data': {'id': user.id, 'username': user.username, 'role': user.role}, 'message': '注册成功'}), 201


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required()
def refresh():
    user_id = get_jwt_identity()
    token = create_access_token(identity=user_id)
    return jsonify({'code': 200, 'data': {'token': token, 'expires_in': 86400}, 'message': 'Token已刷新'})
