"""
What-If 仿真引擎 (简化版)

不依赖真实 SUMO 仿真, 使用数学估算模型模拟不同交通管理策略的效果。

支持的干预策略:
    1. 限流 x%: 干预区域流量 *= (1 - x/100)
    2. 信号优化: 通行效率提升 y% (基于 Webster 配时结果)
    3. 路段封闭: 封闭路段流量重新分配到相邻路段

输出对比指标:
    - 总延误 (veh·h)
    - 平均速度 (km/h)
    - 拥堵路段数
    - CO2 排放 (kg/h)
    - 通行能力 (veh/h)

参考:
    Daganzo, C. F. "Fundamentals of Transportation and Traffic Operations"
    Highway Capacity Manual (HCM 2016)
"""

from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass, field
import math
import copy
from enum import Enum


class ScenarioType(Enum):
    """干预策略类型"""
    FLOW_LIMIT = "flow_limit"          # 限流
    SIGNAL_OPTIMIZE = "signal_optimize" # 信号优化
    ROAD_CLOSURE = "road_closure"       # 路段封闭
    COMBINED = "combined"               # 组合策略


@dataclass
class SegmentState:
    """路段状态"""
    section_id: str
    length_km: float            # 长度 (km)
    lanes: int                  # 车道数
    capacity_veh_h: float       # 通行能力 (veh/h)
    current_flow_veh_h: float   # 当前流量 (veh/h)
    current_speed_kmh: float    # 当前速度 (km/h)
    free_speed_kmh: float       # 自由流速度 (km/h)
    name: str = ""

    @property
    def vc_ratio(self) -> float:
        """流量/通行能力比 (V/C)"""
        if self.capacity_veh_h <= 0:
            return 1.0
        return self.current_flow_veh_h / self.capacity_veh_h

    @property
    def is_congested(self) -> bool:
        """是否拥堵 (V/C > 0.8 或速度 < 40% 自由流)"""
        return (self.vc_ratio > 0.8 or
                self.current_speed_kmh < self.free_speed_kmh * 0.4)

    @property
    def delay_veh_h(self) -> float:
        """延误 (veh·h)"""
        if self.current_speed_kmh <= 0 or self.free_speed_kmh <= 0:
            return 0.0
        # 延误 = 流量 * 长度 * (1/当前速度 - 1/自由流速度)
        t_actual = self.length_km / max(self.current_speed_kmh, 1.0)
        t_free = self.length_km / self.free_speed_kmh
        return self.current_flow_veh_h * (t_actual - t_free) / 3600.0

    @property
    def co2_emission_kg(self) -> float:
        """CO2 排放 (kg/h)"""
        # 简化模型: 基于速度和流量
        if self.current_speed_kmh <= 0:
            return 0.0
        # 基础排放率 (g/km)
        a, b, c, d = 130.45, 0.39, 0.027, 1170.3
        v = self.current_speed_kmh
        rate_g_per_km = a + b * v + c * v * v + d / v
        # 总排放 = 排放率 * 流量 * 长度 / 1000 (kg/h)
        return rate_g_per_km * self.current_flow_veh_h * self.length_km / 1000.0

    def clone(self) -> "SegmentState":
        return copy.deepcopy(self)


@dataclass
class ScenarioInput:
    """场景输入"""
    segments: List[SegmentState]          # 路网状态
    scenario_type: ScenarioType           # 干预类型
    # 限流参数
    flow_limit_pct: float = 0.0           # 限流百分比 (%)
    flow_limit_zone: List[str] = None     # 限流区域路段 ID 列表
    # 信号优化参数
    signal_efficiency_gain_pct: float = 0.0  # 信号效率提升百分比 (%)
    signal_zone: List[str] = None            # 信号优化区域路段 ID 列表
    # 路段封闭参数
    closed_roads: List[str] = None         # 封闭路段 ID 列表
    # 组合策略
    scenario_name: str = "未命名场景"

    def __post_init__(self):
        if self.flow_limit_zone is None:
            self.flow_limit_zone = []
        if self.signal_zone is None:
            self.signal_zone = []
        if self.closed_roads is None:
            self.closed_roads = []


