"""SUMO仿真控制 — /api/v1/sumo/* — Agent-Lead"""
import subprocess, os, sys, platform, signal, time
from datetime import datetime
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required

sumo_bp = Blueprint('sumo', __name__)
ALGORITHM_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'algorithm'))
STOP_FILE = os.path.join(ALGORITHM_DIR, '.stop_realtime')
PAUSE_FILE = os.path.join(ALGORITHM_DIR, '.pause_realtime')
PROGRESS_FILE = os.path.join(ALGORITHM_DIR, '.sim_progress')
PID_FILE = os.path.join(ALGORITHM_DIR, '.sim_pid')
HEARTBEAT_FILE = os.path.join(ALGORITHM_DIR, '.sim_heartbeat')

_realtime_process = None
_batch_process = None


def _cleanup_orphans():
    """Flask重启后清理残留的孤儿进程和失效控制文件。

    场景：Flask重启 -> 旧的sumo.exe/subprocess.py变成孤儿进程
    -> .sim_progress保留旧值 -> 前端进度条卡住 -> 新启动无法正常运行。

    策略：
    1. 通过PID文件检测旧进程 -> 优雅终止 -> 强制杀掉
    2. 清理全部4个信号文件（STOP/PAUSE/PROGRESS/PID）
    3. 额外兜底：查找并杀掉残留的sumo.exe
    """
    # 1. 通过PID文件检测并杀掉孤儿进程（先于文件清理，保证finally有机会执行）
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE) as f:
                old_pid = int(f.read().strip())
            print(f'[Cleanup] 发现PID文件，旧PID={old_pid}，检查是否存活...')

            if _is_process_alive(old_pid):
                _kill_process_tree(old_pid)
                print(f'[Cleanup] 已杀掉孤儿进程树 (PID={old_pid})')
        except (ValueError, OSError, subprocess.TimeoutExpired) as e:
            print(f'[Cleanup] 处理PID文件异常: {e}')

    # 2. 清理全部5个信号文件（无论进程是否存在、是否被杀都清理）
    for f in [STOP_FILE, PAUSE_FILE, PROGRESS_FILE, PID_FILE, HEARTBEAT_FILE]:
        if os.path.exists(f):
            try:
                os.remove(f)
                print(f'[Cleanup] 已清理残留文件: {f}')
            except OSError as e:
                print(f'[Cleanup] 清理残留文件失败 {f}: {e}')

    # 3. 额外兜底：查找并杀掉残留的sumo.exe（非Flask启动的孤儿）
    if platform.system() == 'Windows':
        try:
            result = subprocess.run(
                ['tasklist', '/FI', 'IMAGENAME eq sumo.exe'],
                capture_output=True, text=True, timeout=5
            )
            if 'sumo.exe' in result.stdout:
                subprocess.run(
                    ['taskkill', '/F', '/IM', 'sumo.exe'],
                    capture_output=True, timeout=5
                )
                print('[Cleanup] 已杀掉残留的sumo.exe孤儿进程')
        except subprocess.TimeoutExpired:
            print('[Cleanup] tasklist/taskkill超时（跳过）')


def _is_process_alive(pid):
    """检查PID对应的进程是否存在。"""
    if platform.system() == 'Windows':
        result = subprocess.run(
            ['tasklist', '/FI', f'PID eq {pid}'],
            capture_output=True, text=True, timeout=5
        )
        return str(pid) in result.stdout
    else:
        try:
            os.kill(pid, 0)
            return True
        except (OSError, ProcessLookupError):
            return False


def _kill_process_tree(pid):
    """杀掉进程树：先优雅终止（SIGTERM/terminate），等2秒，再强制杀（SIGKILL/taskkill /F）。

    优雅终止优先让子进程的finally块有机会执行（清理信号文件），
    无法在2秒内退出的进程再用taskkill /F兜底。
    """
    if platform.system() == 'Windows':
        # 第一步：优雅终止（不带/F）
        subprocess.run(
            ['taskkill', '/T', '/PID', str(pid)],
            capture_output=True, timeout=5
        )
        print(f'[Cleanup] 已发送终止信号给PID={pid}，等待2秒...')
        time.sleep(2)
        # 第二步：检查是否还在运行，强制杀
        if _is_process_alive(pid):
            subprocess.run(
                ['taskkill', '/F', '/T', '/PID', str(pid)],
                capture_output=True, timeout=5
            )
            print(f'[Cleanup] 已强制杀掉PID={pid}')
    else:
        try:
            os.kill(pid, signal.SIGTERM)
            print(f'[Cleanup] 已发送SIGTERM给PID={pid}，等待2秒...')
            time.sleep(2)
            # 第二步：强制杀
            try:
                os.kill(pid, signal.SIGKILL)
                print(f'[Cleanup] 已强制杀掉PID={pid}')
            except ProcessLookupError:
                pass  # 进程已优雅退出，正常
        except ProcessLookupError:
            pass  # 进程已不存在


