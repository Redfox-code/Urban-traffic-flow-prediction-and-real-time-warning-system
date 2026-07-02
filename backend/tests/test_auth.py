"""认证模块测试 — 基于 D4-T05 API测试用例设计"""
import json


class TestAuth:
    def test_login_success(self, client):
        """TC-A-01: 正确用户名密码 → 200"""
        client.post('/api/v1/auth/register', json={
            'username': 'test', 'password': 'pass', 'role': 'analyst'
        })
        res = client.post('/api/v1/auth/login', json={
            'username': 'test', 'password': 'pass'
        })
        assert res.status_code == 200
        data = res.get_json()
        assert data['code'] == 200
        assert 'token' in data['data']

    def test_login_wrong_password(self, client):
        """TC-A-02: 错误密码 → 401"""
        client.post('/api/v1/auth/register', json={
            'username': 'test2', 'password': 'pass', 'role': 'analyst'
        })
        res = client.post('/api/v1/auth/login', json={
            'username': 'test2', 'password': 'wrong'
        })
        assert res.status_code == 401

    def test_login_empty_body(self, client):
        """TC-A-03: 空body → 400"""
        res = client.post('/api/v1/auth/login', json={})
        assert res.status_code == 400

    def test_register_duplicate(self, client):
        """TC-A-05: 重复用户名 → 409"""
        client.post('/api/v1/auth/register', json={
            'username': 'dup', 'password': 'pass', 'role': 'analyst'
        })
        res = client.post('/api/v1/auth/register', json={
            'username': 'dup', 'password': 'pass', 'role': 'analyst'
        })
        assert res.status_code == 409

    def test_refresh_token(self, client, admin_token, auth_header):
        """TC-A-06: 有效Token刷新 → 200"""
        res = client.post('/api/v1/auth/refresh', headers=auth_header)
        assert res.status_code == 200
