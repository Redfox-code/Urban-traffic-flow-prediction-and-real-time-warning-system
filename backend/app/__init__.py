import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from config import config_map

db = SQLAlchemy()
jwt = JWTManager()


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

    # 创建数据库表（开发环境）
    with app.app_context():
        from app.models import user, traffic_section, traffic_detector
        from app.models import traffic_record, prediction_result
        from app.models import warning_event, route_record, system_log
        db.create_all()

    return app
