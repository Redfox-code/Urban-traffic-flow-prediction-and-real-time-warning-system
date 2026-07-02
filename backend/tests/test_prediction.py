"""预测API测试 — D4-T05 TC-P-01~06"""
class TestPrediction:
    def test_forecast_no_auth(self, client):
        res = client.get('/api/v1/predict/forecast?section_id=1')
        assert res.status_code == 401

    def test_forecast_invalid_model(self, client, auth_header):
        res = client.get('/api/v1/predict/forecast?section_id=1&model=INVALID', headers=auth_header)
        assert res.status_code == 400

    def test_forecast_missing_section(self, client, auth_header):
        res = client.get('/api/v1/predict/forecast', headers=auth_header)
        assert res.status_code == 400