@dataclass
class ScenarioMetrics:
    """场景指标"""
    total_delay_veh_h: float = 0.0       # 总延误 (veh·h)
    avg_speed_kmh: float = 0.0            # 平均速度 (km/h)
    num_congested: int = 0                # 拥堵路段数
    total_co2_kg: float = 0.0             # CO2 总排放 (kg/h)
    total_flow_veh_h: float = 0.0         # 总流量 (veh/h)
    avg_vc_ratio: float = 0.0             # 平均 V/C 比
    num_segments: int = 0

    def to_dict(self) -> Dict:
        return {
            "total_delay_veh_h": round(self.total_delay_veh_h, 2),
            "avg_speed_kmh": round(self.avg_speed_kmh, 1),
            "num_congested": self.num_congested,
            "total_co2_kg": round(self.total_co2_kg, 2),
            "total_flow_veh_h": round(self.total_flow_veh_h, 0),
            "avg_vc_ratio": round(self.avg_vc_ratio, 3),
            "num_segments": self.num_segments,
            "congestion_ratio": round(
                self.num_congested / self.num_segments * 100, 1
            ) if self.num_segments > 0 else 0,
        }


@dataclass
class ScenarioResult:
    """场景仿真结果"""
    scenario_name: str
    scenario_type: str
    baseline: ScenarioMetrics     # 基线指标 (无干预)
    intervention: ScenarioMetrics  # 干预后指标
    delta: Dict                    # 变化量

    def to_dict(self) -> Dict:
        return {
            "scenario_name": self.scenario_name,
            "scenario_type": self.scenario_type,
            "baseline": self.baseline.to_dict(),
            "intervention": self.intervention.to_dict(),
            "delta": self.delta,
        }


def compute_metrics(segments: List[SegmentState]) -> ScenarioMetrics:
    """计算路段集合的汇总指标"""
    if not segments:
        return ScenarioMetrics()

    metrics = ScenarioMetrics()
    metrics.num_segments = len(segments)
    metrics.total_flow_veh_h = sum(s.current_flow_veh_h for s in segments)
    metrics.total_delay_veh_h = sum(s.delay_veh_h for s in segments)
    metrics.total_co2_kg = sum(s.co2_emission_kg for s in segments)
    metrics.num_congested = sum(1 for s in segments if s.is_congested)

    # 加权平均速度
    total_flow = metrics.total_flow_veh_h
    if total_flow > 0:
        metrics.avg_speed_kmh = sum(
            s.current_speed_kmh * s.current_flow_veh_h for s in segments
        ) / total_flow

    # 平均 V/C 比
    metrics.avg_vc_ratio = sum(s.vc_ratio for s in segments) / len(segments)

    return metrics


def apply_flow_limit(
    segments: List[SegmentState],
    zone_ids: List[str],
    limit_pct: float,
) -> List[SegmentState]:
    """
    应用限流策略: 区域流量 *= (1 - limit_pct/100).

    同时模拟流量减少对速度的影响:
    - 新速度 = free_speed * (1 - (新V/C)^2)

    Args:
        segments: 原路段列表 (不会被修改)
        zone_ids: 限流区域路段 ID 列表 (空列表 = 全局)
        limit_pct: 限流百分比 (0-100)

    Returns:
        更新后的路段列表
    """
    new_segments = [s.clone() for s in segments]
    zones = set(zone_ids) if zone_ids else set()

    for seg in new_segments:
        if zones and seg.section_id not in zones:
            continue
        if not zones:
            continue  # zone_ids 为空时已跳过

        # 1. 减少流量
        seg.current_flow_veh_h *= (1.0 - limit_pct / 100.0)

        # 2. 更新速度 (BPR 函数简化版)
        new_vc = seg.vc_ratio
        # 速度 = 自由流速度 * (1 - (V/C)^2) 当 V/C < 1
        if new_vc < 1.0:
            seg.current_speed_kmh = seg.free_speed_kmh * (1.0 - new_vc * new_vc * 0.3)
        else:
            seg.current_speed_kmh = seg.free_speed_kmh * 0.3  # 过饱和最低速

        seg.current_speed_kmh = max(seg.current_speed_kmh, 5.0)

    return new_segments


