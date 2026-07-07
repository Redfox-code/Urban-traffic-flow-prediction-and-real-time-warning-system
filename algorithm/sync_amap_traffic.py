#!/usr/bin/env python3
"""
高德交通态势API同步脚本
从高德地图交通态势API获取国贸CBD实时路况数据，写入traffic_records表

用法:
    python sync_amap_traffic.py

依赖:
    pip install requests
"""
import sys
import os
from datetime import datetime

import requests

# 添加backend路径以便导入Flask应用和数据库模型
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# ─── 高德API配置 ────────────────────────────────────────────────
AMAP_KEY = 'a7e006e65af936c9e57abc52fff9b826'
RECTANGLE = '116.44,39.898;116.48,39.918'  # 国贸CBD区域 (左下经度,纬度;右上经度,纬度)

# 状态映射: 高德status → occupancy(%) + level
STATUS_MAP = {
    1: {'occupancy': 20, 'level': 'smooth'},    # 畅通
    2: {'occupancy': 50, 'level': 'slow'},       # 缓行
    3: {'occupancy': 75, 'level': 'congested'},  # 拥堵
    4: {'occupancy': 90, 'level': 'jammed'},     # 严重拥堵
}


def fetch_amap_traffic():
    """调用高德交通态势API，返回道路列表"""
    url = 'https://restapi.amap.com/v3/traffic/status/rectangle'
    params = {
        'key': AMAP_KEY,
        'rectangle': RECTANGLE,
        'extensions': 'all',
        'output': 'JSON',
    }
    print(f'[amap] 请求高德交通态势API: rectangle={RECTANGLE}')
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.RequestException as e:
        print(f'[amap] 网络请求失败: {e}')
        return []
    except ValueError as e:
        print(f'[amap] JSON解析失败: {e}')
        return []

    if data.get('status') != '1':
        print(f'[amap] API业务失败: {data.get("info", "未知错误")}')
        return []

    roads = data.get('trafficinfo', {}).get('roads', [])
    description = data.get('trafficinfo', {}).get('description', '未知区域')
    print(f'[amap] 区域: {description}, 获取到 {len(roads)} 条道路')
    return roads


def match_section(sections, road_name):
    """按道路名匹配 traffic_sections 表

    使用子串匹配策略:
    - 高德道路名包含DB路段名 → 匹配
    - DB路段名包含高德道路名 → 匹配
    """
    if not road_name:
        return None
    for s in sections:
        db_name = s.name.strip()
        if road_name in db_name or db_name in road_name:
            return s
    return None


def get_status_mapping(status_code):
    """将高德status映射为占有率"""
    return STATUS_MAP.get(int(status_code), STATUS_MAP[1])  # 默认畅通


def sync():
    """主同步函数: 获取高德数据 → 匹配路段 → 写入traffic_records"""
    from app import create_app, db
    from app.models.traffic_section import TrafficSection
    from app.models.traffic_record import TrafficRecord

    app = create_app()

    with app.app_context():
        # 1. 获取数据库中的所有路段
        sections = TrafficSection.query.all()
        print(f'[sync] 数据库中共有 {len(sections)} 条路段')

        if not sections:
            print('[sync] 数据库路段为空，请先运行 seed_data.py')
            return

        # 2. 获取高德实时路况
        roads = fetch_amap_traffic()
        if not roads:
            print('[sync] 未获取到高德道路数据，同步终止')
            return

        # 3. 逐条匹配并写入
        now = datetime.utcnow()
        matched_count = 0
        inserted_count = 0
        unmatched_names = []

        for road in roads:
            name = road.get('name', '').strip()
            if not name:
                continue

            # 按路名匹配
            section = match_section(sections, name)
            if not section:
                unmatched_names.append(name)
                continue
            matched_count += 1

            # 解析高德API字段
            status_code = int(road.get('status', 1))
            amap_speed = float(road.get('speed', 0))

            occ_info = get_status_mapping(status_code)
            occupancy = occ_info['occupancy']

            # vehicle_count = 通行能力 * 占有率%
            vehicle_count = int(section.capacity * occupancy / 100)

            # avg_speed: 优先用高德返回的速度，为0时估算
            avg_speed = amap_speed
            if avg_speed <= 0:
                avg_speed = section.max_speed * (1 - occupancy / 100)

            # 取第一个检测器作为detector_id
            detector = section.detectors[0] if section.detectors else None
            detector_id = detector.id if detector else 1

            # 写入traffic_records
            record = TrafficRecord(
                section_id=section.id,
                detector_id=detector_id,
                vehicle_count=vehicle_count,
                avg_speed=round(avg_speed, 1),
                occupancy=round(occupancy, 1),
                timestamp=now,
            )
            db.session.add(record)
            inserted_count += 1

        # 4. 提交事务
        db.session.commit()

        # 5. 打印同步结果
        print(f'[sync] 匹配结果: {matched_count} 条道路匹配成功')
        print(f'[sync] 写入: {inserted_count} 条记录到 traffic_records 表')
        if unmatched_names:
            print(f'[sync] 未匹配的道路名 ({len(unmatched_names)} 条):')
            for uname in unmatched_names[:10]:  # 最多显示10条
                print(f'       - {uname}')
            if len(unmatched_names) > 10:
                print(f'       ... 及其他 {len(unmatched_names) - 10} 条')

        print(f'[sync] 同步完成时间: {now.isoformat()}')


