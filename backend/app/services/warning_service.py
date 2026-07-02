"""预警规则引擎 — Agent-Lead"""
from app.models.warning_event import WarningEvent
from app import db


def check_warning(section_id, occupancy, vehicle_count):
    """检查是否触发预警，返回(level, message)或None"""
    thresholds = {'warning_threshold': 85, 'critical_threshold': 95}
    if occupancy >= thresholds['critical_threshold']:
        return 'CRITICAL', f'严重拥堵：占有率{occupancy}%超过{thresholds["critical_threshold"]}%阈值'
    elif occupancy >= thresholds['warning_threshold']:
        return 'WARNING', f'拥堵预警：占有率{occupancy}%超过{thresholds["warning_threshold"]}%阈值'
    return None
