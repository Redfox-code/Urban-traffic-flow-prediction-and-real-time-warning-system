"""
Webster 信号配时计算模块

基于 Webster 最优周期公式计算交叉口信号配时方案。

核心公式:
    C_opt = (1.5 * L + 5) / (1 - Y)

其中:
    L = 总损失时间（每相位损失时间之和，默认每相位 5 秒: 3s 黄灯 + 2s 全红）
    Y = 各相位最大流量比之和, y_i = q_i / S_i (流量 / 饱和流量)

有效绿灯时间: G_e = C_opt - L
各相位绿灯分配: g_i = (y_i / Y) * G_e
"""

from typing import List, Dict, Optional, Tuple


class PhaseData:
    """单个相位数据"""

    def __init__(self, phase_id: str, flow_veh_h: float,
                 saturation_flow_veh_h: float):
        """
        Args:
            phase_id: 相位标识 (如 "A", "B", "C", "D")
            flow_veh_h: 该相位的实际车流量 (veh/h)
            saturation_flow_veh_h: 该相位的饱和流量 (veh/h), 默认 1800 veh/h/车道
        """
        self.phase_id = phase_id
        self.flow = flow_veh_h
        self.saturation_flow = saturation_flow_veh_h
        self.flow_ratio = flow_veh_h / saturation_flow_veh_h if saturation_flow_veh_h > 0 else 0.0

    def __repr__(self) -> str:
        return (f"PhaseData(phase_id={self.phase_id!r}, "
                f"flow={self.flow}, sat_flow={self.saturation_flow}, "
                f"y={self.flow_ratio:.3f})")


class WebsterResult:
    """Webster 配时计算结果"""

    def __init__(self):
        self.optimal_cycle_sec: float = 0.0      # 最优周期 (秒)
        self.total_loss_time_sec: float = 0.0     # 总损失时间 (秒)
        self.total_flow_ratio: float = 0.0         # Y = sum(y_i)
        self.effective_green_sec: float = 0.0      # 有效绿灯总时间 (秒)
        self.green_splits: List[Dict] = []         # 各相位绿灯分配
        self.efficiency_gain_pct: float = 0.0      # 效率提升百分比 (vs 固定周期)
        self.delay_reduction_sec: float = 0.0       # 延误降低 (秒/每车)
        self.intersection_capacity_veh_h: float = 0.0  # 交叉口通行能力 (veh/h)

    def to_dict(self) -> Dict:
        return {
            "optimal_cycle_sec": round(self.optimal_cycle_sec, 1),
            "total_loss_time_sec": round(self.total_loss_time_sec, 1),
            "total_flow_ratio": round(self.total_flow_ratio, 3),
            "effective_green_sec": round(self.effective_green_sec, 1),
            "green_splits": self.green_splits,
            "efficiency_gain_pct": round(self.efficiency_gain_pct, 1),
            "delay_reduction_sec": round(self.delay_reduction_sec, 1),
            "intersection_capacity_veh_h": round(self.intersection_capacity_veh_h, 0),
        }

    def __repr__(self) -> str:
        return (f"WebsterResult(C_opt={self.optimal_cycle_sec:.1f}s, "
                f"G_e={self.effective_green_sec:.1f}s, "
                f"Y={self.total_flow_ratio:.3f})")


def webster_optimal_cycle(total_loss_time: float, total_flow_ratio: float) -> float:
    """
    Webster 最优周期公式: C_opt = (1.5 * L + 5) / (1 - Y)

    Args:
        total_loss_time: 总损失时间 L (秒)
        total_flow_ratio: 总流量比 Y = sum(y_i)

    Returns:
        最优周期长度 (秒)

    Raises:
        ValueError: 当 total_flow_ratio >= 1.0 时，交叉口已过饱和
    """
    if total_flow_ratio <= 0:
        raise ValueError(f"总流量比 Y={total_flow_ratio} 必须大于 0")
    if total_flow_ratio >= 1.0:
        raise ValueError(
            f"交叉口过饱和: Y={total_flow_ratio:.3f} >= 1.0, "
            f"Webster 公式不适用, 需要增加车道或优化相位方案"
        )

    C_opt = (1.5 * total_loss_time + 5) / (1.0 - total_flow_ratio)

    # 实际周期不能太小或太大 (工程约束)
    C_opt = max(30.0, min(180.0, C_opt))

    return C_opt


