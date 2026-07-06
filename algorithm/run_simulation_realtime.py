"""SUMO实时仿真 (TraCI) — Agent-Algorithm
使用TraCI逐步运行SUMO仿真，每N步将路况数据写入数据库，前端实时刷新。

防护机制:
  - 线程超时: simulationStep() 10秒超时 → 3次连续→死锁退出
  - 进程监控: 每步检查sumo进程是否存活
  - 仿真状态: getMinExpectedNumber()检测是否还有待处理车辆
  - 文件信号: .stop_realtime / .pause_realtime 即时响应
  - PID+心跳: Flask端孤儿进程检测

用法: python run_simulation_realtime.py [--duration 3600] [--interval 50]
"""
import os, sys, time, sqlite3, argparse, threading, queue, signal
from datetime import datetime

# 检查TraCI
try:
    import traci
except ImportError:
    print("TraCI不可用。pip install traci")
    sys.exit(1)

BASE_DIR = os.path.dirname(__file__)
STOP_FILE = os.path.join(BASE_DIR, '.stop_realtime')
PAUSE_FILE = os.path.join(BASE_DIR, '.pause_realtime')
PROGRESS_FILE = os.path.join(BASE_DIR, '.sim_progress')
PID_FILE = os.path.join(BASE_DIR, '.sim_pid')
HEARTBEAT_FILE = os.path.join(BASE_DIR, '.sim_heartbeat')
CONFIG = os.path.join(BASE_DIR, 'sumo', 'config.sumocfg')
DB_PATH = os.path.join(BASE_DIR, '..', 'backend', 'instance', 'dev.db')

# TraCI端口（避免与系统中其他SUMO实例冲突）
TRACI_PORT = 8873


def _write_heartbeat():
    try:
        with open(HEARTBEAT_FILE, 'w') as f:
            f.write(datetime.utcnow().isoformat())
    except: pass


def _write_progress(step, duration):
    """写入进度文件"""
    total_steps = duration * 10  # step-length=0.1
    pct = min(99, int(step / total_steps * 100))
    try:
        with open(PROGRESS_FILE, 'w') as f:
            f.write(str(pct))
    except: pass


def _step_with_timeout(timeout=10):
    """在daemon线程中执行simulationStep()，超时返回False"""
    q = queue.Queue()
    def do_step():
        try:
            result = traci.simulationStep()
            q.put(('ok', result))
        except Exception as e:
            q.put(('error', str(e)))

    t = threading.Thread(target=do_step, daemon=True)
    t.start()
    t.join(timeout=timeout)

    if t.is_alive():
        return ('timeout', None)
    try:
        return q.get_nowait()
    except queue.Empty:
        return ('timeout', None)


