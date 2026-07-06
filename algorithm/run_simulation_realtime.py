"""实时交通数据模拟器 — Agent-Algorithm
纯Python实现的交通流模拟，不依赖TraCI，稳定可控。

核心思路：用数学函数模拟24个路段的交通流变化（高峰期、随机波动），
每秒生成一轮数据写入数据库，前端5秒刷新即可看到实时路况变化。

用法: python run_simulation_realtime.py [--duration 3600] [--interval 1]
"""
import os, sys, time, sqlite3, argparse, math, random, json
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(__file__)
STOP_FILE = os.path.join(BASE_DIR, '.stop_realtime')
PAUSE_FILE = os.path.join(BASE_DIR, '.pause_realtime')
PROGRESS_FILE = os.path.join(BASE_DIR, '.sim_progress')
PID_FILE = os.path.join(BASE_DIR, '.sim_pid')
HEARTBEAT_FILE = os.path.join(BASE_DIR, '.sim_heartbeat')
DB_PATH = os.path.join(BASE_DIR, '..', 'backend', 'instance', 'dev.db')

# 24个路段配置（与seed_data.py的路段名称一致）
SECTION_NAMES = [
    'bottom0A0', 'bottom1B0', 'bottom2C0', 'bottom3D0', 'bottom4E0', 'bottom5F0',
    'top0A3', 'top1B3', 'top2C3', 'top3D3', 'top4E3', 'top5F3',
    'left0A0', 'left1A1', 'left2A2', 'left3A3',
    'right0F0', 'right1F1', 'right2F2', 'right3F3',
    'center0A1', 'center1B1', 'center2C1', 'center3D1',
]


def _traffic_model(section_idx, seconds_elapsed):
    """交通流数学模型：输入路段编号+仿真已运行秒数，输出(车流量, 速度, 占有率)。

    模拟效果：
    - 30分钟周期的高峰/低谷波动
    - 不同路段有不同的基础流量
    - 叠加随机噪声使数据看起来真实
    """
    t = seconds_elapsed
    sid = section_idx

    # 每个路段有不同的相位偏移，避免所有路段同步变化
    phase = sid * 37  # 素数偏移，打散相位

    # 主要周期：30分钟（1800秒）一个高峰周期
    cycle1 = math.sin((t + phase) * 2 * math.pi / 1800)

    # 次要周期：5分钟（300秒）短时波动
    cycle2 = math.sin((t + phase * 3) * 2 * math.pi / 300) * 0.3

    # 长期趋势：缓慢上升后下降
    trend = math.sin(t * math.pi / 3600) * 0.2

    # 合成波动因子 (0.3 ~ 1.7)
    wave = 1.0 + cycle1 * 0.4 + cycle2 + trend

    # 基础车流量：不同路段不同 (10-60 veh/step)
    base_volume = 20 + (sid % 6) * 8

    # 加噪声
    noise = random.gauss(0, 2)
    volume = max(0, int(base_volume * wave + noise))

    # 占有率 = 车流量 * 0.7 + 噪声 (0-100%)
    occupancy = max(1, min(98, volume * 0.7 + random.uniform(-3, 8)))

    # 速度 = 上限60 - 占有率影响 (km/h)
    speed = max(5, min(60, 60 - occupancy * 0.55 + random.uniform(-3, 3)))

    return volume, round(speed, 1), round(occupancy, 1)


def _write_heartbeat():
    """写入心跳时间戳"""
    try:
        with open(HEARTBEAT_FILE, 'w') as f:
            f.write(datetime.utcnow().isoformat())
    except:
        pass


def _get_section_detector_map(conn):
    """从数据库读取路段→检测器映射"""
    rows = conn.execute(
        'SELECT s.id as section_id, d.id as detector_id, s.name '
        'FROM traffic_sections s '
        'JOIN traffic_detectors d ON d.section_id = s.id '
        'ORDER BY s.id'
    ).fetchall()
    if rows:
        return [(r[0], r[1], r[2]) for r in rows]

    # 数据库为空时用默认映射（与seed_data.py一致）
    return [(i + 1, i + 1, SECTION_NAMES[i]) for i in range(min(24, len(SECTION_NAMES)))]


def run_realtime(duration=3600, interval=1):
    """运行实时交通数据模拟

    Args:
        duration: 模拟总时长（秒），默认3600(1小时)
        interval: 数据写入间隔（秒），默认1秒
    """
    print(f'[SIM] 启动实时交通模拟 (时长{duration}s, 间隔{interval}s)')

    # 写PID文件
    with open(PID_FILE, 'w') as f:
        f.write(str(os.getpid()))
    print(f'[SIM] PID={os.getpid()}')

    # 连接数据库
    conn = sqlite3.connect(DB_PATH)
    conn.execute('PRAGMA journal_mode=WAL')

    # 获取路段→检测器映射
    mapping = _get_section_detector_map(conn)
    print(f'[SIM] 已加载{len(mapping)}个路段')

    # 启动时间
    start_time = datetime.utcnow()
    seconds = 0
    total_records = 0

    try:
        # 清理残留信号文件
        for f in [STOP_FILE, PAUSE_FILE]:
            if os.path.exists(f):
                os.remove(f)

        while seconds < duration:
            # === 信号检查 ===
            if os.path.exists(STOP_FILE):
                print('\n[SIM] 收到停止信号')
                break

            while os.path.exists(PAUSE_FILE) and not os.path.exists(STOP_FILE):
                time.sleep(0.5)
                _write_heartbeat()

            # === 生成一轮数据 ===
            sim_timestamp = start_time + timedelta(seconds=seconds)
            batch = []
            for section_id, detector_id, name in mapping:
                idx = (section_id - 1) % len(SECTION_NAMES)
                veh, speed, occ = _traffic_model(idx, seconds)
                batch.append((section_id, detector_id, veh, speed, occ,
                              sim_timestamp.isoformat()))

            # 批量写入
            conn.executemany(
                'INSERT INTO traffic_records (section_id, detector_id, vehicle_count, avg_speed, occupancy, timestamp) '
                'VALUES (?, ?, ?, ?, ?, ?)',
                batch
            )
            conn.commit()
            total_records += len(batch)

            # === 更新进度和心跳 ===
            seconds += interval
            progress = min(99, int(seconds / duration * 100))
            with open(PROGRESS_FILE, 'w') as f:
                f.write(str(progress))
            _write_heartbeat()

            if seconds % 5 == 0:
                print(f'\r[SIM] {seconds}s/{duration}s 进度{progress}% 已生成{total_records}条', end='')

            # 确保实际间隔准确（减去处理时间）
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            sleep_time = seconds - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

    except KeyboardInterrupt:
        print('\n[SIM] 用户中断')
    finally:
        conn.close()
        for f in [PROGRESS_FILE, PAUSE_FILE, STOP_FILE, PID_FILE, HEARTBEAT_FILE]:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except OSError:
                    pass
        elapsed = (datetime.utcnow() - start_time).total_seconds()
        print(f'\n[SIM] 完成: {total_records}条记录, 耗时{elapsed:.0f}s')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='实时交通数据模拟器')
    parser.add_argument('--duration', type=int, default=3600, help='模拟时长(秒)')
    parser.add_argument('--interval', type=int, default=1, help='数据写入间隔(秒)')
    args = parser.parse_args()
    run_realtime(args.duration, args.interval)
