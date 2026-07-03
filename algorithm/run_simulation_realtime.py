"""SUMO实时仿真 — Agent-Algorithm
使用TraCI逐步运行仿真，每N步将路况数据写入数据库，前端实时刷新。
用法: python run_simulation_realtime.py [--duration 3600] [--interval 100]
"""
import os, sys, time, sqlite3, argparse
from datetime import datetime

# 检查TraCI是否可用
try:
    import traci
except ImportError:
    print("TraCI不可用。请确保SUMO_HOME环境变量已设置。")
    print("pip install traci  # 或设置 SUMO_HOME 指向SUMO安装目录")
    sys.exit(1)

BASE_DIR = os.path.dirname(__file__)
STOP_FILE = os.path.join(BASE_DIR, '.stop_realtime')
CONFIG = os.path.join(BASE_DIR, 'sumo', 'config.sumocfg')
DB_PATH = os.path.join(BASE_DIR, '..', 'backend', 'instance', 'dev.db')


def run_realtime(duration=3600, interval=100):
    """实时运行SUMO仿真，每interval步写入DB一次"""
    print(f'[RT-SUMO] 启动实时仿真 (时长{duration}s, 每{interval}步写入DB)')

    # 连接SQLite
    conn = sqlite3.connect(DB_PATH)
    conn.execute('PRAGMA journal_mode=WAL')

    # 获取检测器→路段映射
    cur = conn.execute('SELECT id, section_id FROM traffic_detectors LIMIT 1')
    row = cur.fetchone()
    detector_id, section_id = row[0], row[1] if row else (1, 1)

    # 启动SUMO
    traci.start(['sumo', '-c', CONFIG])
    step = 0
    records = 0

    try:
        # 清理stop文件
        if os.path.exists(STOP_FILE):
            os.remove(STOP_FILE)

        while step < duration * 10:  # step-length=0.1 → 10步/秒
            if os.path.exists(STOP_FILE):
                print('\n[RT-SUMO] 收到停止信号')
                break
            traci.simulationStep()
            step += 1

            if step % interval == 0:
                # 读取所有检测器的实时数据
                det_ids = traci.lanearea.getIDList()
                for did in det_ids:
                    try:
                        veh = traci.lanearea.getLastStepVehicleNumber(did)
                        speed = traci.lanearea.getLastStepMeanSpeed(did)
                        occ = traci.lanearea.getLastStepOccupancy(did) * 100
                        speed = max(0, speed) if speed >= 0 else 0

                        conn.execute(
                            'INSERT INTO traffic_records (section_id, detector_id, vehicle_count, avg_speed, occupancy, timestamp) VALUES (?, ?, ?, ?, ?, ?)',
                            (section_id, detector_id, veh, round(speed, 1), round(occ, 1), datetime.utcnow().isoformat())
                        )
                        records += 1
                    except:
                        pass  # 某些检测器可能未激活

                sim_time = step * 0.1  # step-length=0.1s
                print(f'\r[RT-SUMO] t={sim_time:.0f}s 已导入{records}条记录', end='')

            if step % 10 == 0:
                conn.commit()

    except KeyboardInterrupt:
        print('\n[RT-SUMO] 用户中断')
    finally:
        conn.commit()
        conn.close()
        traci.close()
        print(f'\n[RT-SUMO] 完成: {records}条记录已写入数据库')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--duration', type=int, default=3600, help='仿真时长(秒)')
    parser.add_argument('--interval', type=int, default=100, help='写入间隔(步数), 100=10秒')
    args = parser.parse_args()
    run_realtime(args.duration, args.interval)
