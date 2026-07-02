"""WebSocket — Flask-SocketIO 实例 — Agent-Lead 负责基础设施，Agent-Frontend-Map 负责事件定义"""
from flask_socketio import SocketIO

socketio = SocketIO(cors_allowed_origins='*')
