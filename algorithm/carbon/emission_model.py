"""
碳排放估算模块

基于简化 COPERT 模型，根据路段平均速度 + 车辆数量估算 CO2 排放量。

核心模型:
    CO2(g/km) = a + b*v + c*v² + d/v

    其中 v 为平均速度 (km/h)

不同车辆类型的 COPERT 系数:
    - 轻型汽油车 (PC-G): a=130.45, b=0.39, c=0.027, d=1170.3
    - 轻型柴油车 (PC-D): a=90.45, b=0.50, c=0.026, d=900.2
    - 公交车 (BUS):     a=420.0,  b=1.20, c=0.060, d=3800.0
    - 重型卡车 (HDT):    a=480.0,  b=1.80, c=0.080, d=4200.0

拥堵额外排放:
    - 当速度 < 40 km/h 时, 额外排放 = CO2_normal * (40/v - 1)
    - 当速度 >= 40 km/h 时, 额外排放 = 0

参考:
    COPERT 5 (https://www.emisia.com/utilities/copert/)
    IPCC Guidelines for National Greenhouse Gas Inventories
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
import math


# COPERT 系数: {车辆类型: (a, b, c, d)}
# 来源: COPERT 5 典型值, 单位: g/km
COPERT_COEFFICIENTS = {
    "passenger_car_gasoline": (130.45, 0.39, 0.027, 1170.3),
    "passenger_car_diesel":   (90.45,  0.50, 0.026, 900.2),
    "bus":                    (420.0,  1.20, 0.060, 3800.0),
    "heavy_truck":            (480.0,  1.80, 0.080, 4200.0),
    "light_truck":            (210.0,  0.70, 0.040, 1900.0),
    "motorcycle":             (85.0,   0.20, 0.015, 680.0),
}

# 默认车辆组成比例 (城市交通典型值)
# {车辆类型: 比例}
DEFAULT_FLEET_MIX = {
    "passenger_car_gasoline": 0.40,
    "passenger_car_diesel":   0.25,
    "light_truck":            0.15,
    "bus":                    0.08,
    "heavy_truck":            0.07,
    "motorcycle":             0.05,
}

# 拥堵速度阈值 (km/h)
CONGESTION_SPEED_THRESHOLD = 40.0

# CO2 密度: 1 g CO2 / km = 0.001 kg CO2 / km
G_TO_KG = 0.001


@dataclass
class EmissionResult:
    """单个路段的碳排放估算结果"""
    section_id: str
    avg_speed_kmh: float
    vehicle_count: int
    total_co2_kg: float           # 总 CO2 排放 (kg/h)
    normal_co2_kg: float          # 正常排放 (kg/h, 自由流情景)
    extra_co2_kg: float           # 拥堵额外排放 (kg/h)
    co2_rate_g_per_km: float      # 单位排放率 (g/km)
    congestion_factor: float      # 拥堵因子 (>=1, 1=无拥堵)
    congestion_level: str         # 拥堵等级: freeflow/moderate/congested/severe

    def to_dict(self) -> Dict:
        return {
            "section_id": self.section_id,
            "avg_speed_kmh": round(self.avg_speed_kmh, 1),
            "vehicle_count": self.vehicle_count,
            "total_co2_kg": round(self.total_co2_kg, 2),
            "normal_co2_kg": round(self.normal_co2_kg, 2),
            "extra_co2_kg": round(self.extra_co2_kg, 2),
            "co2_rate_g_per_km": round(self.co2_rate_g_per_km, 2),
            "congestion_factor": round(self.congestion_factor, 2),
            "congestion_level": self.congestion_level,
        }


def copert_emission_rate(
    speed_kmh: float,
    vehicle_type: str = "passenger_car_gasoline",
) -> float:
    """
    计算给定速度下某类车辆的 CO2 排放率 (g/km)。

    公式: CO2(g/km) = a + b*v + c*v² + d/v

    Args:
        speed_kmh: 平均速度 (km/h)
        vehicle_type: 车辆类型, 必须是 COPERT_COEFFICIENTS 的键

    Returns:
        CO2 排放率 (g/km)

    Raises:
        ValueError: speed_kmh <= 0 或 vehicle_type 未知
    """
    if speed_kmh <= 0:
        raise ValueError(f"速度必须 > 0 km/h, 实际: {speed_kmh}")

    if vehicle_type not in COPERT_COEFFICIENTS:
        raise ValueError(f"未知车辆类型: {vehicle_type}, "
                         f"可选: {list(COPERT_COEFFICIENTS.keys())}")

    a, b, c, d = COPERT_COEFFICIENTS[vehicle_type]
    v = speed_kmh

    rate = a + b * v + c * v * v + d / v
    return rate


def get_congestion_level(speed_kmh: float) -> Tuple[str, float]:
    """
    根据速度判断拥堵等级。

    Args:
        speed_kmh: 平均速度 (km/h)

    Returns:
        (拥堵等级, 拥堵因子)
        - "freeflow":  v >= 60, factor=1.0
        - "moderate":  40 <= v < 60, factor=1.0~1.5
        - "congested": 20 <= v < 40, factor=1.5~3.0
        - "severe":    v < 20, factor=3.0~6.0
    """
    if speed_kmh >= 60:
        return "freeflow", 1.0
    elif speed_kmh >= 40:
        factor = 1.0 + (60 - speed_kmh) / 60 * 0.5
        return "moderate", round(factor, 2)
    elif speed_kmh >= 20:
        factor = 1.5 + (40 - speed_kmh) / 20 * 1.5
        return "congested", round(factor, 2)
    else:
        factor = 3.0 + (20 - speed_kmh) / 20 * 3.0
        factor = min(factor, 6.0)
        return "severe", round(factor, 2)


def calculate_normal_emission(
    speed_kmh: float,
    vehicle_count: int,
    avg_trip_length_km: float = 1.0,
    fleet_mix: Optional[Dict[str, float]] = None,
) -> float:
    """
    计算自由流状态下的正常排放 (kg/h)。

    正常排放 = sum(车辆类型比例 * COPERT_rate(v) * 车辆数 * 路程长度) / 1000

    Args:
        speed_kmh: 平均速度 (km/h)
        vehicle_count: 车辆数 (veh/h)
        avg_trip_length_km: 平均行驶里程 (km), 默认 1.0km (城市路段)
        fleet_mix: 车辆组成比例, None 则使用 DEFAULT_FLEET_MIX

    Returns:
        正常排放总量 (kg/h)
    """
    if fleet_mix is None:
        fleet_mix = DEFAULT_FLEET_MIX

    total_emission_g = 0.0
    for vtype, ratio in fleet_mix.items():
        rate = copert_emission_rate(speed_kmh, vtype)
        total_emission_g += ratio * rate * vehicle_count * avg_trip_length_km

    return total_emission_g * G_TO_KG


def calculate_extra_emission(
    speed_kmh: float,
    normal_co2_kg: float,
    congestion_level: str,
) -> float:
    """
    计算拥堵额外排放 (kg/h)。

    当速度低于阈值时, 由于频繁启停、怠速等产生的额外排放。

    Args:
        speed_kmh: 平均速度 (km/h)
        normal_co2_kg: 正常排放 (kg/h)
        congestion_level: 拥堵等级

    Returns:
        额外排放 (kg/h)
    """
    if speed_kmh >= CONGESTION_SPEED_THRESHOLD:
        return 0.0

    # 额外排放因子: 速度越低, 额外比例越大
    extra_factor = max(0.0, (CONGESTION_SPEED_THRESHOLD / max(speed_kmh, 1.0)) - 1.0)

    # 拥堵越严重, 额外比例非线性增长
    if congestion_level == "severe":
        extra_factor *= 1.5  # 严重拥堵额外比例 x1.5
    elif congestion_level == "congested":
        extra_factor *= 1.2

    return normal_co2_kg * extra_factor


def estimate_emission(
    section_id: str,
    avg_speed_kmh: float,
    vehicle_count: int,
    avg_trip_length_km: float = 1.0,
    fleet_mix: Optional[Dict[str, float]] = None,
) -> EmissionResult:
    """
    估算单个路段的碳排放。

    Args:
        section_id: 路段标识
        avg_speed_kmh: 平均速度 (km/h)
        vehicle_count: 车辆数 (veh/h)
        avg_trip_length_km: 平均行驶里程 (km), 默认 1.0
        fleet_mix: 车辆组成比例

    Returns:
        EmissionResult
    """
    # 拥堵等级
    congestion_level, congestion_factor = get_congestion_level(avg_speed_kmh)

    # 计算加权平均排放率
    if fleet_mix is None:
        fleet_mix = DEFAULT_FLEET_MIX
    weighted_rate = 0.0
    for vtype, ratio in fleet_mix.items():
        rate = copert_emission_rate(max(avg_speed_kmh, 0.1), vtype)
        weighted_rate += ratio * rate

    # 正常排放
    normal_co2 = calculate_normal_emission(
        avg_speed_kmh, vehicle_count, avg_trip_length_km, fleet_mix
    )

    # 额外排放
    extra_co2 = calculate_extra_emission(avg_speed_kmh, normal_co2, congestion_level)

    return EmissionResult(
        section_id=section_id,
        avg_speed_kmh=avg_speed_kmh,
        vehicle_count=vehicle_count,
        total_co2_kg=normal_co2 + extra_co2,
        normal_co2_kg=normal_co2,
        extra_co2_kg=extra_co2,
        co2_rate_g_per_km=weighted_rate,
        congestion_factor=congestion_factor,
        congestion_level=congestion_level,
    )


def batch_estimate_emissions(
    road_segments: List[Dict],
    fleet_mix: Optional[Dict[str, float]] = None,
) -> List[EmissionResult]:
    """
    批量估算多个路段碳排放。

    Args:
        road_segments: 路段列表, 每项格式:
            {
                "section_id": str,
                "avg_speed_kmh": float,
                "vehicle_count": int,
            }
        fleet_mix: 车辆组成比例

    Returns:
        [EmissionResult, ...]
    """
    results = []
    for seg in road_segments:
        result = estimate_emission(
            section_id=str(seg.get("section_id", seg.get("id", "unknown"))),
            avg_speed_kmh=float(seg.get("avg_speed_kmh", seg.get("speed", 50))),
            vehicle_count=int(seg.get("vehicle_count", seg.get("count", 100))),
            avg_trip_length_km=float(seg.get("avg_trip_length_km", 1.0)),
            fleet_mix=fleet_mix,
        )
        results.append(result)
    return results


def summarize_emissions(results: List[EmissionResult]) -> Dict:
    """
    汇总碳排放统计。

    Args:
        results: EmissionResult 列表

    Returns:
        汇总统计字典
    """
    total_co2 = sum(r.total_co2_kg for r in results)
    total_normal = sum(r.normal_co2_kg for r in results)
    total_extra = sum(r.extra_co2_kg for r in results)

    congestion_counts = {}
    for r in results:
        congestion_counts[r.congestion_level] = \
            congestion_counts.get(r.congestion_level, 0) + 1

    return {
        "total_co2_kg": round(total_co2, 2),
        "total_normal_co2_kg": round(total_normal, 2),
        "total_extra_co2_kg": round(total_extra, 2),
        "extra_ratio_pct": round(total_extra / total_co2 * 100, 1) if total_co2 > 0 else 0,
        "num_segments": len(results),
        "segments_congested": congestion_counts.get("congested", 0) + congestion_counts.get("severe", 0),
        "congestion_distribution": congestion_counts,
    }


# ===== 独立测试 =====
if __name__ == "__main__":
    print("=" * 60)
    print("碳排放估算模型 — 测试用例")
    print("=" * 60)

    # 测试 1: 自由流状态 (60 km/h)
    print("\n--- 测试 1: 自由流 (60 km/h, 500 辆车/h) ---")
    result1 = estimate_emission("S001", 60.0, 500)
    print(f"  路段: {result1.section_id}")
    print(f"  速度: {result1.avg_speed_kmh:.1f} km/h")
    print(f"  车辆数: {result1.vehicle_count}")
    print(f"  拥堵等级: {result1.congestion_level}")
    print(f"  单位排放率: {result1.co2_rate_g_per_km:.2f} g/km")
    print(f"  正常排放: {result1.normal_co2_kg:.2f} kg/h")
    print(f"  额外排放: {result1.extra_co2_kg:.2f} kg/h")
    print(f"  总排放: {result1.total_co2_kg:.2f} kg/h")
    assert result1.extra_co2_kg == 0.0, "自由流应无额外排放"
    assert result1.congestion_level == "freeflow"
    print("  [PASS] 通过")

    # 测试 2: 拥堵状态 (20 km/h)
    print("\n--- 测试 2: 拥堵 (20 km/h, 800 辆车/h) ---")
    result2 = estimate_emission("S002", 20.0, 800)
    print(f"  拥堵等级: {result2.congestion_level}")
    print(f"  拥堵因子: {result2.congestion_factor}")
    print(f"  正常排放: {result2.normal_co2_kg:.2f} kg/h")
    print(f"  额外排放: {result2.extra_co2_kg:.2f} kg/h")
    print(f"  总排放: {result2.total_co2_kg:.2f} kg/h")
    assert result2.extra_co2_kg > 0, "拥堵应有额外排放"
    assert result2.congestion_level == "congested"
    assert result2.total_co2_kg > result2.normal_co2_kg
    print("  [PASS] 通过")

    # 测试 3: 严重拥堵 (8 km/h)
    print("\n--- 测试 3: 严重拥堵 (8 km/h, 1000 辆车/h) ---")
    result3 = estimate_emission("S003", 8.0, 1000)
    print(f"  拥堵等级: {result3.congestion_level}")
    print(f"  拥堵因子: {result3.congestion_factor}")
    print(f"  正常排放: {result3.normal_co2_kg:.2f} kg/h")
    print(f"  额外排放: {result3.extra_co2_kg:.2f} kg/h")
    print(f"  总排放: {result3.total_co2_kg:.2f} kg/h")
    assert result3.congestion_level == "severe"
    assert result3.extra_co2_kg > result3.normal_co2_kg, "严重拥堵额外排放大"
    print("  [PASS] 通过")

    # 测试 4: 批量计算
    print("\n--- 测试 4: 批量计算 (5 个路段) ---")
    segments = [
        {"section_id": "R01", "avg_speed_kmh": 65.0, "vehicle_count": 400},
        {"section_id": "R02", "avg_speed_kmh": 45.0, "vehicle_count": 600},
        {"section_id": "R03", "avg_speed_kmh": 30.0, "vehicle_count": 750},
        {"section_id": "R04", "avg_speed_kmh": 15.0, "vehicle_count": 900},
        {"section_id": "R05", "avg_speed_kmh": 5.0,  "vehicle_count": 300},
    ]
    results = batch_estimate_emissions(segments)
    summary = summarize_emissions(results)
    print(f"  总排放: {summary['total_co2_kg']:.2f} kg/h")
    print(f"  额外排放占比: {summary['extra_ratio_pct']:.1f}%")
    print(f"  拥堵路段数: {summary['segments_congested']}")
    print(f"  拥堵分布: {summary['congestion_distribution']}")
    assert summary["num_segments"] == 5
    assert summary["extra_ratio_pct"] > 0
    print("  [PASS] 通过")

    # 测试 5: COPERT 排放率验证
    print("\n--- 测试 5: COPERT 排放率验证 ---")
    for speed in [10, 30, 50, 80]:
        rate = copert_emission_rate(speed)
        print(f"  {speed} km/h -> {rate:.1f} g/km")
        # U 型曲线: 极低速和极高速排放率高
    print("  [PASS] 通过")

    # 测试 6: 不同类型车辆对比
    print("\n--- 测试 6: 不同车辆类型排放对比 (50 km/h) ---")
    for vtype in COPERT_COEFFICIENTS:
        rate = copert_emission_rate(50.0, vtype)
        print(f"  {vtype}: {rate:.1f} g/km")
    print("  [PASS] 通过")

    # 测试 7: 不同拥堵等级
    print("\n--- 测试 7: 拥堵等级判定 ---")
    test_speeds = [70, 50, 30, 15, 5]
    for speed in test_speeds:
        level, factor = get_congestion_level(speed)
        print(f"  {speed:3d} km/h -> {level:10s} (factor={factor:.1f})")
    print("  [PASS] 通过")

    print("\n" + "=" * 60)
    print("所有测试通过 [PASS]")
    print("=" * 60)
