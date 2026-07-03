"""SUMO仿真控制 — /api/v1/sumo/* — Agent-Lead"""
import subprocess
import os
import sys
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required

sumo_bp = Blueprint('sumo', __name__)

# 实时仿真进程状态（简单全局变量）
_realtime_process = None
STOP_FILE = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'algorithm', '.stop_realtime')


@sumo_bp.route('/run_realtime', methods=['POST'])
@jwt_required()
def run_realtime():
    """启动实时仿真（后台进程，数据持续写入DB）"""
    global _realtime_process
    if _realtime_process and _realtime_process.poll() is None:
        return jsonify({'code': 200, 'data': {'status': 'already_running'}, 'message': '实时仿真已在运行中'})

    import subprocess as sp
    try:
        _realtime_process = sp.Popen(
            [sys.executable, 'run_simulation_realtime.py', '--duration', '3600', '--interval', '100'],
            cwd=ALGORITHM_DIR, stdout=sp.PIPE, stderr=sp.PIPE, text=True
        )
        return jsonify({'code': 200, 'data': {'status': 'started'}, 'message': '实时仿真已启动'})
    except Exception as e:
        return jsonify({'code': 500, 'data': None, 'message': str(e)}), 500


@sumo_bp.route('/stop', methods=['POST'])
@jwt_required()
def stop_realtime():
    """停止实时仿真"""
    global _realtime_process
    # 创建stop文件（run_simulation_realtime.py会检测）
    with open(STOP_FILE, 'w') as f:
        f.write('stop')
    if _realtime_process and _realtime_process.poll() is None:
        _realtime_process.terminate()
        _realtime_process = None
    return jsonify({'code': 200, 'data': {'status': 'stopped'}, 'message': '仿真已停止'})


@sumo_bp.route('/status', methods=['GET'])
@jwt_required()
def realtime_status():
    """查询实时仿真状态"""
    global _realtime_process
    running = _realtime_process and _realtime_process.poll() is None
    return jsonify({'code': 200, 'data': {'running': running}, 'message': 'ok'})

ALGORITHM_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'algorithm'))


@sumo_bp.route('/run', methods=['POST'])
@jwt_required()
def run_simulation():
    """一键运行SUMO仿真+导入数据库"""
    results = {}

    try:
        # Step 1: 生成路网（快速）
        gen = subprocess.run(
            [sys.executable, 'run_simulation.py', 'generate'],
            cwd=ALGORITHM_DIR, capture_output=True, text=True, timeout=60
        )
        results['generate'] = {'ok': gen.returncode == 0, 'output': gen.stdout[-200:]}
        if gen.returncode != 0:
            return jsonify({'code': 500, 'data': results,
                            'message': f'路网生成失败: {gen.stderr[-200:]}'}), 500

        # Step 2: 运行仿真（1小时仿真，约30-60秒）
        sim = subprocess.run(
            [sys.executable, 'run_simulation.py', 'run'],
            cwd=ALGORITHM_DIR, capture_output=True, text=True, timeout=120
        )
        results['simulation'] = {'ok': sim.returncode == 0, 'lines': len(sim.stdout.split(chr(10)))}
        if sim.returncode != 0:
            return jsonify({'code': 500, 'data': results,
                            'message': f'仿真运行失败: {sim.stderr[-200:] or sim.stdout[-200:]}'}), 500

        # Step 3: 导入数据库
        imp = subprocess.run(
            [sys.executable, 'import_sumo_data.py'],
            cwd=ALGORITHM_DIR, capture_output=True, text=True, timeout=30
        )
        results['import'] = {'ok': imp.returncode == 0, 'output': imp.stdout[:300]}
        if imp.returncode != 0:
            return jsonify({'code': 500, 'data': results,
                            'message': f'导入失败: {imp.stderr[-200:]}'}), 500

        count = 0
        for line in imp.stdout.split('\n'):
            if '成功导入' in line:
                count = int(line.split('成功导入')[1].split('条')[0].strip() or 0)

        return jsonify({'code': 200, 'data': {
            'records_imported': count, 'status': '仿真完成', 'steps': results
        }, 'message': 'ok'})

    except subprocess.TimeoutExpired as e:
        return jsonify({'code': 500, 'data': results,
                        'message': f'步骤超时({e.timeout}s)，请检查SUMO是否正常运行'}), 500
    except Exception as e:
        return jsonify({'code': 500, 'data': results, 'message': str(e)}), 500
