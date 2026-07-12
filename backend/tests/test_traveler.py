"""出行者API测试 — 画像管理 + 提醒管理 + 历史记录"""
import json


def _traveler_login(client):
    """辅助：注册出行者并返回token"""
    client.post('/api/v1/auth/register', json={
        'username': 'trav_test', 'password': 'pass123', 'role': 'traveler'
    })
    res = client.post('/api/v1/auth/login', json={
        'username': 'trav_test', 'password': 'pass123'
    })
    return res.get_json()['data']['token']


class TestTraveler:
    """TEST-04: 出行者API测试"""

    # ========== 画像 (Profile) ==========

    def test_profile_empty(self, client):
        """GET /traveler/profile 初始为空"""
        token = _traveler_login(client)
        res = client.get('/api/v1/traveler/profile', headers={
            'Authorization': f'Bearer {token}'
        })
        assert res.status_code == 200
        data = res.get_json()['data']
        assert 'profiles' in data
        assert data['profiles'] == []

    def test_profile_save_route(self, client):
        """POST /traveler/profile/route 保存常用路线 → 201"""
        token = _traveler_login(client)
        res = client.post('/api/v1/traveler/profile/route', json={
            'origin_name': '家',
            'origin_lat': 39.908,
            'origin_lng': 116.397,
            'dest_name': '公司',
            'dest_lat': 39.928,
            'dest_lng': 116.427,
            'depart_hour': 8.5
        }, headers={'Authorization': f'Bearer {token}'})
        assert res.status_code in (200, 201)
        data = res.get_json()
        assert 'id' in data['data']

    def test_profile_save_duplicate(self, client):
        """保存相同OD对 → 200(updated)"""
        token = _traveler_login(client)
        # 第一次
        client.post('/api/v1/traveler/profile/route', json={
            'origin_name': '家', 'origin_lat': 39.908, 'origin_lng': 116.397,
            'dest_name': '公司', 'dest_lat': 39.928, 'dest_lng': 116.427,
        }, headers={'Authorization': f'Bearer {token}'})
        # 第二次（相同坐标，容差0.001内）
        res = client.post('/api/v1/traveler/profile/route', json={
            'origin_name': '家', 'origin_lat': 39.9085, 'origin_lng': 116.3975,
            'dest_name': '公司', 'dest_lat': 39.9285, 'dest_lng': 116.4275,
        }, headers={'Authorization': f'Bearer {token}'})
        assert res.status_code in (200, 201)
        data = res.get_json()['data']
        assert data['action'] == 'updated'

    def test_profile_get_routes(self, client):
        """保存后查询画像列表 → 含保存的路线"""
        token = _traveler_login(client)
        client.post('/api/v1/traveler/profile/route', json={
            'origin_name': '家', 'origin_lat': 39.908, 'origin_lng': 116.397,
            'dest_name': '公司', 'dest_lat': 39.928, 'dest_lng': 116.427,
        }, headers={'Authorization': f'Bearer {token}'})
        res = client.get('/api/v1/traveler/profile', headers={
            'Authorization': f'Bearer {token}'
        })
        assert res.status_code == 200
        profiles = res.get_json()['data']['profiles']
        assert len(profiles) >= 1
        assert profiles[0]['origin_name'] == '家'

    def test_profile_delete(self, client):
        """DELETE /traveler/profile/route/{id} → 200"""
        token = _traveler_login(client)
        # 先创建
        save_res = client.post('/api/v1/traveler/profile/route', json={
            'origin_name': '待删除', 'origin_lat': 39.91, 'origin_lng': 116.40,
            'dest_name': '目标', 'dest_lat': 39.92, 'dest_lng': 116.41,
        }, headers={'Authorization': f'Bearer {token}'})
        profile_id = save_res.get_json()['data']['id']

        res = client.delete(f'/api/v1/traveler/profile/route/{profile_id}', headers={
            'Authorization': f'Bearer {token}'
        })
        assert res.status_code == 200

    def test_profile_delete_not_found(self, client):
        """删除不存在的画像 → 404"""
        token = _traveler_login(client)
        res = client.delete('/api/v1/traveler/profile/route/99999', headers={
            'Authorization': f'Bearer {token}'
        })
        assert res.status_code == 404

    def test_profile_label(self, client):
        """PUT /traveler/profile/route/{id}/label 自定义标签 → 200"""
        token = _traveler_login(client)
        save_res = client.post('/api/v1/traveler/profile/route', json={
            'origin_name': 'A', 'origin_lat': 39.90, 'origin_lng': 116.39,
            'dest_name': 'B', 'dest_lat': 39.91, 'dest_lng': 116.40,
        }, headers={'Authorization': f'Bearer {token}'})
        profile_id = save_res.get_json()['data']['id']

        res = client.put(f'/api/v1/traveler/profile/route/{profile_id}/label', json={
            'label': '自定义标签'
        }, headers={'Authorization': f'Bearer {token}'})
        assert res.status_code == 200

    # ========== 提醒 (Alerts) ==========

    def test_alerts_list(self, client):
        """GET /traveler/alerts → 200 + 分页结构"""
        token = _traveler_login(client)
        res = client.get('/api/v1/traveler/alerts', headers={
            'Authorization': f'Bearer {token}'
        })
        assert res.status_code == 200
        data = res.get_json()['data']
        assert 'items' in data
        assert 'total' in data
        assert 'page' in data
        assert 'page_size' in data
        # 初始空列表
        assert data['total'] == 0

    def test_alerts_mark_read(self, client):
        """PUT /traveler/alerts/{id}/read 标记已读 → 200 或 404(无数据时)"""
        token = _traveler_login(client)
        # 先获取列表（可能为空）
        list_res = client.get('/api/v1/traveler/alerts', headers={
            'Authorization': f'Bearer {token}'
        })
        items = list_res.get_json()['data']['items']
        if not items:
            # 没有提醒，标记不存在的id应为404
            res = client.put('/api/v1/traveler/alerts/99999/read', headers={
                'Authorization': f'Bearer {token}'
            })
            assert res.status_code == 404
        else:
            alert_id = items[0]['id']
            res = client.put(f'/api/v1/traveler/alerts/{alert_id}/read', headers={
                'Authorization': f'Bearer {token}'
            })
            assert res.status_code == 200

    def test_alerts_batch_read(self, client):
        """POST /traveler/alerts/batch-read 批量已读 → 200"""
        token = _traveler_login(client)
        res = client.post('/api/v1/traveler/alerts/batch-read', json={
            'alert_ids': []
        }, headers={'Authorization': f'Bearer {token}'})
        assert res.status_code == 200
        data = res.get_json()['data']
        assert 'affected' in data
        assert data['affected'] == 0

    def test_alerts_settings(self, client):
        """PUT /traveler/alerts/settings 更新提醒偏好 → 200 或 404"""
        token = _traveler_login(client)
        # 先创建画像
        save_res = client.post('/api/v1/traveler/profile/route', json={
            'origin_name': '提醒测试', 'origin_lat': 39.90, 'origin_lng': 116.39,
            'dest_name': '目标', 'dest_lat': 39.91, 'dest_lng': 116.40,
        }, headers={'Authorization': f'Bearer {token}'})
        profile_id = save_res.get_json()['data']['id']

        res = client.put('/api/v1/traveler/alerts/settings', json={
            'profile_id': profile_id,
            'alert_enabled': True,
            'alert_before_min': 15
        }, headers={'Authorization': f'Bearer {token}'})
        assert res.status_code == 200

    # ========== 历史记录 (History) ==========

    def test_history_list(self, client):
        """GET /traveler/history → 200 + 分页结构"""
        token = _traveler_login(client)
        res = client.get('/api/v1/traveler/history', headers={
            'Authorization': f'Bearer {token}'
        })
        assert res.status_code == 200
        data = res.get_json()['data']
        assert 'items' in data
        assert 'total' in data
        assert 'page' in data

    def test_history_delete_one(self, client):
        """DELETE /traveler/history/{id} → 200 或 404"""
        token = _traveler_login(client)
        res = client.delete('/api/v1/traveler/history/99999', headers={
            'Authorization': f'Bearer {token}'
        })
        # 没有历史记录时返回404
        assert res.status_code == 404

    def test_history_clear(self, client):
        """DELETE /traveler/history 清空全部 → 200 + deleted计数"""
        token = _traveler_login(client)
        res = client.delete('/api/v1/traveler/history', headers={
            'Authorization': f'Bearer {token}'
        })
        assert res.status_code == 200
        data = res.get_json()['data']
        assert 'deleted' in data