@sumo_bp.route('/run_realtime', methods=['POST'])
@jwt_required()
def run_realtime():
    global _realtime_process
    if _realtime_process and _realtime_process.poll() is None:
        return jsonify({'code': 200, 'data': {'status': 'already_running'}, 'message': '实时仿真已在运行中'})
    # 启动前先清理孤儿进程+残留文件
    _cleanup_orphans()
    # 重置进度
    with open(PROGRESS_FILE, 'w') as f: f.write('0')
    try:
        _realtime_process = subprocess.Popen(
            [sys.executable, 'run_simulation_realtime.py', '--duration', '3600', '--interval', '50'],
            cwd=ALGORITHM_DIR, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return jsonify({'code': 200, 'data': {'status': 'started'}, 'message': '实时仿真已启动'})
    except Exception as e:
        return jsonify({'code': 500, 'data': None, 'message': str(e)}), 500


@sumo_bp.route('/stop', methods=['POST'])
@jwt_required()
def stop_realtime():
    global _realtime_process, _batch_process
    # 停止实时仿真
    with open(STOP_FILE, 'w') as f: f.write('stop')
    if _realtime_process and _realtime_process.poll() is None:
        _realtime_process.terminate(); _realtime_process = None
    # 停止离线仿真
    if _batch_process and _batch_process.poll() is None:
        _batch_process.terminate(); _batch_process = None
    return jsonify({'code': 200, 'data': {'status': 'stopped'}, 'message': '已停止'})


@sumo_bp.route('/pause', methods=['POST'])
@jwt_required()
def pause_realtime():
    with open(PAUSE_FILE, 'w') as f: f.write('pause')
    return jsonify({'code': 200, 'data': {'status': 'paused'}, 'message': '已暂停'})


@sumo_bp.route('/resume', methods=['POST'])
@jwt_required()
def resume_realtime():
    if os.path.exists(PAUSE_FILE): os.remove(PAUSE_FILE)
    return jsonify({'code': 200, 'data': {'status': 'resumed'}, 'message': '已继续'})


@sumo_bp.route('/status', methods=['GET'])
@jwt_required()
def realtime_status():
    global _realtime_process, _batch_process
    rt_running = _realtime_process and _realtime_process.poll() is None
    batch_running = _batch_process and _batch_process.poll() is None
    progress = 0
    heartbeat_stale = False

    if rt_running:
        if os.path.exists(PROGRESS_FILE):
            try:
                with open(PROGRESS_FILE) as f: progress = int(f.read().strip() or 0)
            except: pass

        # 心跳检测：如果进程在运行但心跳>60秒未更新，判定为卡死
        if os.path.exists(HEARTBEAT_FILE):
            try:
                with open(HEARTBEAT_FILE) as f:
                    last_hb = f.read().strip()
                if last_hb:
                    hb_time = datetime.fromisoformat(last_hb)
                    heartbeat_stale = (datetime.utcnow() - hb_time).total_seconds() > 60
            except: pass

    return jsonify({'code': 200, 'data': {
        'realtime_running': rt_running,
        'batch_running': batch_running,
        'progress': progress,
        'heartbeat_stale': heartbeat_stale  # True=仿真卡死
    }, 'message': 'ok'})


@sumo_bp.route('/run', methods=['POST'])
@jwt_required()
def run_simulation():
    global _batch_process
    # 启动前先清理孤儿进程+残留文件
    _cleanup_orphans()
    _batch_process = None
    try:
        _batch_process = subprocess.Popen(
            [sys.executable, 'run_simulation.py', 'all'],
            cwd=ALGORITHM_DIR, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = _batch_process.communicate(timeout=120)
        rc = _batch_process.returncode; _batch_process = None
        if rc != 0:
            return jsonify({'code': 500, 'data': {'stdout': stdout[-300:], 'stderr': stderr[-300:]},
                            'message': f'仿真失败: {stderr[-200:] or stdout[-200:]}'}), 500

        imp = subprocess.run([sys.executable, 'import_sumo_data.py'], cwd=ALGORITHM_DIR,
                             capture_output=True, text=True, timeout=30)
        out = imp.stdout + imp.stderr
        if imp.returncode != 0:
            return jsonify({'code': 500, 'data': {'stdout': imp.stdout[-300:], 'stderr': imp.stderr[-300:]},
                            'message': f'导入失败: {out[-300:]}'}), 500

        count = 0
        for line in imp.stdout.split('\n'):
            if '成功导入' in line:
                count = int(line.split('成功导入')[1].split('条')[0].strip() or 0)
        return jsonify({'code': 200, 'data': {'records_imported': count, 'status': '完成'}, 'message': 'ok'})
    except subprocess.TimeoutExpired:
        _batch_process = None
        return jsonify({'code': 500, 'message': '仿真超时(120秒)'}), 500
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e)}), 500


@sumo_bp.route('/batch/stop', methods=['POST'])
@jwt_required()
def stop_batch():
    global _batch_process
    if _batch_process and _batch_process.poll() is None:
        _batch_process.terminate(); _batch_process = None
    return jsonify({'code': 200, 'data': {'status': 'stopped'}, 'message': '离线仿真已停止'})


# 模块加载时自动清理（Flask重启时杀掉孤儿进程）
_cleanup_orphans()
