"""数据库Seed脚本 — 预置24条路段(国贸CBD真实道路)+检测器"""
from app import create_app, db
from app.models.user import User
from app.models.traffic_section import TrafficSection
from app.models.traffic_detector import TrafficDetector
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    db.create_all()

    # 清除旧数据（从依赖表开始）
    from app.models.traffic_detector import TrafficDetector
    from app.models.traffic_record import TrafficRecord
    from app.models.prediction_result import PredictionResult
    from app.models.warning_event import WarningEvent
    WarningEvent.query.delete()
    PredictionResult.query.delete()
    TrafficRecord.query.delete()
    TrafficDetector.query.delete()
    TrafficSection.query.delete()
    db.session.commit()
    print('已清除旧路段数据和检测器')

    # 预置用户
    if not User.query.first():
        db.session.add(User(username='admin', password_hash=generate_password_hash('admin123'), role='admin'))
        db.session.add(User(username='analyst', password_hash=generate_password_hash('analyst123'), role='analyst'))

    # 预置24条路段 — 北京国贸CBD区域真实道路
    # 坐标基于高德地图(GCJ-02), 与frontend roadNetwork.js + SUMO路网一致
    sections_data = [
        # === 东西向 (W→E) 7条 ===
        {'name': '通惠河北路主路西向东',   'capacity': 1200, 'length': 1.4, 'max_speed': 40,
         'coordinates': {'start': [116.4520, 39.9028], 'end': [116.4685, 39.9028],
                         'waypoints': [[116.4565, 39.9028], [116.4615, 39.9028], [116.4650, 39.9028]]}},
        {'name': '通惠河北路辅路西向东',   'capacity': 1200, 'length': 1.4, 'max_speed': 40,
         'coordinates': {'start': [116.4520, 39.9048], 'end': [116.4685, 39.9048],
                         'waypoints': [[116.4565, 39.9048], [116.4615, 39.9048], [116.4650, 39.9048]]}},
        {'name': '景辉街西向东',           'capacity': 1000, 'length': 1.4, 'max_speed': 40,
         'coordinates': {'start': [116.4520, 39.9065], 'end': [116.4685, 39.9065],
                         'waypoints': [[116.4565, 39.9065], [116.4615, 39.9065], [116.4650, 39.9065]]}},
        {'name': '建国路西向东',           'capacity': 2000, 'length': 1.4, 'max_speed': 60,
         'coordinates': {'start': [116.4520, 39.9080], 'end': [116.4685, 39.9080],
                         'waypoints': [[116.4565, 39.9080], [116.4615, 39.9080], [116.4650, 39.9080]]}},
        {'name': '景华街西向东',           'capacity': 1000, 'length': 1.4, 'max_speed': 40,
         'coordinates': {'start': [116.4520, 39.9095], 'end': [116.4685, 39.9095],
                         'waypoints': [[116.4565, 39.9095], [116.4615, 39.9095], [116.4650, 39.9095]]}},
        {'name': '光华路西向东',           'capacity': 1200, 'length': 1.4, 'max_speed': 40,
         'coordinates': {'start': [116.4520, 39.9113], 'end': [116.4685, 39.9113],
                         'waypoints': [[116.4565, 39.9113], [116.4615, 39.9113], [116.4650, 39.9113]]}},
        {'name': '光华北路西向东',         'capacity': 1000, 'length': 1.4, 'max_speed': 40,
         'coordinates': {'start': [116.4520, 39.9140], 'end': [116.4685, 39.9140],
                         'waypoints': [[116.4565, 39.9140], [116.4615, 39.9140], [116.4650, 39.9140]]}},

        # === 东西向 (E→W) 7条 ===
        {'name': '通惠河北路主路东向西',   'capacity': 1200, 'length': 1.4, 'max_speed': 40,
         'coordinates': {'start': [116.4685, 39.9028], 'end': [116.4520, 39.9028],
                         'waypoints': [[116.4650, 39.9028], [116.4615, 39.9028], [116.4565, 39.9028]]}},
        {'name': '通惠河北路辅路东向西',   'capacity': 1200, 'length': 1.4, 'max_speed': 40,
         'coordinates': {'start': [116.4685, 39.9048], 'end': [116.4520, 39.9048],
                         'waypoints': [[116.4650, 39.9048], [116.4615, 39.9048], [116.4565, 39.9048]]}},
        {'name': '景辉街东向西',           'capacity': 1000, 'length': 1.4, 'max_speed': 40,
         'coordinates': {'start': [116.4685, 39.9065], 'end': [116.4520, 39.9065],
                         'waypoints': [[116.4650, 39.9065], [116.4615, 39.9065], [116.4565, 39.9065]]}},
        {'name': '建国路东向西',           'capacity': 2000, 'length': 1.4, 'max_speed': 60,
         'coordinates': {'start': [116.4685, 39.9080], 'end': [116.4520, 39.9080],
                         'waypoints': [[116.4650, 39.9080], [116.4615, 39.9080], [116.4565, 39.9080]]}},
        {'name': '景华街东向西',           'capacity': 1000, 'length': 1.4, 'max_speed': 40,
         'coordinates': {'start': [116.4685, 39.9095], 'end': [116.4520, 39.9095],
                         'waypoints': [[116.4650, 39.9095], [116.4615, 39.9095], [116.4565, 39.9095]]}},
        {'name': '光华路东向西',           'capacity': 1200, 'length': 1.4, 'max_speed': 40,
         'coordinates': {'start': [116.4685, 39.9113], 'end': [116.4520, 39.9113],
                         'waypoints': [[116.4650, 39.9113], [116.4615, 39.9113], [116.4565, 39.9113]]}},
        {'name': '光华北路东向西',         'capacity': 1000, 'length': 1.4, 'max_speed': 40,
         'coordinates': {'start': [116.4685, 39.9140], 'end': [116.4520, 39.9140],
                         'waypoints': [[116.4650, 39.9140], [116.4615, 39.9140], [116.4565, 39.9140]]}},

        # === 南北向 (S→N) 5条 ===
        {'name': '东大桥路南向北',         'capacity': 1000, 'length': 1.2, 'max_speed': 40,
         'coordinates': {'start': [116.4520, 39.9028], 'end': [116.4520, 39.9140],
                         'waypoints': [[116.4520, 39.9048], [116.4520, 39.9065], [116.4520, 39.9080],
                                       [116.4520, 39.9095], [116.4520, 39.9113]]}},
        {'name': '金桐西路南向北',         'capacity': 1000, 'length': 1.2, 'max_speed': 40,
         'coordinates': {'start': [116.4565, 39.9028], 'end': [116.4565, 39.9140],
                         'waypoints': [[116.4565, 39.9048], [116.4565, 39.9065], [116.4565, 39.9080],
                                       [116.4565, 39.9095], [116.4565, 39.9113]]}},
        {'name': '东三环中路南向北',       'capacity': 2000, 'length': 1.2, 'max_speed': 60,
         'coordinates': {'start': [116.4615, 39.9028], 'end': [116.4615, 39.9140],
                         'waypoints': [[116.4615, 39.9048], [116.4615, 39.9065], [116.4615, 39.9080],
                                       [116.4615, 39.9095], [116.4615, 39.9113]]}},
        {'name': '针织路南向北',           'capacity': 1000, 'length': 1.2, 'max_speed': 40,
         'coordinates': {'start': [116.4650, 39.9028], 'end': [116.4650, 39.9140],
                         'waypoints': [[116.4650, 39.9048], [116.4650, 39.9065], [116.4650, 39.9080],
                                       [116.4650, 39.9095], [116.4650, 39.9113]]}},
        {'name': '西大望路南向北',         'capacity': 1200, 'length': 1.2, 'max_speed': 40,
         'coordinates': {'start': [116.4685, 39.9028], 'end': [116.4685, 39.9140],
                         'waypoints': [[116.4685, 39.9048], [116.4685, 39.9065], [116.4685, 39.9080],
                                       [116.4685, 39.9095], [116.4685, 39.9113]]}},

        # === 南北向 (N→S) 5条 ===
        {'name': '东大桥路北向南',         'capacity': 1000, 'length': 1.2, 'max_speed': 40,
         'coordinates': {'start': [116.4520, 39.9140], 'end': [116.4520, 39.9028],
                         'waypoints': [[116.4520, 39.9113], [116.4520, 39.9095], [116.4520, 39.9080],
                                       [116.4520, 39.9065], [116.4520, 39.9048]]}},
        {'name': '金桐西路北向南',         'capacity': 1000, 'length': 1.2, 'max_speed': 40,
         'coordinates': {'start': [116.4565, 39.9140], 'end': [116.4565, 39.9028],
                         'waypoints': [[116.4565, 39.9113], [116.4565, 39.9095], [116.4565, 39.9080],
                                       [116.4565, 39.9065], [116.4565, 39.9048]]}},
        {'name': '东三环中路北向南',       'capacity': 2000, 'length': 1.2, 'max_speed': 60,
         'coordinates': {'start': [116.4615, 39.9140], 'end': [116.4615, 39.9028],
                         'waypoints': [[116.4615, 39.9113], [116.4615, 39.9095], [116.4615, 39.9080],
                                       [116.4615, 39.9065], [116.4615, 39.9048]]}},
        {'name': '针织路北向南',           'capacity': 1000, 'length': 1.2, 'max_speed': 40,
         'coordinates': {'start': [116.4650, 39.9140], 'end': [116.4650, 39.9028],
                         'waypoints': [[116.4650, 39.9113], [116.4650, 39.9095], [116.4650, 39.9080],
                                       [116.4650, 39.9065], [116.4650, 39.9048]]}},
        {'name': '西大望路北向南',         'capacity': 1200, 'length': 1.2, 'max_speed': 40,
         'coordinates': {'start': [116.4685, 39.9140], 'end': [116.4685, 39.9028],
                         'waypoints': [[116.4685, 39.9113], [116.4685, 39.9095], [116.4685, 39.9080],
                                       [116.4685, 39.9065], [116.4685, 39.9048]]}},
    ]

    for sd in sections_data:
        if not TrafficSection.query.filter_by(name=sd['name']).first():
            section = TrafficSection(
                name=sd['name'], capacity=sd['capacity'], length=sd['length'],
                max_speed=sd['max_speed'],
                coordinates=sd['coordinates']
            )
            db.session.add(section)
            db.session.flush()

            # 每个路段2个检测器
            for j in range(2):
                db.session.add(TrafficDetector(
                    section_id=section.id, type='e2',
                    position=0.3 + j * 0.5, status='active'
                ))

    db.session.commit()
    print(f'Seed完成: {User.query.count()}用户, {TrafficSection.query.count()}路段, {TrafficDetector.query.count()}检测器')
