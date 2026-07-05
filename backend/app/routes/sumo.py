"""SUMO仿真控制 — /api/v1/sumo/* — Agent-Lead"""
import subprocess, os, sys
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required

sumo_bp = Blueprint('sumo', __name__)
ALGORITHM_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'algorithm'))
STOP_FILE = os.path.join(ALGORITHM_DIR, '.stop_realtime')
PROGRESS_FILE = os.path.join(ALGORITHM_DIR, '.sim_progress')

_realtime_process = None
_batch_process = None


@sumo_bp.route('/run_realtime', methods=['POST'])
@jwt_required()
def run_realtime():
    global _realtime_process
    if _realtime_process and _realtime_process.poll() is None:
        return jsonify({'code': 200, 'data': {'status': 'already_running'}, 'message': '实时仿真已在运行中'})
    try:
        _realtime_process = subprocess.Popen(
            [sys.executable, 'run_simulation_realtime.py', '--duration', '3600', '--interval', '100'],
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


@sumo_bp.route('/status', methods=['GET'])
@jwt_required()
def realtime_status():
    global _realtime_process, _batch_process
    rt_running = _realtime_process and _realtime_process.poll() is None
    batch_running = _batch_process and _batch_process.poll() is None
    progress = 0
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE) as f: progress = int(f.read().strip() or 0)
        except: pass
    return jsonify({'code': 200, 'data': {
        'realtime_running': rt_running,
        'batch_running': batch_running,
        'progress': progress
    }, 'message': 'ok'})


@sumo_bp.route('/run', methods=['POST'])
@jwt_required()
def run_simulation():
    global _batch_process
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
        global _batch_process; _batch_process = None
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
