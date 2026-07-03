"""仿真管理 — /api/v1/simulation/* — Agent-Lead"""
import os, sys, subprocess, sqlite3, xml.etree.ElementTree as ET
from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app import db
from app.models.simulation import Simulation

sim_bp = Blueprint('simulation', __name__)

ALGORITHM_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'algorithm'))
DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'instance', 'dev.db')
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'algorithm', 'uploads')


@sim_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload():
    """提交仿真文件"""
    sim_type = request.form.get('type', 'batch')
    name = request.form.get('name', f'仿真提交_{datetime.utcnow().strftime("%m%d_%H%M")}')

    sim = Simulation(name=name, sim_type=sim_type, status='uploaded')

    if 'file' in request.files:
        file = request.files['file']
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        fname = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
        fpath = os.path.join(UPLOAD_DIR, fname)
        file.save(fpath)
        sim.file_path = fpath
        # 小文件直接存内容
        content = file.read().decode('utf-8', errors='ignore')
        file.seek(0)
        if len(content) < 100000:
            sim.file_content = content
    elif 'content' in request.form:
        sim.file_content = request.form['content']

    db.session.add(sim)
    db.session.commit()
    return jsonify({'code': 201, 'data': {'id': sim.id, 'name': sim.name}, 'message': '提交成功'}), 201


@sim_bp.route('/list', methods=['GET'])
@jwt_required()
def list_simulations():
    """仿真提交历史"""
    sim_type = request.args.get('type', '')
    query = Simulation.query
    if sim_type:
        query = query.filter_by(sim_type=sim_type)
    items = query.order_by(Simulation.created_at.desc()).limit(50).all()
    return jsonify({'code': 200, 'data': {'items': [
        {'id': s.id, 'name': s.name, 'type': s.sim_type, 'status': s.status,
         'records': s.records_imported, 'created_at': s.created_at.isoformat()}
        for s in items
    ]}, 'message': 'ok'})


@sim_bp.route('/<int:sim_id>/load', methods=['POST'])
@jwt_required()
def load_simulation(sim_id):
    """读取已提交的仿真文件并导入数据库"""
    sim = db.session.get(Simulation, sim_id)
    if not sim:
        return jsonify({'code': 404, 'message': '仿真记录不存在'}), 404
    if not sim.file_path or not os.path.exists(sim.file_path):
        return jsonify({'code': 400, 'message': '文件不存在，请重新上传'}), 400

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute('PRAGMA journal_mode=WAL')
        cur = conn.execute('SELECT id, section_id FROM traffic_detectors LIMIT 1')
        det = cur.fetchone()
        if not det:
            conn.close()
            return jsonify({'code': 400, 'message': '无检测器数据，请先运行seed_data'}), 400
        detector_id, section_id = det[0], det[1]

        tree = ET.parse(sim.file_path)
        count = 0
        for interval in tree.iter('interval'):
            veh = int(float(interval.get('nVehEntered', 0)))
            speed = float(interval.get('meanSpeed', -1))
            occ = float(interval.get('meanOccupancy', 0))
            if veh == 0 and speed == -1: veh, speed = 0, 0.0
            conn.execute(
                'INSERT INTO traffic_records (section_id, detector_id, vehicle_count, avg_speed, occupancy, timestamp) VALUES (?,?,?,?,?,?)',
                (section_id, detector_id, veh, round(speed, 2), round(occ, 2), datetime.utcnow().isoformat())
            )
            count += 1

        conn.commit(); conn.close()
        sim.status = 'completed'
        sim.records_imported = count
        db.session.commit()

        return jsonify({'code': 200, 'data': {'records_imported': count, 'status': 'completed'}, 'message': 'ok'})
    except Exception as e:
        sim.status = 'failed'; sim.error_log = str(e); db.session.commit()
        return jsonify({'code': 500, 'message': str(e)}), 500


@sim_bp.route('/<int:sim_id>', methods=['DELETE'])
@jwt_required()
def delete_simulation(sim_id):
    sim = db.session.get(Simulation, sim_id)
    if not sim: return jsonify({'code': 404}), 404
    db.session.delete(sim); db.session.commit()
    return jsonify({'code': 200, 'message': '已删除'})
