"""认证模块 — /api/v1/auth/* — Agent-Lead 负责"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['POST'])
def login():
    """POST /api/v1/auth/login — 用户登录"""
    data = request.get_json()
    # TODO D7: 实现JWT登录逻辑
    return jsonify({'code': 200, 'data': {}, 'message': 'ok'})


@auth_bp.route('/register', methods=['POST'])
def register():
    """POST /api/v1/auth/register — 用户注册"""
    # TODO D7: 实现注册逻辑
    return jsonify({'code': 201, 'data': {}, 'message': 'ok'})


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required()
def refresh():
    """POST /api/v1/auth/refresh — 刷新Token"""
    # TODO D7: 实现Token刷新
    return jsonify({'code': 200, 'data': {}, 'message': 'ok'})
