"""碳排放API测试 — 全城排放汇总 + 趋势 + 路段排行 + 估算"""
import json


def _login(client, username='carb_user', role='admin'):
    """辅助：注册+登录"""
    client.post('/api/v1/auth/register', json={
        'username': username, 'password': 'pass123', 'role': role
    })
    res = client.post('/api/v1/auth/login', json={
        'username': username, 'password': 'pass123'
    })
    return res.get_json()['data']['token']


class TestCarbon:
    """TEST-03: 碳排放API测试"""

    def test_current(self, client):
        """GET /carbon/current → 200 + 全城排放汇总结构"""
        token = _login(client)
        res = client.get('/api/v1/carbon/current', headers={
            'Authorization': f'Bearer {token}'
        })
        assert res.status_code == 200
        data = res.get_json()['data']
        # 检查返回结构
        assert 'total_co2_kg' in data
        assert 'total_extra_co2_kg' in data
        assert 'sections_count' in data
        assert 'avg_speed' in data
        assert 'timestamp' in data
        # 没有数据时应该是0
        assert isinstance(data['total_co2_kg'], (int, float))
        assert isinstance(data['sections_count'], int)

    def test_trend_day(self, client):
        """GET /carbon/trend?period=day → 200"""
        token = _login(client)
        res = client.get('/api/v1/carbon/trend?period=day', headers={
            'Authorization': f'Bearer {token}'
        })
        assert res.status_code == 200
        data = res.get_json()['data']
        assert data['period'] == 'day'
        assert 'items' in data

    def test_trend_week(self, client):
        """GET /carbon/trend?period=week → 200"""
        token = _login(client)
        res = client.get('/api/v1/carbon/trend?period=week', headers={
            'Authorization': f'Bearer {token}'
        })
        assert res.status_code == 200
        data = res.get_json()['data']
        assert data['period'] == 'week'
        assert 'items' in data

    def test_trend_month(self, client):
        """GET /carbon/trend?period=month → 200"""
        token = _login(client)
        res = client.get('/api/v1/carbon/trend?period=month', headers={
            'Authorization': f'Bearer {token}'
        })
        assert res.status_code == 200
        data = res.get_json()['data']
        assert data['period'] == 'month'
        assert 'items' in data

    def test_trend_invalid_period(self, client):
        """无效period参数 → 降级为day"""
        token = _login(client)
        res = client.get('/api/v1/carbon/trend?period=invalid', headers={
            'Authorization': f'Bearer {token}'
        })
        assert res.status_code == 200
        data = res.get_json()['data']
        assert data['period'] == 'day'

    def test_sections_top(self, client):
        """GET /carbon/sections/top → 200 + Top10"""
        token = _login(client)
        res = client.get('/api/v1/carbon/sections/top', headers={
            'Authorization': f'Bearer {token}'
        })
        assert res.status_code == 200
        data = res.get_json()
        assert 'items' in data['data']

    def test_sections_top_limit(self, client):
        """GET /carbon/sections/top?limit=5 → 200"""
        token = _login(client)
        res = client.get('/api/v1/carbon/sections/top?limit=5', headers={
            'Authorization': f'Bearer {token}'
        })
        assert res.status_code == 200
        data = res.get_json()['data']
        assert 'items' in data

    def test_estimate_default(self, client):
        """POST /carbon/estimate 默认参数 → 200 + 合理排放值"""
        token = _login(client)
        res = client.post('/api/v1/carbon/estimate', json={}, headers={
            'Authorization': f'Bearer {token}'
        })
        assert res.status_code == 200
        data = res.get_json()['data']
        assert 'total_co2_kg' in data
        assert 'normal_co2_kg' in data
        assert 'extra_co2_kg' in data
        # 默认参数(30km/h, 100veh) 应产生正排放
        assert data['total_co2_kg'] > 0

    def test_estimate_custom(self, client):
        """POST /carbon/estimate 自定义参数 → 200"""
        token = _login(client)
        res = client.post('/api/v1/carbon/estimate', json={
            'avg_speed_kmh': 60,
            'vehicle_count': 200
        }, headers={'Authorization': f'Bearer {token}'})
        assert res.status_code == 200
        data = res.get_json()['data']
        assert data['total_co2_kg'] > 0
        # 更高速度产生更少额外排放
        assert data['extra_co2_kg'] >= 0

    def test_estimate_comparison(self, client):
        """碳排放与速度的反比关系验证

        低速(拥堵)排放 > 高速(畅通)排放
        """
        token = _login(client)
        # 低速场景
        slow_res = client.post('/api/v1/carbon/estimate', json={
            'avg_speed_kmh': 10, 'vehicle_count': 100
        }, headers={'Authorization': f'Bearer {token}'})
        # 高速场景
        fast_res = client.post('/api/v1/carbon/estimate', json={
            'avg_speed_kmh': 60, 'vehicle_count': 100
        }, headers={'Authorization': f'Bearer {token}'})
        slow_co2 = slow_res.get_json()['data']['total_co2_kg']
        fast_co2 = fast_res.get_json()['data']['total_co2_kg']
        # 低速拥堵排放应明显高于高速畅通排放
        assert slow_co2 > fast_co2, \
            f'低速({10}km/h)排放{slow_co2}应高于高速(60km/h)排放{fast_co2}'
