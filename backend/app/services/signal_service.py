"""信号优化服务 — Agent-Lead"""
import json, sys, os

# 确保 algorithm 目录在 path 中
ALGORITHM_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'algorithm'))
if ALGORITHM_DIR not in sys.path:
    sys.path.insert(0, ALGORITHM_DIR)


def calculate_webster(intersection_data):
    """调用Webster公式计算最优信号配时。

    Args:
        intersection_data: dict {
            'phases': [{'phase_id': str, 'flow': float, 'saturation_flow': float}, ...],
            'loss_time_per_phase': float (default 5.0),
            'current_cycle': float (optional, 当前周期)
        }

    Returns:
        dict: {optimal_cycle, green_splits, efficiency_gain_pct, delay_reduction_sec}
    """
    phases = intersection_data.get('phases', [])
    L = intersection_data.get('loss_time_per_phase', 5.0) * len(phases)

    if not phases:
        return {'error': '至少需要一个相位'}

    # 计算各相位流量比 y = flow / saturation_flow
    y_values = []
    for p in phases:
        sf = p.get('saturation_flow', 1800)  # 默认饱和流量1800 vph
        if sf <= 0:
            return {'error': '饱和流量必须为正数'}
        y = min(p.get('flow', 0) / sf, 0.95)  # 最大流量比0.95
        y_values.append(y)

    Y = sum(y_values)
    if Y >= 1.0:
        return {'error': f'流量比之和({Y:.2f})>=1，交叉口过饱和，Webster公式不适用'}

    # Webster 最优周期
    C_opt = (1.5 * L + 5) / (1 - Y)
    C_opt = max(min(C_opt, 180), 30)  # 周期限制在30-180秒

    # 各相位绿灯分配
    effective_green = C_opt - L
    green_splits = []
    for i, p in enumerate(phases):
        g_i = (y_values[i] / Y) * effective_green if Y > 0 else effective_green / len(phases)
        green_splits.append({
            'phase_id': p.get('phase_id', f'phase_{i}'),
            'green_sec': round(g_i, 1),
            'flow_ratio': round(y_values[i], 3)
        })

    # 估算改善效果
    current_cycle = intersection_data.get('current_cycle', 120)
    efficiency_gain = round((1 - C_opt / current_cycle) * 100, 1) if current_cycle > 0 else 0
    delay_reduction = round(abs(current_cycle - C_opt) * 0.5, 1)  # 简化估算：每减少1秒周期=减少0.5秒延误

    return {
        'optimal_cycle': round(C_opt, 1),
        'green_splits': green_splits,
        'total_loss_time': round(L, 1),
        'flow_ratio_sum': round(Y, 3),
        'efficiency_gain_pct': efficiency_gain,
        'delay_reduction_sec': delay_reduction
    }


def get_intersection_list():
    """获取路口列表（基于现有traffic_sections的路口信息）。

    从traffic_sections表提取有信号灯的路口，估算各进口道流量，
    按优化潜力降序排列。
    """
    from app.models.traffic_section import TrafficSection
    from app.models.traffic_record import TrafficRecord
    from app import db
    from sqlalchemy import func

    sections = TrafficSection.query.all()
    if not sections:
        return []

    intersections = []
    seen_names = set()

    for s in sections:
        name = s.name or f'路段{s.id}'
        base_name = name.split('-')[0].strip() if '-' in name else name

        if base_name in seen_names:
            continue
        seen_names.add(base_name)

        # 从最近记录获取流量
        latest = TrafficRecord.query.filter_by(
            section_id=s.id
        ).order_by(TrafficRecord.timestamp.desc()).first()

        current_flow = latest.vehicle_count if latest else 100
        capacity = s.capacity or 2000

        intersections.append({
            'intersection_id': str(s.id),
            'intersection_name': base_name,
            'current_cycle': 120,  # 假设当前固定配时120秒
            'estimated_flow': current_flow,
            'capacity': capacity,
            'optimization_potential_pct': round(min((current_flow / capacity) * 50, 80), 1)
        })

    # 按优化潜力降序
    intersections.sort(key=lambda x: x['optimization_potential_pct'], reverse=True)
    return intersections
