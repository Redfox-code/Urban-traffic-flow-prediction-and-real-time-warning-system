"""数据库Seed脚本 — 从OSM路网数据生成路段(国贸CBD真实道路)"""
import json, os, sys
from app import create_app, db
from app.models.user import User
from app.models.traffic_section import TrafficSection
from app.models.traffic_detector import TrafficDetector
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    db.create_all()

    # 清除旧数据
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
    print('已清除旧数据')

    # 预置用户
    if not User.query.first():
        db.session.add(User(username='admin', password_hash=generate_password_hash('admin123'), role='admin'))
        db.session.add(User(username='analyst', password_hash=generate_password_hash('analyst123'), role='analyst'))

    # 从OSM路网JSON加载路段数据
    json_path = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'src', 'data', 'roadNetwork.json')
    sections_data = []

    if os.path.exists(json_path):
        with open(json_path, 'r', encoding='utf-8') as f:
            road_data = json.load(f)
        segments = road_data.get('segments', [])
        print(f'[seed] 从OSM路网加载 {len(segments)} 条路段')

        # 取前30条最长的路段（按长度降序已排好）
        import_segments = segments[:30]
        for seg in import_segments:
            path = seg.get('path', [])
            sections_data.append({
                'name': seg['name'],
                'capacity': 1200 if seg.get('length', 0) > 500 else 800,  # 长路段高容量
                'length': round(seg.get('length', 200) / 1000, 2),  # 转为km
                'max_speed': 60 if 'trunk' in str(seg.get('type', '')).lower() or
                                   'motorway' in str(seg.get('type', '')).lower() else 40,
                'coordinates': {
                    'start': path[0] if len(path) > 0 else [0, 0],
                    'end': path[-1] if len(path) > 1 else path[0] if path else [0, 0],
                    'waypoints': path[1:-1] if len(path) > 2 else [],
                },
            })
    else:
        print('[seed] OSM路网JSON未找到，使用fallback路段')

    # 如果OSM数据不足以填充，使用国贸CBD真实道路列表
    # (与高德交通态势API返回的道路名称一致，确保sync_amap_traffic.py可匹配)
    if len(sections_data) < 10:
        sections_data = [
            # === 东西向主干道 ===
            {'name': '建国路', 'capacity': 2000, 'length': 1.4, 'max_speed': 60,
             'coordinates': {'start': [116.452, 39.908], 'end': [116.475, 39.908], 'waypoints': [[116.462, 39.908], [116.469, 39.908]]}},
            {'name': '建国门外大街', 'capacity': 2000, 'length': 1.0, 'max_speed': 60,
             'coordinates': {'start': [116.445, 39.907], 'end': [116.455, 39.907], 'waypoints': []}},
            {'name': '朝阳路', 'capacity': 1500, 'length': 1.2, 'max_speed': 50,
             'coordinates': {'start': [116.448, 39.915], 'end': [116.475, 39.915], 'waypoints': [[116.460, 39.915], [116.468, 39.915]]}},
            {'name': '朝阳门外大街', 'capacity': 1600, 'length': 0.9, 'max_speed': 50,
             'coordinates': {'start': [116.445, 39.919], 'end': [116.460, 39.919], 'waypoints': []}},
            {'name': '光华路', 'capacity': 1200, 'length': 0.8, 'max_speed': 40,
             'coordinates': {'start': [116.448, 39.912], 'end': [116.472, 39.912], 'waypoints': [[116.460, 39.912], [116.466, 39.912]]}},
            {'name': '光华北路', 'capacity': 1000, 'length': 0.7, 'max_speed': 40,
             'coordinates': {'start': [116.450, 39.915], 'end': [116.470, 39.915], 'waypoints': []}},
            {'name': '景辉街', 'capacity': 1000, 'length': 0.5, 'max_speed': 40,
             'coordinates': {'start': [116.452, 39.910], 'end': [116.470, 39.910], 'waypoints': []}},
            {'name': '景华街', 'capacity': 800, 'length': 0.4, 'max_speed': 40,
             'coordinates': {'start': [116.455, 39.913], 'end': [116.468, 39.913], 'waypoints': []}},
            {'name': '通惠河北路', 'capacity': 1800, 'length': 1.0, 'max_speed': 60,
             'coordinates': {'start': [116.448, 39.900], 'end': [116.472, 39.900], 'waypoints': [[116.460, 39.900]]}},

            # === 南北向主干道 ===
            {'name': '东三环中路', 'capacity': 2000, 'length': 1.2, 'max_speed': 60,
             'coordinates': {'start': [116.462, 39.900], 'end': [116.462, 39.918], 'waypoints': [[116.462, 39.905], [116.462, 39.912]]}},
            {'name': '东三环南路', 'capacity': 2000, 'length': 0.6, 'max_speed': 60,
             'coordinates': {'start': [116.462, 39.895], 'end': [116.462, 39.900], 'waypoints': []}},
            {'name': '东三环北路', 'capacity': 2000, 'length': 0.8, 'max_speed': 60,
             'coordinates': {'start': [116.462, 39.918], 'end': [116.462, 39.925], 'waypoints': []}},
            {'name': '东大桥路', 'capacity': 1200, 'length': 0.6, 'max_speed': 40,
             'coordinates': {'start': [116.450, 39.910], 'end': [116.450, 39.918], 'waypoints': []}},
            {'name': '金桐西路', 'capacity': 800, 'length': 0.3, 'max_speed': 40,
             'coordinates': {'start': [116.455, 39.910], 'end': [116.455, 39.915], 'waypoints': []}},
            {'name': '金桐东路', 'capacity': 800, 'length': 0.3, 'max_speed': 40,
             'coordinates': {'start': [116.458, 39.910], 'end': [116.458, 39.915], 'waypoints': []}},
            {'name': '针织路', 'capacity': 1000, 'length': 0.5, 'max_speed': 40,
             'coordinates': {'start': [116.466, 39.905], 'end': [116.466, 39.915], 'waypoints': []}},
            {'name': '西大望路', 'capacity': 1500, 'length': 0.7, 'max_speed': 50,
             'coordinates': {'start': [116.472, 39.902], 'end': [116.472, 39.916], 'waypoints': [[116.472, 39.908]]}},
            {'name': '日坛路', 'capacity': 800, 'length': 0.4, 'max_speed': 40,
             'coordinates': {'start': [116.440, 39.908], 'end': [116.440, 39.915], 'waypoints': []}},
            {'name': '永安路', 'capacity': 800, 'length': 0.4, 'max_speed': 40,
             'coordinates': {'start': [116.445, 39.912], 'end': [116.445, 39.917], 'waypoints': []}},

            # === 快速路 ===
            {'name': '京通快速路', 'capacity': 2400, 'length': 1.5, 'max_speed': 80,
             'coordinates': {'start': [116.448, 39.905], 'end': [116.480, 39.905], 'waypoints': [[116.460, 39.905], [116.470, 39.905]]}},
        ]
        print(f'[seed] 使用国贸CBD道路列表: {len(sections_data)} 条')
    else:
        # OSM数据足够，但也追加国贸CBD道路列表（与高德API匹配的路名）
        print(f'[seed] OSM路网数据: {len(sections_data)} 条，追加国贸CBD道路列表')
        guomao_roads = [
            {'name': '朝阳门外大街', 'capacity': 1600, 'length': 0.9, 'max_speed': 50,
             'coordinates': {'start': [116.445, 39.919], 'end': [116.460, 39.919], 'waypoints': []}},
            {'name': '东三环中路', 'capacity': 2000, 'length': 1.2, 'max_speed': 60,
             'coordinates': {'start': [116.462, 39.900], 'end': [116.462, 39.918], 'waypoints': [[116.462, 39.905], [116.462, 39.912]]}},
            {'name': '东三环南路', 'capacity': 2000, 'length': 0.6, 'max_speed': 60,
             'coordinates': {'start': [116.462, 39.895], 'end': [116.462, 39.900], 'waypoints': []}},
            {'name': '东三环北路', 'capacity': 2000, 'length': 0.8, 'max_speed': 60,
             'coordinates': {'start': [116.462, 39.918], 'end': [116.462, 39.925], 'waypoints': []}},
            {'name': '光华北路', 'capacity': 1000, 'length': 0.7, 'max_speed': 40,
             'coordinates': {'start': [116.450, 39.915], 'end': [116.470, 39.915], 'waypoints': []}},
            {'name': '景辉街', 'capacity': 1000, 'length': 0.5, 'max_speed': 40,
             'coordinates': {'start': [116.452, 39.910], 'end': [116.470, 39.910], 'waypoints': []}},
            {'name': '景华街', 'capacity': 800, 'length': 0.4, 'max_speed': 40,
             'coordinates': {'start': [116.455, 39.913], 'end': [116.468, 39.913], 'waypoints': []}},
            {'name': '金桐西路', 'capacity': 800, 'length': 0.3, 'max_speed': 40,
             'coordinates': {'start': [116.455, 39.910], 'end': [116.455, 39.915], 'waypoints': []}},
            {'name': '金桐东路', 'capacity': 800, 'length': 0.3, 'max_speed': 40,
             'coordinates': {'start': [116.458, 39.910], 'end': [116.458, 39.915], 'waypoints': []}},
            {'name': '针织路', 'capacity': 1000, 'length': 0.5, 'max_speed': 40,
             'coordinates': {'start': [116.466, 39.905], 'end': [116.466, 39.915], 'waypoints': []}},
            {'name': '永安路', 'capacity': 800, 'length': 0.4, 'max_speed': 40,
             'coordinates': {'start': [116.445, 39.912], 'end': [116.445, 39.917], 'waypoints': []}},
            {'name': '京通快速路', 'capacity': 2400, 'length': 1.5, 'max_speed': 80,
             'coordinates': {'start': [116.448, 39.905], 'end': [116.480, 39.905], 'waypoints': [[116.460, 39.905], [116.470, 39.905]]}},
        ]
        sections_data.extend(guomao_roads)
        print(f'[seed] 合并后共 {len(sections_data)} 条路段')

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