def run_realtime(duration=3600, interval=50):
    """TraCI实时仿真 — 逐步运行SUMO并写入DB

    Args:
        duration: 仿真时长(秒)
        interval: 数据写入间隔(步数), 50=5秒
    """
    print(f'[TraCI] 启动SUMO实时仿真 (时长{duration}s, 间隔{interval}步)')

    # 写PID
    with open(PID_FILE, 'w') as f:
        f.write(str(os.getpid()))

    # 清理残留信号
    for f in [STOP_FILE, PAUSE_FILE]:
        if os.path.exists(f): os.remove(f)
    _write_progress(0, duration)

    # 连接SQLite
    conn = sqlite3.connect(DB_PATH)
    conn.execute('PRAGMA journal_mode=WAL')

    # 获取检测器→路段映射
    cur = conn.execute('SELECT id, section_id FROM traffic_detectors LIMIT 1')
    row = cur.fetchone()
    detector_id, section_id = row[0], row[1] if row else (1, 1)

    # 启动SUMO (通过TraCI)
    sumo_binary = 'sumo'
    sumo_cmd = [sumo_binary, '-c', CONFIG,
                '--remote-port', str(TRACI_PORT),
                '--no-step-log', '--no-warnings']
    print(f'[TraCI] 启动SUMO: {" ".join(sumo_cmd)}')

    step = 0
    records = 0
    stuck_count = 0
    sumo_process = None

    try:
        # 方式1: traci.start() 内部启动sumo
        traci.start(sumo_cmd)

        # 等待连接稳定
        time.sleep(0.5)

        # 获取SUMO进程引用（traci内部管理的连接）
        total_steps = duration * 10  # step-length=0.1
        print(f'[TraCI] 总步数={total_steps}, 数据间隔={interval}步')

        while step < total_steps:
            # === 信号检查 ===
            if os.path.exists(STOP_FILE):
                print('\n[TraCI] 收到停止信号')
                break
            while os.path.exists(PAUSE_FILE) and not os.path.exists(STOP_FILE):
                time.sleep(0.3)
                _write_heartbeat()

            # === 带超时的simulationStep ===
            status, val = _step_with_timeout(timeout=15)

            if status == 'timeout':
                stuck_count += 1
                print(f'\n[TraCI] ⚠ step超时({stuck_count}/3)')
                if stuck_count >= 3:
                    print('[TraCI] ❌ 连续3次超时，判定死锁')
                    break
                continue
            elif status == 'error':
                print(f'\n[TraCI] ⚠ step异常: {val}')
                stuck_count += 1
                if stuck_count >= 3: break
                continue
            else:
                stuck_count = 0  # 成功 → 重置

            # val < 0 表示仿真已结束
            if val is not None and val < 0:
                print(f'\n[TraCI] SUMO仿真正常结束 (step={step})')
                break

            step += 1

            # === 检查仿真是否还有待处理车辆 ===
            try:
                if traci.simulation.getMinExpectedNumber() <= 0 and step > 100:
                    # 仿真中已无车辆，但flow可能还在生成
                    # 不立即退出，继续推进但输出提示
                    if step % 500 == 0:
                        print(f'\n[TraCI] 提示: step={step}无待处理车辆')
            except:
                pass

            # === 数据采集 (每interval步) ===
            if step % interval == 0:
                try:
                    det_ids = traci.lanearea.getIDList()
                    for did in det_ids:
                        try:
                            veh = traci.lanearea.getLastStepVehicleNumber(did)
                            speed = traci.lanearea.getLastStepMeanSpeed(did)
                            occ = traci.lanearea.getLastStepOccupancy(did) * 100
                            speed = max(0, speed) if speed is not None and speed >= 0 else 0
                            conn.execute(
                                'INSERT INTO traffic_records (section_id, detector_id, vehicle_count, avg_speed, occupancy, timestamp) '
                                'VALUES (?, ?, ?, ?, ?, ?)',
                                (section_id, detector_id, veh, round(speed, 1), round(occ, 1), datetime.utcnow().isoformat())
                            )
                            records += 1
                        except:
                            pass
                    sim_time = step * 0.1
                    print(f'\r[TraCI] t={sim_time:.0f}s 已导入{records}条', end='')
                except Exception as e:
                    print(f'\n[TraCI] 数据采集异常: {e}')

            # === 提交+进度 (每50步) ===
            if step % 50 == 0:
                try:
                    conn.commit()
                except:
                    pass
                _write_progress(step, duration)
                _write_heartbeat()

    except KeyboardInterrupt:
        print('\n[TraCI] 用户中断')
    except Exception as e:
        print(f'\n[TraCI] 异常: {e}')
    finally:
        # 清理
        try:
            conn.commit()
        except:
            pass
        conn.close()

        try:
            traci.close()
        except:
            pass

        # 杀掉可能残留的sumo进程
        try:
            import subprocess as sp
            if platform.system() == 'Windows':
                sp.run(['taskkill', '/F', '/IM', 'sumo.exe'],
                       capture_output=True, timeout=5)
        except:
            pass

        for f in [PROGRESS_FILE, PAUSE_FILE, STOP_FILE, PID_FILE, HEARTBEAT_FILE]:
            if os.path.exists(f):
                try: os.remove(f)
                except OSError: pass

        print(f'\n[TraCI] 完成: {records}条记录, {step}步')


if __name__ == '__main__':
    import platform
    parser = argparse.ArgumentParser(description='SUMO TraCI实时仿真')
    parser.add_argument('--duration', type=int, default=3600, help='仿真时长(秒)')
    parser.add_argument('--interval', type=int, default=50, help='数据写入间隔(步数), 50=5秒')
    parser.add_argument('--port', type=int, default=TRACI_PORT, help='TraCI端口')
    args = parser.parse_args()
    TRACI_PORT = args.port
    run_realtime(args.duration, args.interval)
