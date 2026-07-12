"""RBAC装饰器 — Agent-Lead"""
from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt, verify_jwt_in_request


def role_required(*allowed_roles):
    """检查JWT中的role字段是否在允许列表中。

    用法：
        @role_required('admin')
        @role_required('admin', 'analyst')
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            user_role = claims.get('role', 'traveler')
            if user_role not in allowed_roles:
                return jsonify({
                    'code': 403,
                    'data': None,
                    'message': f'权限不足，需要角色: {", ".join(allowed_roles)}，当前角色: {user_role}'
                }), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def optional_role(fn):
    """允许未登录用户访问，但如果已登录则解析角色信息。

    用于出行者路径规划页等免登录场景。
    通过 get_jwt() 获取role（未登录时为None）。
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request(optional=True)
            claims = get_jwt()
            user_role = claims.get('role', None) if claims else None
        except Exception:
            user_role = None
        # 将解析结果存入 kwargs 供视图函数使用
        kwargs['_current_role'] = user_role
        return fn(*args, **kwargs)
    return wrapper