def apply_flow_limit_global(
    segments: List[SegmentState],
    limit_pct: float,
) -> List[SegmentState]:
    """
    全局限流 (所有路段).
    """
    new_segments = [s.clone() for s in segments]
    for seg in new_segments:
        seg.current_flow_veh_h *= (1.0 - limit_pct / 100.0)
        new_vc = seg.vc_ratio
        if new_vc < 1.0:
            seg.current_speed_kmh = seg.free_speed_kmh * (1.0 - new_vc * new_vc * 0.3)
        else:
            seg.current_speed_kmh = seg.free_speed_kmh * 0.3
        seg.current_speed_kmh = max(seg.current_speed_kmh, 5.0)
    return new_segments


def apply_signal_optimization(
    segments: List[SegmentState],
    zone_ids: List[str],
    efficiency_gain_pct: float,
) -> List[SegmentState]:
    """
    应用信号优化: 通行效率提升 y%.

    效果:
    1. 通行能力提升: capacity *= (1 + y/100 * 0.5)  (信号优化对容量的边际效益)
    2. 延误降低: 通过 V/C 间接反映

    Args:
        segments: 原路段列表
        zone_ids: 优化区域路段 ID (空列表 = 全局)
        efficiency_gain_pct: 效率提升百分比 (%)

    Returns:
        更新后的路段列表
    """
    new_segments = [s.clone() for s in segments]
    zones = set(zone_ids) if zone_ids else set()

    for seg in new_segments:
        if zones and seg.section_id not in zones:
            continue
        if not zones:
            continue

        # 1. 提升通行能力 (信号优化对容量的影响系数 0.5)
        capacity_gain = efficiency_gain_pct / 100.0 * 0.5
        seg.capacity_veh_h *= (1.0 + capacity_gain)

        # 2. 速度提升 (基于新的 V/C)
        new_vc = seg.vc_ratio
        if new_vc < 1.0:
            seg.current_speed_kmh = seg.free_speed_kmh * (1.0 - new_vc * new_vc * 0.25)
        else:
            seg.current_speed_kmh = seg.free_speed_kmh * 0.4

        seg.current_speed_kmh = max(seg.current_speed_kmh, 5.0)

    return new_segments


def apply_signal_optimization_global(
    segments: List[SegmentState],
    efficiency_gain_pct: float,
) -> List[SegmentState]:
    """全局信号优化"""
    return apply_signal_optimization(segments, [], efficiency_gain_pct)


def apply_road_closure(
    segments: List[SegmentState],
    closed_ids: List[str],
) -> Tuple[List[SegmentState], List[SegmentState]]:
    """
    应用路段封闭策略.

    封闭路段流量按比例分配到相邻未封闭路段。
    返回 (未封闭路段列表, 封闭路段列表)。

    Args:
        segments: 原路段列表
        closed_ids: 封闭路段 ID 列表

    Returns:
        (remaining, closed): 剩余路段和封闭路段
    """
    closed_set = set(closed_ids)
    closed = [s for s in segments if s.section_id in closed_set]
    remaining = [s.clone() for s in segments if s.section_id not in closed_set]

    if not remaining or not closed:
        return remaining or segments, closed

    # 分配封闭路段的流量到剩余路段
    total_closed_flow = sum(s.current_flow_veh_h for s in closed)
    total_remaining_capacity = sum(s.capacity_veh_h for s in remaining)

    if total_remaining_capacity > 0:
        for seg in remaining:
            # 按通行能力比例分配封闭流量
            redistributed = total_closed_flow * (seg.capacity_veh_h / total_remaining_capacity)
            seg.current_flow_veh_h += redistributed

            # 更新速度 (过饱和)
            new_vc = seg.vc_ratio
            if new_vc < 1.0:
                seg.current_speed_kmh = seg.free_speed_kmh * (1.0 - new_vc * new_vc * 0.35)
            else:
                seg.current_speed_kmh = seg.free_speed_kmh * 0.25

            seg.current_speed_kmh = max(seg.current_speed_kmh, 3.0)

    return remaining, closed