def replay(speed=30):
    """回放模式：从DB读取历史数据，按时间顺序逐批回放。

    不调API。将每批记录的timestamp更新为当前时间，
    前端5秒刷新感知数据变化，模拟实时路况效果。

    Args:
        speed: 加速倍数。speed=30表示1秒回放30分钟数据
    """
    from app import create_app, db
    from app.models.traffic_record import TrafficRecord

    app = create_app()
    with app.app_context():
        # 读取所有不同的时间批次，按时间排序
        timestamps = db.session.query(TrafficRecord.timestamp)\
            .distinct()\
            .order_by(TrafficRecord.timestamp.asc())\
            .all()
        batches = [t[0] for t in timestamps]
        print(f'[replay] 共 {len(batches)} 个时间批次')

        if len(batches) < 2:
            print('[replay] 数据不足，至少需要2个批次')
            return

        # 计算相邻批次的实际时间间隔
        batch_span = (batches[-1] - batches[0]).total_seconds()
        replay_seconds = batch_span / speed
        batch_delay = replay_seconds / len(batches)
        print(f'[replay] 实际跨度 {batch_span/60:.0f}分钟, '
              f'回放速度 ×{speed}, 预计 {replay_seconds:.0f}秒完成 '
              f'(每批{batch_delay:.1f}秒)')

        for i, ts in enumerate(batches):
            # 将该批次所有记录的timestamp更新为"现在"
            now = datetime.utcnow()
            count = TrafficRecord.query.filter_by(timestamp=ts).update(
                {'timestamp': now}, synchronize_session=False
            )
            db.session.commit()
            print(f'\r[replay] {i+1}/{len(batches)} ts={ts.strftime("%H:%M")} '
                  f'→ now ({count}条)', end='')
            time.sleep(batch_delay)

        print(f'\n[replay] 回放完成')


if __name__ == '__main__':
    import argparse, time
    parser = argparse.ArgumentParser(description='高德交通态势同步')
    parser.add_argument('--continuous', action='store_true', help='持续录制模式')
    parser.add_argument('--interval', type=int, default=120, help='录制间隔(秒)')
    parser.add_argument('--max-runs', type=int, default=0, help='最大录制批数(0=无限)')
    parser.add_argument('--replay', action='store_true', help='回放模式(不调API)')
    parser.add_argument('--speed', type=int, default=30, help='回放加速倍数')
    args = parser.parse_args()

    if args.replay:
        replay(speed=args.speed)
    elif args.continuous:
        STOP_FILE = os.path.join(os.path.dirname(__file__), '.stop_realtime')
        print(f'[sync] 录制模式: 间隔{args.interval}s')
        if args.max_runs:
            print(f'[sync] 共录制 {args.max_runs} 批后自动停止')
        run = 0
        while True:
            if os.path.exists(STOP_FILE):
                print('[sync] 收到停止信号，退出')
                os.remove(STOP_FILE)
                break
            sync()
            run += 1
            if args.max_runs and run >= args.max_runs:
                print(f'[sync] 已完成 {run}/{args.max_runs} 批，自动停止')
                break
            print(f'[sync] ({run}' +
                  (f'/{args.max_runs}' if args.max_runs else '') +
                  f') 等待 {args.interval}s...\n')
            for _ in range(args.interval):
                if os.path.exists(STOP_FILE):
                    break
                try:
                    time.sleep(1)
                except KeyboardInterrupt:
                    print('\n[sync] 用户中断，退出')
                    sys.exit(0)
    else:
        sync()
