"""RBAC权限测试 — 三用户角色 platform 权限验证"""
import json


def _register_and_login(client, username, password, role):
    """辅助：注册+登录，返回 (token, role)"""
    client.post('/api/v1/auth/register', json={
        'username': username, 'password': password, 'role': role
    })
    res = client.post('/api/v1/auth/login', json={
        'username': username, 'password': password
    })
    assert res.status_code == 200
    data = res.get_json()['data']
    return data['token'], data['user']['role']


class TestRBAC:
    """TEST-01: RBAC权限测试"""

    def test_register_admin(self, client):
        """管理员注册admin角色 → 201 + role=admin"""
        res = client.post('/api/v1/auth/register', json={
            'username': 'admin_rbac', 'password': 'pass123', 'role': 'admin'
        })
        assert res.status_code == 201
        data = res.get_json()
        assert data['data']['role'] == 'admin'

    def test_register_analyst(self, client):
        """分析员注册analyst角色 → 201 + role=analyst"""
        res = client.post('/api/v1/auth/register', json={
            'username': 'analyst_rbac', 'password': 'pass123', 'role': 'analyst'
        })
        assert res.status_code == 201
        data = res.get_json()
        assert data['data']['role'] == 'analyst'

    def test_register_traveler(self, client):
        """出行者注册traveler角色 → 201 + role=traveler"""
        res = client.post('/api/v1/auth/register', json={
            'username': 'traveler_rbac', 'password': 'pass123', 'role': 'traveler'
        })
        assert res.status_code == 201
        data = res.get_json()
        assert data['data']['role'] == 'traveler'

    def test_register_invalid_role(self, client):
        """无效角色 → 400"""
        res = client.post('/api/v1/auth/register', json={
            'username': 'invalid_role', 'password': 'pass123', 'role': 'superadmin'
        })
        assert res.status_code == 400

    def test_auth_me(self, client):
        """GET /auth/me 返回当前用户信息含角色"""
        token, _ = _register_and_login(client, 'me_test', 'pass123', 'analyst')
        res = client.get('/api/v1/auth/me', headers={
            'Authorization': f'Bearer {token}'
        })
        assert res.status_code == 200
        data = res.get_json()
        assert data['data']['username'] == 'me_test'
        assert data['data']['role'] == 'analyst'

    def test_auth_me_no_token(self, client):
        """未登录访问/auth/me → 401"""
        res = client.get('/api/v1/auth/me')
        assert res.status_code == 401

    def test_auth_roles(self, client):
        """GET /auth/roles 返回三个角色"""
        res = client.get('/api/v1/auth/roles')
        assert res.status_code == 200
        data = res.get_json()
        roles = data['data']['roles']
        assert 'admin' in roles
        assert 'analyst' in roles
        assert 'traveler' in roles

    def test_analyst_can_access_analyst_api(self, client):
        """分析员访问analyst-allowed API → 200"""
        token, _ = _register_and_login(client, 'ana_api', 'pass123', 'analyst')
        res = client.post('/api/v1/signal/calculate', json={
            'intersection_id': 'test',
            'phases': [{'phase_id': 'A', 'flow': 500, 'saturation_flow': 1800}],
            'loss_time_per_phase': 5,
            'current_cycle': 120
        }, headers={'Authorization': f'Bearer {token}'})
        assert res.status_code == 200

    def test_analyst_cannot_access_admin_api(self, client):
        """分析员访问admin-only API → 403"""
        token, _ = _register_and_login(client, 'ana_forbid', 'pass123', 'analyst')
        res = client.post('/api/v1/signal/apply', json={
            'optimization_id': 999
        }, headers={'Authorization': f'Bearer {token}'})
        assert res.status_code == 403

    def test_traveler_cannot_access_analyst_api(self, client):
        """出行者访问analyst-allowed API → 403"""
        token, _ = _register_and_login(client, 'trav_forbid', 'pass123', 'traveler')
        res = client.post('/api/v1/signal/calculate', json={
            'phases': [{'phase_id': 'A', 'flow': 500, 'saturation_flow': 1800}]
        }, headers={'Authorization': f'Bearer {token}'})
        assert res.status_code == 403

    def test_unauthenticated_access(self, client):
        """未认证访问受保护端点 → 401"""
        for endpoint in [
            '/api/v1/auth/me',
            '/api/v1/signal/intersections',
            '/api/v1/carbon/current',
            '/api/v1/traveler/profile',
            '/api/v1/propagation/active',
            '/api/v1/emergency/records',
            '/api/v1/scenario/scenarios',
        ]:
            res = client.get(endpoint)
            assert res.status_code == 401, f'{endpoint} should return 401, got {res.status_code}'

    def test_admin_can_access_admin_api(self, client):
        """管理员访问admin-only API → 200"""
        token, _ = _register_and_login(client, 'adm_api', 'pass123', 'admin')
        # 先创建一条优化记录用于apply
        calc_res = client.post('/api/v1/signal/calculate', json={
            'intersection_id': 'test_apply',
            'phases': [{'phase_id': 'A', 'flow': 500, 'saturation_flow': 1800}],
            'loss_time_per_phase': 5,
            'current_cycle': 120
        }, headers={'Authorization': f'Bearer {token}'})
        assert calc_res.status_code == 200
        opt_id = calc_res.get_json()['data']['optimization_id']

        res = client.post('/api/v1/signal/apply', json={
            'optimization_id': opt_id
        }, headers={'Authorization': f'Bearer {token}'})
        assert res.status_code == 200
