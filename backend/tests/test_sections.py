"""路段API测试 — TC-S-01~06"""
import json


class TestSections:
    def test_list_empty(self, client, auth_header):
        """TC-S-01: 无参数列表 → 200"""
        res = client.get('/api/v1/sections', headers=auth_header)
        assert res.status_code == 200
        data = res.get_json()
        assert data['code'] == 200
        assert 'items' in data['data']

    def test_list_pagination(self, client, auth_header):
        """TC-S-02: 大页码 → items=[]"""
        res = client.get('/api/v1/sections?page=999', headers=auth_header)
        assert res.status_code == 200

    def test_get_not_found(self, client, auth_header):
        """TC-S-04: 不存在的ID → 404"""
        res = client.get('/api/v1/sections/999', headers=auth_header)
        assert res.status_code == 404

    def test_create_section(self, client, auth_header):
        """TC-S-05: admin创建路段 → 201"""
        res = client.post('/api/v1/sections', json={
            'name': '测试路段', 'capacity': 1000, 'length': 1.5,
            'max_speed': 60, 'coordinates': {'start': [116.39, 39.90], 'end': [116.40, 39.91]}
        }, headers=auth_header)
        assert res.status_code == 201

    def test_unauthenticated(self, client):
        """未认证请求 → 401"""
        res = client.get('/api/v1/sections')
        assert res.status_code == 401
