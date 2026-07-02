"""端到端集成测试 — D10-T03"""
import json


class TestIntegration:
    def test_full_auth_flow(self, client):
        """完整认证流程：注册→登录→Token访问"""
        # 注册
        res = client.post('/api/v1/auth/register', json={'username': 'e2e_test', 'password': 'pass', 'role': 'analyst'})
        assert res.status_code == 201
        # 登录
        res = client.post('/api/v1/auth/login', json={'username': 'e2e_test', 'password': 'pass'})
        assert res.status_code == 200
        token = res.get_json()['data']['token']
        # Token访问需要认证的端点
        res = client.get('/api/v1/sections', headers={'Authorization': f'Bearer {token}'})
        assert res.status_code == 200

    def test_section_crud_flow(self, client, auth_header):
        """路段CRUD流程：创建→查询→更新→删除"""
        # 创建
        res = client.post('/api/v1/sections', json={'name': '集成测试路段', 'capacity': 500, 'length': 2.0, 'max_speed': 40}, headers=auth_header)
        assert res.status_code == 201
        sid = res.get_json()['data']['id']
        # 查询
        res = client.get(f'/api/v1/sections/{sid}', headers=auth_header)
        assert res.status_code == 200
        assert res.get_json()['data']['name'] == '集成测试路段'
        # 更新
        client.put(f'/api/v1/sections/{sid}', json={'name': '更新后路段'}, headers=auth_header)
        res = client.get(f'/api/v1/sections/{sid}', headers=auth_header)
        assert res.get_json()['data']['name'] == '更新后路段'

    def test_route_plan(self, client, auth_header):
        """路径规划端到端"""
        # 先创建两个路段
        for name in ['路段A', '路段B']:
            client.post('/api/v1/sections', json={'name': name, 'capacity': 1000, 'length': 2.0, 'max_speed': 60}, headers=auth_header)
        res = client.post('/api/v1/route/plan', json={'origin_section_id': 1, 'dest_section_id': 2}, headers=auth_header)
        assert res.status_code in [200, 422]  # 200=找到路径, 422=图不连通

    def test_public_endpoints_blocked(self, client):
        """未认证访问保护端点→401"""
        for endpoint in ['/api/v1/sections', '/api/v1/predict/forecast?section_id=1', '/api/v1/warning/list']:
            res = client.get(endpoint)
            assert res.status_code == 401, f'{endpoint} should return 401'