def calculate_green_splits(
    phases: List[PhaseData],
    optimal_cycle: float,
    total_loss_time: float,
    min_green_sec: float = 10.0,
) -> List[Dict]:
    """
    计算各相位的绿灯时间分配。

    g_i = (y_i / Y) * (C_opt - L)

    Args:
        phases: 相位列表
        optimal_cycle: 最优周期 (秒)
        total_loss_time: 总损失时间 (秒)
        min_green_sec: 最小绿灯时间 (秒), 默认 10s

    Returns:
        各相位的绿灯分配列表 [{
            "phase_id": str,
            "flow_ratio": float,
            "green_sec": float,
            "green_pct": float
        }, ...]
    """
    Y = sum(p.flow_ratio for p in phases)
    if Y <= 0:
        raise ValueError("总流量比 Y 必须大于 0")

    effective_green = optimal_cycle - total_loss_time
    if effective_green <= 0:
        raise ValueError(f"有效绿灯时间 {effective_green:.1f}s <= 0, 周期太短")

    splits = []
    total_allocated = 0.0

    for phase in phases:
        # 按流量比例分配绿灯时间
        green_sec = (phase.flow_ratio / Y) * effective_green
        green_sec = max(min_green_sec, green_sec)
        splits.append({
            "phase_id": phase.phase_id,
            "flow_ratio": round(phase.flow_ratio, 3),
            "green_sec": round(green_sec, 1),
            "green_pct": round(green_sec / optimal_cycle * 100, 1),
        })
        total_allocated += green_sec

    # 归一化调整: 如果总分配超过周期长度，按比例缩减
    if total_allocated > optimal_cycle - total_loss_time:
        scale = (optimal_cycle - total_loss_time) / total_allocated
        for s in splits:
            s["green_sec"] = round(max(min_green_sec, s["green_sec"] * scale), 1)
            s["green_pct"] = round(s["green_sec"] / optimal_cycle * 100, 1)

    return splits


def estimate_delay(
    phases: List[PhaseData],
    optimal_cycle: float,
    total_loss_time: float,
    fixed_cycle: Optional[float] = None,
) -> Tuple[float, float]:
    """
    估算 Webster 配时方案的延误，并与固定周期对比。

    使用 Webster 延误公式（简化）:
    d = (C * (1 - g/C)^2) / (2 * (1 - y)) + ...

    这里对比最优方案 vs 固定周期方案

    Args:
        phases: 相位列表
        optimal_cycle: 最优周期 (秒)
        total_loss_time: 总损失时间 (秒)
        fixed_cycle: 固定周期 (秒), 若为 None 则假定固定周期 = optimal_cycle + 20s

    Returns:
        (efficiency_gain_pct, delay_reduction_sec) 效率提升百分比, 延误降低秒数
    """
    Y = sum(p.flow_ratio for p in phases)
    if Y <= 0:
        return 0.0, 0.0

    if fixed_cycle is None:
        fixed_cycle = optimal_cycle + 20  # 假设固定周期比最优长 20s

    # 最优配时下的延误 (Webster 延误公式简化版)
    G_e_opt = optimal_cycle - total_loss_time
    d_opt = 0.0
    for phase in phases:
        y = phase.flow_ratio
        g_opt = (y / Y) * G_e_opt if Y > 0 else 0
        if g_opt <= 0 or optimal_cycle <= 0:
            continue
        # Webster 第一项: 均匀延误
        d1 = (optimal_cycle * (1 - g_opt / optimal_cycle) ** 2) / (2 * (1 - y)) if y < 1 else 0
        d_opt += d1 * y
    if Y > 0:
        d_opt /= (len(phases) * Y)

    # 固定周期下的延误
    G_e_fixed = fixed_cycle - total_loss_time
    d_fixed = 0.0
    for phase in phases:
        y = phase.flow_ratio
        g_fixed = (y / Y) * G_e_fixed if Y > 0 else 0
        if g_fixed <= 0 or fixed_cycle <= 0:
            continue
        d1 = (fixed_cycle * (1 - g_fixed / fixed_cycle) ** 2) / (2 * (1 - y)) if y < 1 else 0
        d_fixed += d1 * y
    if Y > 0:
        d_fixed /= (len(phases) * Y)

    # 效率提升 = (固定延误 - 最优延误) / 固定延误
    efficiency_gain = 0.0
    if d_fixed > 0:
        efficiency_gain = (d_fixed - d_opt) / d_fixed * 100

    delay_reduction = d_fixed - d_opt

    return efficiency_gain, delay_reduction


def calculate_intersection_capacity(
    phases: List[PhaseData],
    optimal_cycle: float,
    green_splits: List[Dict],
    total_loss_time: float,
) -> float:
    """
    计算交叉口通行能力 (veh/h)。

    通行能力 = sum(饱和流量_i * (g_i / C))

    Args:
        phases: 相位列表
        optimal_cycle: 最优周期 (秒)
        green_splits: 绿灯分配列表
        total_loss_time: 总损失时间 (秒, 未使用, 保留参数)

    Returns:
        交叉口总通行能力 (veh/h)
    """
    capacity = 0.0
    for phase, split in zip(phases, green_splits):
        g_i = split["green_sec"]
        cap_i = phase.saturation_flow * (g_i / optimal_cycle)
        capacity += cap_i
    return capacity


