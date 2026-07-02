"""数据库Seed脚本 — 预置24条路段+40个检测器"""
from app import create_app, db
from app.models.user import User
from app.models.traffic_section import TrafficSection
from app.models.traffic_detector import TrafficDetector
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    db.create_all()

    # 预置用户
    if not User.query.first():
        db.session.add(User(username='admin', password_hash=generate_password_hash('admin123'), role='admin'))
        db.session.add(User(username='analyst', password_hash=generate_password_hash('analyst123'), role='analyst'))

    # 预置24条路段（模拟6x4城市路网）
    names = [
        '长安街东段','长安街西段','建国路','复兴路',
        '东三环北路','东三环南路','西三环北路','西三环南路',
        '北二环东路','北二环西路','南二环东路','南二环西路',
        '朝阳路','海淀路','丰台路','石景山路',
        '中关村大街','学院路','知春路','成府路',
        '平安大街','两广路','通惠河路','机场高速辅路',
    ]
    base_lng, base_lat = 116.38, 39.90
    for i, name in enumerate(names):
        if not TrafficSection.query.filter_by(name=name).first():
            row, col = i // 6, i % 6
            lng = base_lng + col * 0.008
            lat = base_lat + row * 0.006
            section = TrafficSection(
                name=name, capacity=1500 + (i % 3) * 500, length=1.5 + (i % 5) * 0.5,
                max_speed=40 + (i % 3) * 20,
                coordinates={'start': [lng, lat], 'end': [lng + 0.005, lat + 0.003]}
            )
            db.session.add(section)
            db.session.flush()

            # 每个路段1-2个检测器
            for j in range(1 + i % 2):
                db.session.add(TrafficDetector(
                    section_id=section.id, type='e2',
                    position=0.5 + j * 0.5, status='active'
                ))

    db.session.commit()
    print(f'Seed完成: {User.query.count()}用户, {TrafficSection.query.count()}路段, {TrafficDetector.query.count()}检测器')