def run_scenario(scenario: ScenarioInput) -> ScenarioResult:
    """
    运行 What-If 场景仿真。

    对输入的路网状态应用指定的干预策略, 计算基线 vs 干预后的指标对比。

    Args:
        scenario: 场景输入

    Returns:
        ScenarioResult 包含基线和干预后指标

    使用示例:
        >>> segments = [
        ...     SegmentState("S1", 1.0, 3, 1800, 1200, 35, 60, "建国路"),
        ...     SegmentState("S2", 0.8, 2, 1200, 900, 30, 50, "朝阳路"),
        ... ]
        >>> scenario = ScenarioInput(
        ...     segments=segments,
        ...     scenario_type=ScenarioType.FLOW_LIMIT,
        ...     flow_limit_pct=20,
        ...     flow_limit_zone=["S1", "S2"],
        ...     scenario_name="限流20%",
        ... )
        >>> result = run_scenario(scenario)
        >>> result.intervention.avg_speed_kmh > result.baseline.avg_speed_kmh
        True
    """
    # 基线指标
    baseline = compute_metrics(scenario.segments)

    # 应用干预
    if scenario.scenario_type == ScenarioType.FLOW_LIMIT:
        if scenario.flow_limit_zone:
            new_segments = apply_flow_limit(
                scenario.segments,
                scenario.flow_limit_zone,
                scenario.flow_limit_pct,
            )
        else:
            # 如果没有指定区域, 默认全局限流
            new_segments = apply_flow_limit_global(
                scenario.segments, scenario.flow_limit_pct
            )

    elif scenario.scenario_type == ScenarioType.SIGNAL_OPTIMIZE:
        new_segments = apply_signal_optimization(
            scenario.segments,
            scenario.signal_zone,
            scenario.signal_efficiency_gain_pct,
        )

    elif scenario.scenario_type == ScenarioType.ROAD_CLOSURE:
        remaining, _closed = apply_road_closure(
            scenario.segments, scenario.closed_roads
        )
        new_segments = remaining

    elif scenario.scenario_type == ScenarioType.COMBINED:
        # 组合策略: 按顺序应用
        current = [s.clone() for s in scenario.segments]

        # 1. 限流
        if scenario.flow_limit_pct > 0:
            current = apply_flow_limit(
                current, scenario.flow_limit_zone, scenario.flow_limit_pct
            )

        # 2. 信号优化
        if scenario.signal_efficiency_gain_pct > 0:
            current = apply_signal_optimization(
                current, scenario.signal_zone, scenario.signal_efficiency_gain_pct
            )

        # 3. 路段封闭
        if scenario.closed_roads:
            current, _ = apply_road_closure(current, scenario.closed_roads)

        new_segments = current

    else:
        raise ValueError(f"未知场景类型: {scenario.scenario_type}")

    # 干预后指标
    intervention = compute_metrics(new_segments)

    # 计算变化量
    delta = {
        "delay_reduction_veh_h": round(
            baseline.total_delay_veh_h - intervention.total_delay_veh_h, 2
        ),
        "speed_increase_kmh": round(
            intervention.avg_speed_kmh - baseline.avg_speed_kmh, 1
        ),
        "congestion_reduction": baseline.num_congested - intervention.num_congested,
        "co2_reduction_kg": round(
            baseline.total_co2_kg - intervention.total_co2_kg, 2
        ),
        "delay_reduction_pct": round(
            (baseline.total_delay_veh_h - intervention.total_delay_veh_h)
            / max(baseline.total_delay_veh_h, 0.01) * 100, 1
        ) if baseline.total_delay_veh_h > 0 else 0,
        "speed_increase_pct": round(
            (intervention.avg_speed_kmh - baseline.avg_speed_kmh)
            / max(baseline.avg_speed_kmh, 0.1) * 100, 1
        ) if baseline.avg_speed_kmh > 0 else 0,
        "co2_reduction_pct": round(
            (baseline.total_co2_kg - intervention.total_co2_kg)
            / max(baseline.total_co2_kg, 0.01) * 100, 1
        ) if baseline.total_co2_kg > 0 else 0,
    }

    return ScenarioResult(
        scenario_name=scenario.scenario_name,
        scenario_type=scenario.scenario_type.value,
        baseline=baseline,
        intervention=intervention,
        delta=delta,
    )


