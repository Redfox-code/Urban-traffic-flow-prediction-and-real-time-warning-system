"""SUMO仿真数据导入脚本 — 使用独立SQLite连接避免锁DB"""
import sys
import os
import sqlite3
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))


def import_sumo_data(xml_path, db_path=None):
    """将SUMO e2_output.xml导入数据库（直接SQLite写入，不通过Flask）"""
    if db_path is None:
        db_path = os.path.join(os.path.dirname(__file__), '..', 'backend', 'instance', 'dev.db')

    # 1. 解析SUMO XML
    tree = ET.parse(xml_path)
    records = []
    for interval in tree.iter('interval'):
        veh = int(float(interval.get('nVehEntered', 0)))
        speed = float(interval.get('meanSpeed', -1))
        occ = float(interval.get('meanOccupancy', 0))
        if veh == 0 and speed == -1:
            veh, speed = 0, 0.0
        records.append({
            'detector_id': interval.get('id'),
            'vehicle_count': veh,
            'avg_speed': round(speed, 2),
            'occupancy': round(occ, 2),
        })
    if not records:
        print('[IMPORT] XML解析结果为空')
        return 0

    # 2. 直接SQLite写入
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # 获取检测器→路段映射
    cur.execute('SELECT id, section_id FROM traffic_detectors LIMIT 1')
    row = cur.fetchone()
    if not row:
        conn.close()
        print('[IMPORT] 数据库无检测器，请先运行 seed_data.py')
        return 0
    detector_id, section_id = row

    # 3. 批量插入
    count = 0
    for rec in records:
        cur.execute(
            'INSERT INTO traffic_records (section_id, detector_id, vehicle_count, avg_speed, occupancy, timestamp) VALUES (?, ?, ?, ?, ?, ?)',
            (section_id, detector_id, rec['vehicle_count'], rec['avg_speed'], rec['occupancy'],
             (datetime.utcnow() - timedelta(minutes=count * 15)).isoformat())
        )
        count += 1

    conn.commit()
    conn.close()
    print(f'[IMPORT] 成功导入 {count} 条流量记录')
    return count


if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(__file__), 'data', 'raw', 'e2_output.xml')
    if not os.path.exists(path):
        print(f'[IMPORT] 文件不存在: {path}')
        sys.exit(1)
    import_sumo_data(path)
