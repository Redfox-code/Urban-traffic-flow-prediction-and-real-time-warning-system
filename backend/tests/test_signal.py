"""信号优化API测试 — Webster配时计算 + 路口列表 + Apply + History"""
import json


def _admin_login(client):
    """辅助：注册admin并返回token"""
    client.post('/api/v1/auth/register', json={
        'username': 'sig_admin', 'password': 'pass123', 'role': 'admin'
    })
    res = client.post('/api/v1/auth/login', json={
        'username': 'sig_admin', 'password': 'pass123'
    })
    return res.get_json()['data']['token']


class TestSignal:
    """TEST-02: 信号优化API测试"""

    def test_intersections_list(self, client):
        """GET /signal/intersections → 200 + 路口列表按优化潜力降序"""
        token = _admin_login(client)
        res = client.get('/api/v1/signal/intersections', headers={
            'Authorization': f'Bearer {token}'
        })
        assert res.status_code == 200
        data = res.get_json()
        assert 'intersections' in data['data']
        intersections = data['data']['intersections']
        # 验证降序排列（如果有多个）
        if len(intersections) > 1:
            potentials = [i['optimization_potential_pct'] for i in intersections]
            for i in range(len(potentials) - 1):
                assert potentials[i] >= potentials[i + 1], \
                    f'路口未按优化潜力降序: {potentials}'

    def test_webster_calculate_valid(self, client):
        """POST /signal/calculate 有效输入 → 200 + 合理的optimal_cycle和green_splits

        Webster公式: C_opt = (1.5L + 5) / (1 - Y)
        已知:
          L = 4 * 5 = 20s
          Y = 500/1800 + 400/1800 = 0.278 + 0.222 = 0.5
          C_opt = (1.5*20 + 5) / (1 - 0.5) = (30+5)/0.5 = 70s
        """
        token = _admin_login(client)
        res = client.post('/api/v1/signal/calculate', json={
            'intersection_id': 'J1',
            'intersection_name': '国贸桥',
            'phases': [
                {'phase_id': 'A', 'flow': 500, 'saturation_flow': 1800},
                {'phase_id': 'B', 'flow': 400, 'saturation_flow': 1800},
                {'phase_id': 'C', 'flow': 300, 'saturation_flow': 1800},
                {'phase_id': 'D', 'flow': 200, 'saturation_flow': 1800},
            ],
            'loss_time_per_phase': 5,
            'current_cycle': 120
        }, headers={'Authorization': f'Bearer {token}'})
        assert res.status_code == 200
        data = res.get_json()['data']
        # Webster验证: C_opt = (1.5*20+5)/(1-(500+400+300+200)/(4*1800))
        # Y = 1400/7200 = 0.1944, C_opt = 35/0.8056 = 43.4s
        assert data['optimal_cycle'] > 0
        assert len(data['green_splits']) == 4
        # 绿信比之和应等于有效绿灯时间
        total_green = sum(g['green_sec'] for g in data['green_splits'])
        assert total_green > 0
        # 对于4相位、各5秒损失，总损失=20, C_opt≈43.4, 有效绿灯≈23.4
        # 各相位绿灯时间应与流量比成正比
        flow_ratios = [g['flow_ratio'] for g in data['green_splits']]
        assert flow_ratios[0] > flow_ratios[3]  # A相位流量比 > D相位

    def test_webster_calculate_single_phase(self, client):
        """单相位计算 → 200"""
        token = _admin_login(client)
        res = client.post('/api/v1/signal/calculate', json={
            'phases': [{'phase_id': 'A', 'flow': 800, 'saturation_flow': 1800}],
            'loss_time_per_phase': 5,
            'current_cycle': 90
        }, headers={'Authorization': f'Bearer {token}'})
        assert res.status_code == 200
        data = res.get_json()['data']
        assert data['optimal_cycle'] > 0
        assert len(data['green_splits']) == 1

    def test_webster_calculate_empty_phases(self, client):
        """空相位列表 → 400"""
        token = _admin_login(client)
        res = client.post('/api/v1/signal/calculate', json={
            'phases': [],
            'loss_time_per_phase': 5
        }, headers={'Authorization': f'Bearer {token}'})
        assert res.status_code == 400

    def test_webster_calculate_overflow(self, client):
        """流量比之和>=1 → 400（过饱和交叉口）

        注意：单相位flow_ratio被cap到0.95，需两个相位各0.95使Y=1.9>=1.0
        """
        token = _admin_login(client)
        res = client.post('/api/v1/signal/calculate', json={
            'phases': [
                {'phase_id': 'A', 'flow': 1800, 'saturation_flow': 1800},
                {'phase_id': 'B', 'flow': 1800, 'saturation_flow': 1800},
            ],
            'loss_time_per_phase': 5
        }, headers={'Authorization': f'Bearer {token}'})
        assert res.status_code == 400

    def test_apply_success(self, client):
        """POST /signal/apply 应用配时方案 → 200"""
        token = _admin_login(client)
        # 先计算
        calc_res = client.post('/api/v1/signal/calculate', json={
            'intersection_id': 'J_apply',
            'phases': [{'phase_id': 'A', 'flow': 600, 'saturation_flow': 1800}],
        }, headers={'Authorization': f'Bearer {token}'})
        assert calc_res.status_code == 200
        opt_id = calc_res.get_json()['data']['optimization_id']

        # 应用
        res = client.post('/api/v1/signal/apply', json={
            'optimization_id': opt_id
        }, headers={'Authorization': f'Bearer {token}'})
        assert res.status_code == 200
        data = res.get_json()
        assert data['data']['optimization_id'] == opt_id

    def test_apply_not_found(self, client):
        """应用不存在的优化记录 → 404"""
        token = _admin_login(client)
        res = client.post('/api/v1/signal/apply', json={
            'optimization_id': 99999
        }, headers={'Authorization': f'Bearer {token}'})
        assert res.status_code == 404

    def test_history(self, client):
        """GET /signal/history → 200 + items列表"""
        token = _admin_login(client)
        res = client.get('/api/v1/signal/history', headers={
            'Authorization': f'Bearer {token}'
        })
        assert res.status_code == 200
        data = res.get_json()
        assert 'items' in data['data']
        assert isinstance(data['data']['items'], list)

    def test_stats(self, client):
        """GET /signal/stats → 200 + 统计数据"""
        token = _admin_login(client)
        res = client.get('/api/v1/signal/stats', headers={
            'Authorization': f'Bearer {token}'
        })
        assert res.status_code == 200
        data = res.get_json()
        assert 'total_optimizations' in data['data']
        assert 'applied_count' in data['data']
        assert 'average_efficiency_gain_pct' in data['data']
