"""SUMO仿真控制 — /api/v1/sumo/* — Agent-Lead"""
import subprocess
import os
import sys
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required

sumo_bp = Blueprint('sumo', __name__)

ALGORITHM_DIR = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'algorithm')


@sumo_bp.route('/run', methods=['POST'])
@jwt_required()
def run_simulation():
    """一键运行SUMO仿真+导入数据库"""
    try:
        # Step 1: 生成路网+检测器+车流
        gen = subprocess.run(
            [sys.executable, 'run_simulation.py', 'generate'],
            cwd=ALGORITHM_DIR, capture_output=True, text=True, timeout=30
        )
        if gen.returncode != 0:
            return jsonify({'code': 500, 'data': {'step': 'generate', 'stderr': gen.stderr[-500:]},
                            'message': '路网生成失败'}), 500

        # Step 2: 运行仿真
        sim = subprocess.run(
            [sys.executable, 'run_simulation.py', 'run'],
            cwd=ALGORITHM_DIR, capture_output=True, text=True, timeout=120
        )
        if sim.returncode != 0:
            return jsonify({'code': 500, 'data': {'step': 'run', 'stderr': sim.stderr[-500:]},
                            'message': '仿真运行失败'}), 500

        # Step 3: 导入数据库
        imp = subprocess.run(
            [sys.executable, 'import_sumo_data.py'],
            cwd=ALGORITHM_DIR, capture_output=True, text=True, timeout=30
        )
        if imp.returncode != 0:
            return jsonify({'code': 500, 'data': {'step': 'import', 'stderr': imp.stderr[-500:]},
                            'message': '数据导入失败'}), 500

        # 提取导入记录数
        count = 0
        for line in imp.stdout.split('\n'):
            if '成功导入' in line:
                count = int(line.split('成功导入')[1].split('条')[0].strip() or 0)

        return jsonify({'code': 200, 'data': {
            'records_imported': count,
            'status': '仿真完成，数据已导入数据库'
        }, 'message': 'ok'})

    except subprocess.TimeoutExpired as e:
        return jsonify({'code': 500, 'data': {'step': 'timeout'},
                        'message': f'仿真超时: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'code': 500, 'data': None, 'message': f'仿真异常: {str(e)}'}), 500
