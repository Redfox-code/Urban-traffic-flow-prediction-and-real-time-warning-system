"""SUMO仿真数据导入脚本 — Agent-Algorithm
将 e2_output.xml 的数据解析后写入 backend/traffic_records 表。
用法: cd algorithm && python import_sumo_data.py [e2_output.xml路径]
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
from app import create_app, db
from app.models.traffic_section import TrafficSection
from app.models.traffic_detector import TrafficDetector
from app.models.traffic_record import TrafficRecord
from preprocessor import parse_e2_output
from datetime import datetime, timedelta


def import_sumo_data(xml_path):
    """将SUMO e2_output.xml导入数据库"""
    app = create_app()
    with app.app_context():
        # 1. 解析SUMO输出
        df = parse_e2_output(xml_path)
        if df.empty:
            print('[IMPORT] 警告: XML解析结果为空')
            return 0

        # 2. 获取已seed的路段和检测器映射
        sections = {s.id: s for s in TrafficSection.query.all()}
        detectors = {d.id: d for d in TrafficDetector.query.all()}
        print(f'[IMPORT] 数据库中有 {len(sections)} 路段, {len(detectors)} 检测器')

        # 3. 将每条记录插入traffic_records
        count = 0
        for _, row in df.iterrows():
            det_id = row.get('detector_id', '')
            # 提取数字部分: 'det_left0to1_0' → 取第一个路段的检测器
            detector = detectors.get(1)  # fallback: 使用第一个检测器
            if not detector:
                continue
            section_id = detector.section_id

            record = TrafficRecord(
                section_id=section_id,
                detector_id=detector.id,
                vehicle_count=int(row.get('vehicle_count', 0)),
                avg_speed=float(row.get('avg_speed', 0)),
                occupancy=float(row.get('occupancy', 0)),
                timestamp=datetime.utcnow() - timedelta(minutes=count * 15)
            )
            db.session.add(record)
            count += 1

        db.session.commit()
        print(f'[IMPORT] 成功导入 {count} 条流量记录')
        return count


if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(__file__), 'data', 'raw', 'e2_output.xml')
    if not os.path.exists(path):
        print(f'[IMPORT] 文件不存在: {path}')
        print('请先运行: python run_simulation.py all  生成仿真数据')
        sys.exit(1)
    import_sumo_data(path)
