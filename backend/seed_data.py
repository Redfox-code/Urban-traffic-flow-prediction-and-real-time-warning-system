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

    # 如果OSM数据不足以填充，添加fallback
    if len(sections_data) < 10:
        sections_data = [
            {'name': '建国路', 'capacity': 2000, 'length': 1.4, 'max_speed': 60,
             'coordinates': {'start': [116.452, 39.908], 'end': [116.469, 39.908], 'waypoints': []}},
            {'name': '东三环中路', 'capacity': 2000, 'length': 1.2, 'max_speed': 60,
             'coordinates': {'start': [116.462, 39.903], 'end': [116.462, 39.914], 'waypoints': []}},
            # ... more fallbacks as needed
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
