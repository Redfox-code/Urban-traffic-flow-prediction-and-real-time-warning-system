"""pytest 配置 + fixtures"""
import pytest
from app import create_app, db


@pytest.fixture
def app():
    """测试Flask应用（SQLite内存库）"""
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def admin_token(client):
    """预置admin并返回Token"""
    client.post('/api/v1/auth/register', json={
        'username': 'admin', 'password': 'test123', 'role': 'admin'
    })
    res = client.post('/api/v1/auth/login', json={
        'username': 'admin', 'password': 'test123'
    })
    return res.json['data']['token']


@pytest.fixture
def auth_header(admin_token):
    return {'Authorization': f'Bearer {admin_token}'}
