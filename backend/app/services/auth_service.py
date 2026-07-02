"""认证服务 — Agent-Lead"""
from app import db
from app.models.user import User
from werkzeug.security import generate_password_hash, check_password_hash


def register_user(username, password, role='analyst'):
    """注册用户，返回(user, error)"""
    if not username or not password:
        return None, ('用户名和密码不能为空', 400)
    if User.query.filter_by(username=username).first():
        return None, ('用户名已存在', 409)
    user = User(username=username, password_hash=generate_password_hash(password), role=role)
    db.session.add(user)
    db.session.commit()
    return user, None


def authenticate(username, password):
    """验证用户，返回(user, error)"""
    if not username or not password:
        return None, ('用户名和密码不能为空', 400)
    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password_hash, password):
        return None, ('用户名或密码错误', 401)
    return user, None