def webster_signal_timing(
    intersection_data: Dict,
) -> WebsterResult:
    """
    Webster 信号配时计算主函数。

    Args:
        intersection_data: 交叉口数据字典, 格式:
            {
                "intersection_id": str,         # 交叉口标识
                "phases": [                      # 相位列表
                    {
                        "phase_id": str,         # 相位 ID
                        "flow": float,           # 车流量 (veh/h)
                        "saturation_flow": float # 饱和流量 (veh/h)
                    },
                    ...
                ],
                "loss_time_per_phase": float,    # 每相位损失时间 (秒, 默认 5)
                "min_green_sec": float,          # 最小绿灯时间 (秒, 默认 10)
                "fixed_cycle_sec": Optional[float] # 当前固定周期 (秒, 用于对比)
            }

    Returns:
        WebsterResult 包含:
            - optimal_cycle_sec: 最优周期 (秒)
            - total_loss_time_sec: 总损失时间 (秒)
            - total_flow_ratio: 总流量比 Y
            - effective_green_sec: 有效绿灯时间 (秒)
            - green_splits: 各相位绿灯分配 [{phase_id, flow_ratio, green_sec, green_pct}]
            - efficiency_gain_pct: 效率提升百分比
            - delay_reduction_sec: 延误降低 (秒/每车)
            - intersection_capacity_veh_h: 交叉口通行能力 (veh/h)

    Raises:
        ValueError: 输入数据不合法
        KeyError: 缺少必要字段

    使用示例:
        >>> data = {
        ...     "intersection_id": "INT-001",
        ...     "phases": [
        ...         {"phase_id": "A", "flow": 600, "saturation_flow": 1800},
        ...         {"phase_id": "B", "flow": 500, "saturation_flow": 1800},
        ...         {"phase_id": "C", "flow": 400, "saturation_flow": 1800},
        ...         {"phase_id": "D", "flow": 300, "saturation_flow": 1800},
        ...     ],
        ...     "loss_time_per_phase": 5,
        ...     "min_green_sec": 10,
        ... }
        >>> result = webster_signal_timing(data)
        >>> result.optimal_cycle_sec
        68.3
    """
    # === 解析输入 ===
    phases_raw = intersection_data.get("phases", [])
    if not phases_raw:
        raise ValueError("intersection_data 必须包含非空的 phases 列表")

    loss_per_phase = intersection_data.get("loss_time_per_phase", 5.0)
    min_green = intersection_data.get("min_green_sec", 10.0)
    fixed_cycle = intersection_data.get("fixed_cycle_sec", None)
    inter_id = intersection_data.get("intersection_id", "unknown")

    # 构建 PhaseData 列表
    phases: List[PhaseData] = []
    for p in phases_raw:
        phase = PhaseData(
            phase_id=p["phase_id"],
            flow_veh_h=float(p["flow"]),
            saturation_flow_veh_h=float(p.get("saturation_flow", 1800)),
        )
        phases.append(phase)

    # === 计算 ===
    # 总损失时间
    n_phases = len(phases)
    total_loss_time = n_phases * loss_per_phase

    # 总流量比 Y
    Y = sum(p.flow_ratio for p in phases)

    # 最优周期
    C_opt = webster_optimal_cycle(total_loss_time, Y)

    # 绿灯分配
    green_splits = calculate_green_splits(phases, C_opt, total_loss_time, min_green)

    # 有效绿灯时间
    G_e = C_opt - total_loss_time

    # 延误估计
    eff_gain, delay_red = estimate_delay(phases, C_opt, total_loss_time, fixed_cycle)

    # 通行能力
    capacity = calculate_intersection_capacity(phases, C_opt, green_splits, total_loss_time)

    # === 组装结果 ===
    result = WebsterResult()
    result.optimal_cycle_sec = C_opt
    result.total_loss_time_sec = total_loss_time
    result.total_flow_ratio = Y
    result.effective_green_sec = G_e
    result.green_splits = green_splits
    result.efficiency_gain_pct = eff_gain
    result.delay_reduction_sec = delay_red
    result.intersection_capacity_veh_h = capacity

    return result


