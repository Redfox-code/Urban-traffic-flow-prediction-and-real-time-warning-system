import os, sys, subprocess, threading
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from config import config_map

db = SQLAlchemy()
jwt = JWTManager()

_sync_process = None


def _start_amap_sync():
    """后台启动高德数据同步（Flask启动时自动运行）"""
    global _sync_process
    # 先杀掉旧进程，避免多个sync同时写DB
    if _sync_process and _sync_process.poll() is None:
        print('[AmapSync] 终止旧同步进程...')
        _sync_process.terminate()
        try: _sync_process.wait(timeout=3)
        except: _sync_process.kill()
    sync_script = os.path.join(os.path.dirname(__file__), '..', '..', 'algorithm', 'sync_amap_traffic.py')
    if not os.path.exists(sync_script):
        print('[AmapSync] 同步脚本未找到，跳过')
        return
    try:
        _sync_process = subprocess.Popen(
            [sys.executable, sync_script, '--continuous', '--interval', '120'],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )
        print(f'[AmapSync] 后台同步已启动 (PID={_sync_process.pid})')
    except Exception as e:
        print(f'[AmapSync] 启动失败: {e}')


def create_app(config_name=None):
    """Flask应用工厂函数"""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config_map[config_name])

    # 初始化扩展
    db.init_app(app)
    jwt.init_app(app)
    CORS(app)

    # 演示模式：不自动启动同步，由前端"启动实时仿真"按钮触发回放
    # 如需恢复自动同步，取消下面注释：
    # if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
    #     sync_thread = threading.Thread(target=_start_amap_sync, daemon=True)
    #     sync_thread.start()

    # 注册蓝图（Agent-Lead 负责的 5 个 Blueprint）
    from app.routes.auth import auth_bp
    from app.routes.sections import sections_bp
    from app.routes.warning import warning_bp
    from app.routes.route_plan import route_bp
    from app.routes.stats import stats_bp
    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')
    app.register_blueprint(sections_bp, url_prefix='/api/v1/sections')
    app.register_blueprint(warning_bp, url_prefix='/api/v1/warning')
    app.register_blueprint(route_bp, url_prefix='/api/v1/route')
    app.register_blueprint(stats_bp, url_prefix='/api/v1/stats')

    # 注册蓝图（Agent-Algorithm 负责的 2 个 Blueprint）
    from app.routes.traffic import traffic_bp
    from app.routes.prediction import prediction_bp
    app.register_blueprint(traffic_bp, url_prefix='/api/v1/traffic')
    app.register_blueprint(prediction_bp, url_prefix='/api/v1/predict')

    # 注册 SUMO 仿真控制 Blueprint
    from app.routes.sumo import sumo_bp
    app.register_blueprint(sumo_bp, url_prefix='/api/v1/sumo')

    # 注册仿真管理 Blueprint
    from app.routes.simulation_routes import sim_bp
    app.register_blueprint(sim_bp, url_prefix='/api/v1/simulation')

    # 注册三用户角色平台新增 Blueprint（Agent-Lead）
    from app.routes.signal import signal_bp
    from app.routes.carbon import carbon_bp
    from app.routes.traveler import traveler_bp
    app.register_blueprint(signal_bp, url_prefix='/api/v1/signal')
    app.register_blueprint(carbon_bp, url_prefix='/api/v1/carbon')
    app.register_blueprint(traveler_bp, url_prefix='/api/v1/traveler')

    # 创建数据库表（开发环境）
    with app.app_context():
        from app.models import user, traffic_section, traffic_detector
        from app.models import traffic_record, prediction_result
        from app.models import warning_event, route_record, system_log
        from app.models import simulation
        # 三用户角色平台新增模型
        from app.models import congestion_propagation, user_travel_profile, user_alert_history
        from app.models import signal_optimization, emergency_route, scenario_simulation, carbon_emission
        db.create_all()

    # 生产环境：serve 前端静态文件 + SPA fallback
    from flask import send_from_directory
    frontend_dist = os.path.join(os.path.dirname(__file__), '..', '..', 'frontend', 'dist')

    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_frontend(path):
        if path and os.path.exists(os.path.join(frontend_dist, path)):
            return send_from_directory(frontend_dist, path)
        return send_from_directory(frontend_dist, 'index.html')

    return app