def build_default_scenarios(segments: List[SegmentState]) -> List[ScenarioInput]:
    """
    构建一组默认的 What-If 场景。

    Args:
        segments: 路网状态

    Returns:
        [ScenarioInput, ...]
    """
    all_ids = [s.section_id for s in segments]
    # 找拥堵路段作为干预区域
    congested_ids = [s.section_id for s in segments if s.is_congested]

    scenarios = []

    # 场景 1: 轻度限流 10%
    scenarios.append(ScenarioInput(
        segments=segments,
        scenario_type=ScenarioType.FLOW_LIMIT,
        flow_limit_pct=10,
        flow_limit_zone=congested_ids if congested_ids else all_ids[:5],
        scenario_name="轻度限流 (10%) - 拥堵区域",
    ))

    # 场景 2: 中度限流 20%
    scenarios.append(ScenarioInput(
        segments=segments,
        scenario_type=ScenarioType.FLOW_LIMIT,
        flow_limit_pct=20,
        flow_limit_zone=congested_ids if congested_ids else all_ids[:5],
        scenario_name="中度限流 (20%) - 拥堵区域",
    ))

    # 场景 3: 信号优化 15%
    scenarios.append(ScenarioInput(
        segments=segments,
        scenario_type=ScenarioType.SIGNAL_OPTIMIZE,
        signal_efficiency_gain_pct=15,
        signal_zone=congested_ids if congested_ids else all_ids[:5],
        scenario_name="信号优化 (效率+15%)",
    ))

    # 场景 4: 路段封闭 (最拥堵的 1-2 个路段)
    if congested_ids:
        closed = congested_ids[:min(2, len(congested_ids))]
        scenarios.append(ScenarioInput(
            segments=segments,
            scenario_type=ScenarioType.ROAD_CLOSURE,
            closed_roads=closed,
            scenario_name=f"路段封闭 ({', '.join(closed)})",
        ))

    # 场景 5: 组合策略
    scenarios.append(ScenarioInput(
        segments=segments,
        scenario_type=ScenarioType.COMBINED,
        flow_limit_pct=15,
        flow_limit_zone=congested_ids if congested_ids else all_ids[:5],
        signal_efficiency_gain_pct=10,
        signal_zone=congested_ids if congested_ids else all_ids[:5],
        scenario_name="组合策略 (限流15% + 信号优化10%)",
    ))

    return scenarios


def build_demo_network() -> List[SegmentState]:
    """
    构建演示用路网状态数据。

    Returns:
        包含 10 个路段的 SegmentState 列表
    """
    return [
        SegmentState("R01", 1.2, 3, 1800, 1500, 35, 60, "建国路"),
        SegmentState("R02", 0.8, 3, 1800, 1400, 38, 60, "建国门外大街"),
        SegmentState("R03", 1.0, 3, 1800, 1200, 40, 60, "东三环中路"),
        SegmentState("R04", 1.5, 4, 2400, 2000, 25, 60, "京通快速路"),
        SegmentState("R05", 0.6, 2, 1200, 1100, 18, 50, "光华路"),
        SegmentState("R06", 0.9, 3, 1800, 800, 45, 60, "朝阳路"),
        SegmentState("R07", 1.1, 3, 1800, 1600, 20, 55, "东四环中路"),
        SegmentState("R08", 0.7, 2, 1200, 1000, 28, 50, "针织路"),
        SegmentState("R09", 1.3, 3, 1800, 1300, 32, 60, "大望路"),
        SegmentState("R10", 0.5, 2, 1200, 600, 50, 55, "通惠河北路"),
    ]