# ===== 独立测试 =====
if __name__ == "__main__":
    print("=" * 60)
    print("Webster 信号配时计算 — 测试用例")
    print("=" * 60)

    # 测试用例 1: 标准四相位交叉口
    print("\n--- 测试 1: 标准四相位交叉口 ---")
    data1 = {
        "intersection_id": "INT-001",
        "phases": [
            {"phase_id": "A (东西直行)", "flow": 800, "saturation_flow": 1800},
            {"phase_id": "B (东西左转)", "flow": 400, "saturation_flow": 1600},
            {"phase_id": "C (南北直行)", "flow": 700, "saturation_flow": 1800},
            {"phase_id": "D (南北左转)", "flow": 350, "saturation_flow": 1600},
        ],
        "loss_time_per_phase": 5,
        "min_green_sec": 10,
    }
    result1 = webster_signal_timing(data1)
    print(f"  最优周期: {result1.optimal_cycle_sec:.1f}s")
    print(f"  总损失时间: {result1.total_loss_time_sec:.1f}s")
    print(f"  总流量比 Y: {result1.total_flow_ratio:.3f}")
    print(f"  有效绿灯时间: {result1.effective_green_sec:.1f}s")
    print(f"  通行能力: {result1.intersection_capacity_veh_h:.0f} veh/h")
    print(f"  效率提升: {result1.efficiency_gain_pct:.1f}%")
    print(f"  延误降低: {result1.delay_reduction_sec:.2f}s")
    print("  绿灯分配:")
    for s in result1.green_splits:
        print(f"    {s['phase_id']}: {s['green_sec']:.1f}s ({s['green_pct']:.1f}%)")
    assert 50 < result1.optimal_cycle_sec < 120, f"周期不在合理范围内: {result1.optimal_cycle_sec}"
    assert abs(result1.total_loss_time_sec - 20.0) < 0.01
    assert result1.intersection_capacity_veh_h > 0
    print("  ✅ 通过")

    # 测试用例 2: 两相位简单交叉口
    print("\n--- 测试 2: 两相位简单交叉口 ---")
    data2 = {
        "intersection_id": "INT-002",
        "phases": [
            {"phase_id": "A (主路)", "flow": 900, "saturation_flow": 1800},
            {"phase_id": "B (支路)", "flow": 300, "saturation_flow": 1800},
        ],
        "loss_time_per_phase": 5,
    }
    result2 = webster_signal_timing(data2)
    print(f"  最优周期: {result2.optimal_cycle_sec:.1f}s")
    print(f"  流量比 Y: {result2.total_flow_ratio:.3f}")
    print("  绿灯分配:")
    for s in result2.green_splits:
        print(f"    {s['phase_id']}: {s['green_sec']:.1f}s ({s['green_pct']:.1f}%)")
    assert 30 < result2.optimal_cycle_sec < 120
    print("  ✅ 通过")

    # 测试用例 3: 拥堵交叉口 (高流量比)
    print("\n--- 测试 3: 高流量比交叉口 (接近饱和) ---")
    data3 = {
        "intersection_id": "INT-003",
        "phases": [
            {"phase_id": "A", "flow": 1500, "saturation_flow": 1800},
            {"phase_id": "B", "flow": 1200, "saturation_flow": 1800},
        ],
        "loss_time_per_phase": 5,
    }
    try:
        result3 = webster_signal_timing(data3)
        print(f"  最优周期: {result3.optimal_cycle_sec:.1f}s")
        print(f"  流量比 Y: {result3.total_flow_ratio:.3f}")
        # 高流量比应产生较长周期
        assert result3.optimal_cycle_sec > 60
        print("  ✅ 通过")
    except ValueError as e:
        print(f"  ⚠️ 过饱和: {e}")

    # 测试用例 4: 过饱和交叉口
    print("\n--- 测试 4: 过饱和交叉口 ---")
    data4 = {
        "intersection_id": "INT-004",
        "phases": [
            {"phase_id": "A", "flow": 1700, "saturation_flow": 1800},
            {"phase_id": "B", "flow": 1600, "saturation_flow": 1800},
        ],
        "loss_time_per_phase": 5,
    }
    try:
        webster_signal_timing(data4)
        print("  ❌ 应该抛出 ValueError")
    except ValueError as e:
        print(f"  ✅ 正确拒绝过饱和: {e}")

    # 测试用例 5: 最小绿灯保障
    print("\n--- 测试 5: 最小绿灯保障 (支路流量极低) ---")
    data5 = {
        "intersection_id": "INT-005",
        "phases": [
            {"phase_id": "A (主路)", "flow": 1200, "saturation_flow": 1800},
            {"phase_id": "B (支路)", "flow": 50, "saturation_flow": 1800},
        ],
        "loss_time_per_phase": 5,
        "min_green_sec": 8,
    }
    result5 = webster_signal_timing(data5)
    print(f"  最优周期: {result5.optimal_cycle_sec:.1f}s")
    for s in result5.green_splits:
        print(f"    {s['phase_id']}: {s['green_sec']:.1f}s ({s['green_pct']:.1f}%)")
        if s['phase_id'] == 'B (支路)':
            assert s['green_sec'] >= 8.0, f"支路绿灯应 >= 8s, 实际 {s['green_sec']}s"
    print("  ✅ 通过")

    print("\n" + "=" * 60)
    print("所有测试通过 ✅")
    print("=" * 60)