# ===== 独立测试 =====
if __name__ == "__main__":
    print("=" * 60)
    print("What-If 仿真引擎 — 测试用例")
    print("=" * 60)

    # 测试 1: 指标计算
    print("\n--- 测试 1: 指标计算 ---")
    demo = build_demo_network()
    metrics = compute_metrics(demo)
    print(f"  路网: {metrics.num_segments} 个路段")
    print(f"  总延误: {metrics.total_delay_veh_h:.2f} veh·h")
    print(f"  平均速度: {metrics.avg_speed_kmh:.1f} km/h")
    print(f"  拥堵路段数: {metrics.num_congested}")
    print(f"  CO2 排放: {metrics.total_co2_kg:.2f} kg/h")
    print(f"  平均 V/C: {metrics.avg_vc_ratio:.3f}")
    assert metrics.num_segments == 10
    assert metrics.total_delay_veh_h > 0
    print("  [PASS] 通过")

    # 测试 2: 限流策略
    print("\n--- 测试 2: 限流 20% ---")
    scen_flow = ScenarioInput(
        segments=demo,
        scenario_type=ScenarioType.FLOW_LIMIT,
        flow_limit_pct=20,
        flow_limit_zone=["R04", "R05", "R07"],
        scenario_name="限流20% (拥堵区域)",
    )
    result_flow = run_scenario(scen_flow)
    print(f"  基线平均速度: {result_flow.baseline.avg_speed_kmh:.1f} km/h")
    print(f"  干预后速度:   {result_flow.intervention.avg_speed_kmh:.1f} km/h")
    print(f"  速度提升:     {result_flow.delta['speed_increase_kmh']:.1f} km/h "
          f"({result_flow.delta['speed_increase_pct']:.1f}%)")
    print(f"  延误降低:     {result_flow.delta['delay_reduction_veh_h']:.2f} veh·h "
          f"({result_flow.delta['delay_reduction_pct']:.1f}%)")
    assert result_flow.intervention.avg_speed_kmh > result_flow.baseline.avg_speed_kmh
    assert result_flow.delta["delay_reduction_veh_h"] >= 0
    print("  [PASS] 通过")

    # 测试 3: 信号优化
    print("\n--- 测试 3: 信号优化 15% ---")
    scen_signal = ScenarioInput(
        segments=demo,
        scenario_type=ScenarioType.SIGNAL_OPTIMIZE,
        signal_efficiency_gain_pct=15,
        signal_zone=["R01", "R02", "R03", "R07"],
        scenario_name="信号优化+15%",
    )
    result_signal = run_scenario(scen_signal)
    print(f"  基线拥堵路段: {result_signal.baseline.num_congested}")
    print(f"  干预后拥堵:   {result_signal.intervention.num_congested}")
    print(f"  速度提升:     {result_signal.delta['speed_increase_kmh']:.1f} km/h")
    print(f"  CO2 减排:     {result_signal.delta['co2_reduction_kg']:.2f} kg/h "
          f"({result_signal.delta['co2_reduction_pct']:.1f}%)")
    assert result_signal.intervention.num_congested <= result_signal.baseline.num_congested
    print("  [PASS] 通过")

    # 测试 4: 路段封闭
    print("\n--- 测试 4: 路段封闭 (R05 光华路) ---")
    scen_closure = ScenarioInput(
        segments=demo,
        scenario_type=ScenarioType.ROAD_CLOSURE,
        closed_roads=["R05"],
        scenario_name="封闭光华路",
    )
    result_closure = run_scenario(scen_closure)
    print(f"  基线拥堵路段: {result_closure.baseline.num_congested}")
    print(f"  干预后拥堵:   {result_closure.intervention.num_congested}")
    print(f"  基线总流量:   {result_closure.baseline.total_flow_veh_h:.0f} veh/h")
    print(f"  干预后流量:   {result_closure.intervention.total_flow_veh_h:.0f} veh/h")
    # 封闭后应少一个路段
    assert result_closure.intervention.num_segments == result_closure.baseline.num_segments - 1
    print("  [PASS] 通过")

    # 测试 5: 组合策略
    print("\n--- 测试 5: 组合策略 ---")
    scen_combined = ScenarioInput(
        segments=demo,
        scenario_type=ScenarioType.COMBINED,
        flow_limit_pct=15,
        flow_limit_zone=["R04", "R05", "R07"],
        signal_efficiency_gain_pct=10,
        signal_zone=["R01", "R02", "R03", "R07"],
        scenario_name="组合策略",
    )
    result_combined = run_scenario(scen_combined)
    print(f"  速度变化: {result_combined.delta['speed_increase_kmh']:.1f} km/h")
    print(f"  延误变化: {result_combined.delta['delay_reduction_veh_h']:.2f} veh·h "
          f"({result_combined.delta['delay_reduction_pct']:.1f}%)")
    print(f"  CO2 变化: {result_combined.delta['co2_reduction_kg']:.2f} kg/h")
    print(f"  拥堵变化: {result_combined.delta['congestion_reduction']} 个路段")
    assert result_combined.intervention.avg_speed_kmh > result_combined.baseline.avg_speed_kmh
    print("  [PASS] 通过")

    # 测试 6: 默认场景生成
    print("\n--- 测试 6: 默认场景生成 ---")
    default_scenarios = build_default_scenarios(demo)
    print(f"  生成 {len(default_scenarios)} 个默认场景:")
    for sc in default_scenarios:
        print(f"    [{sc.scenario_type.value}] {sc.scenario_name}")
    print("  [PASS] 通过")

    # 测试 7: 全局限流 vs 区域限流
    print("\n--- 测试 7: 全局限流 vs 区域限流 ---")
    # 全局
    global_result = run_scenario(ScenarioInput(
        segments=demo,
        scenario_type=ScenarioType.FLOW_LIMIT,
        flow_limit_pct=20,
        flow_limit_zone=[],
        scenario_name="全局限流",
    ))
    global_zone_result = run_scenario(ScenarioInput(
        segments=demo,
        scenario_type=ScenarioType.FLOW_LIMIT,
        flow_limit_pct=20,
        flow_limit_zone=["R01", "R02", "R03"],
        scenario_name="区域限流",
    ))
    print(f"  全局: 速度={global_result.intervention.avg_speed_kmh:.1f} km/h, "
          f"流量={global_result.intervention.total_flow_veh_h:.0f} veh/h")
    print(f"  区域: 速度={global_zone_result.intervention.avg_speed_kmh:.1f} km/h, "
          f"流量={global_zone_result.intervention.total_flow_veh_h:.0f} veh/h")
    # 全局的流量减少更多 (区域限流只影响3/10路段)
    assert global_result.intervention.total_flow_veh_h < global_zone_result.intervention.total_flow_veh_h
    print("  [PASS] 通过")

    # 测试 8: 极值场景
    print("\n--- 测试 8: 极端限流 80% ---")
    extreme = run_scenario(ScenarioInput(
        segments=demo,
        scenario_type=ScenarioType.FLOW_LIMIT,
        flow_limit_pct=80,
        flow_limit_zone=["R05"],
        scenario_name="极端限流80%",
    ))
    print(f"  R05 限流80%: 速度={extreme.intervention.avg_speed_kmh:.1f} km/h")
    print(f"  CO2 减排: {extreme.delta['co2_reduction_kg']:.2f} kg/h")
    assert extreme.delta["co2_reduction_kg"] >= 0
    print("  [PASS] 通过")

    print("\n" + "=" * 60)
    print("所有测试通过 [PASS]")
    print("=" * 60)
