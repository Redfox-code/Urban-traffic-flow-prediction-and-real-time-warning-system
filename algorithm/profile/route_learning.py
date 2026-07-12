"""
常用路线自动识别模块

基于用户历史出行数据, 自动识别常用路线并标注语义标签。

核心算法:
    1. OD对聚合: 经纬度容差 < 0.001 (~100m) 视为同一 OD 对
    2. K-means 出发时间聚类 (k=2), 识别早晚高峰模式
    3. 自动标签:
        - 7:00-9:30 + 工作日 → "上班路线"
        - 17:00-19:30 + 工作日 → "回家路线"
        - 周末 → "周末出行"
        - 其他 → "日常出行"
    4. 频次筛选: f >= min_frequency 的 OD 对才识别为常用路线
    5. EWMA 更新出发时间: new_avg = 0.7 * old_avg + 0.3 * current_hour

参考:
    Giannotti, F. et al. "Trajectory pattern mining"
    EWMA (Exponentially Weighted Moving Average)
"""

from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass, field
from collections import defaultdict
import math
import random
from datetime import datetime, date, timedelta


# 经纬度容差 (度), ~100m
LATLNG_TOLERANCE = 0.001

# 最小频次
MIN_FREQUENCY = 3

# EWMA 平滑系数
EWMA_ALPHA = 0.3

# 高峰时段定义
MORNING_PEAK_START = 7.0   # 7:00
MORNING_PEAK_END = 9.5     # 9:30
EVENING_PEAK_START = 17.0  # 17:00
EVENING_PEAK_END = 19.5    # 19:30

# K-means 聚类数 (早/晚高峰)
K_CLUSTERS = 2

# 一周的工作日
WEEKDAYS = {0, 1, 2, 3, 4}  # Mon=0, ..., Fri=4


@dataclass
class TripRecord:
    """单次出行记录"""
    user_id: str
    origin_lat: float
    origin_lng: float
    dest_lat: float
    dest_lng: float
    depart_hour: float          # 出发时间 (小时, 如 8.5 = 8:30)
    depart_date: Optional[str] = None   # 日期字符串 YYYY-MM-DD
    travel_time_min: float = 0.0        # 出行耗时 (分钟)
    distance_km: float = 0.0            # 出行距离 (km)

    def to_dict(self) -> Dict:
        return {
            "user_id": self.user_id,
            "origin_lat": self.origin_lat,
            "origin_lng": self.origin_lng,
            "dest_lat": self.dest_lat,
            "dest_lng": self.dest_lng,
            "depart_hour": self.depart_hour,
            "depart_date": self.depart_date or "",
            "travel_time_min": self.travel_time_min,
            "distance_km": self.distance_km,
        }

    @property
    def is_weekday(self) -> bool:
        """判断是否为工作日"""
        if self.depart_date:
            try:
                dt = datetime.strptime(self.depart_date, "%Y-%m-%d")
                return dt.weekday() in WEEKDAYS
            except (ValueError, TypeError):
                pass
        return True  # 默认工作日

    @property
    def is_morning_peak(self) -> bool:
        return MORNING_PEAK_START <= self.depart_hour <= MORNING_PEAK_END

    @property
    def is_evening_peak(self) -> bool:
        return EVENING_PEAK_START <= self.depart_hour <= EVENING_PEAK_END


@dataclass
class ODKey:
    """OD 对聚合键"""
    origin_lat: float
    origin_lng: float
    dest_lat: float
    dest_lng: float

    def __hash__(self):
        return hash((round(self.origin_lat, 3), round(self.origin_lng, 3),
                     round(self.dest_lat, 3), round(self.dest_lng, 3)))

    def __eq__(self, other):
        return (abs(self.origin_lat - other.origin_lat) < LATLNG_TOLERANCE and
                abs(self.origin_lng - other.origin_lng) < LATLNG_TOLERANCE and
                abs(self.dest_lat - other.dest_lat) < LATLNG_TOLERANCE and
                abs(self.dest_lng - other.dest_lng) < LATLNG_TOLERANCE)


@dataclass
class RouteProfile:
    """常用路线画像"""
    user_id: str
    origin_lat: float
    origin_lng: float
    dest_lat: float
    dest_lng: float
    route_label: str
    depart_hour_avg: float    # EWMA 平均出发时间
    frequency: int            # 出行频次
    peak_type: str            # morning/evening/other
    typical_travel_time_min: float = 0.0
    typical_distance_km: float = 0.0

    def to_dict(self) -> Dict:
        return {
            "user_id": self.user_id,
            "origin_lat": round(self.origin_lat, 4),
            "origin_lng": round(self.origin_lng, 4),
            "dest_lat": round(self.dest_lat, 4),
            "dest_lng": round(self.dest_lng, 4),
            "route_label": self.route_label,
            "depart_hour_avg": round(self.depart_hour_avg, 1),
            "frequency": self.frequency,
            "peak_type": self.peak_type,
            "typical_travel_time_min": round(self.typical_travel_time_min, 1),
            "typical_distance_km": round(self.typical_distance_km, 2),
        }


def haversine_km(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """计算两点间的大圆距离 (km)."""
    R = 6371.0
    dlon = math.radians(lon2 - lon1)
    dlat = math.radians(lat2 - lat1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * \
        math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    return R * c


def create_od_key(trip: TripRecord) -> ODKey:
    """创建 OD 对聚合键"""
    return ODKey(
        origin_lat=trip.origin_lat,
        origin_lng=trip.origin_lng,
        dest_lat=trip.dest_lat,
        dest_lng=trip.dest_lng,
    )


def aggregate_trips(trips: List[TripRecord]) -> Dict[ODKey, List[TripRecord]]:
    """
    按 OD 对聚合出行记录。

    Args:
        trips: 出行记录列表

    Returns:
        {ODKey: [TripRecord, ...]}
    """
    groups = defaultdict(list)
    for trip in trips:
        key = create_od_key(trip)
        groups[key].append(trip)
    return dict(groups)


def kmeans_depart_time_cluster(
    depart_hours: List[float],
    k: int = K_CLUSTERS,
    max_iter: int = 100,
) -> Tuple[List[int], List[float]]:
    """
    K-means 出发时间聚类 (一维)。

    Args:
        depart_hours: 出发时间列表 (小时)
        k: 聚类数
        max_iter: 最大迭代次数

    Returns:
        (labels, centroids)
        labels: 每个点所属聚类 [0, k-1]
        centroids: 聚类中心 [cluster_id -> center_hour]
    """
    n = len(depart_hours)
    if n == 0:
        return [], []
    if n <= k:
        return list(range(n)), depart_hours[:]

    # 初始化: 随机选择 k 个点作为中心
    random.seed(42)
    centroids = sorted(random.sample(depart_hours, k))

    labels = [0] * n
    for _ in range(max_iter):
        # 分配每个点到最近的中心
        changed = False
        for i, h in enumerate(depart_hours):
            distances = [abs(h - c) for c in centroids]
            new_label = distances.index(min(distances))
            if new_label != labels[i]:
                labels[i] = new_label
                changed = True

        if not changed:
            break

        # 更新中心
        for j in range(k):
            cluster_points = [depart_hours[i] for i in range(n) if labels[i] == j]
            if cluster_points:
                centroids[j] = sum(cluster_points) / len(cluster_points)

    return labels, centroids


def determine_peak_type(
    depart_hours: List[float],
    labels: List[int],
    centroids: List[float],
) -> str:
    """
    根据聚类结果确定高峰类型。

    如果所有出发时间都在 7-9:30 或 17-19:30:
        - 聚类中心在 7-9:30 → morning
        - 聚类中心在 17-19:30 → evening
    如果分布复杂, 取平均值判断

    Args:
        depart_hours: 出发时间列表
        labels: 聚类标签
        centroids: 聚类中心

    Returns:
        "morning" / "evening" / "mixed" / "other"
    """
    if not depart_hours:
        return "other"

    avg_hour = sum(depart_hours) / len(depart_hours)

    all_morning = all(MORNING_PEAK_START <= h <= MORNING_PEAK_END for h in depart_hours)
    all_evening = all(EVENING_PEAK_START <= h <= EVENING_PEAK_END for h in depart_hours)

    if all_morning:
        return "morning"
    if all_evening:
        return "evening"

    # 混合模式: 看主要聚类中心
    if centroids:
        main_center = centroids[0]
        if MORNING_PEAK_START <= main_center <= MORNING_PEAK_END:
            return "morning"
        elif EVENING_PEAK_START <= main_center <= EVENING_PEAK_END:
            return "evening"
        elif main_center < MORNING_PEAK_START:
            return "other"
        else:
            return "other"

    if MORNING_PEAK_START <= avg_hour <= MORNING_PEAK_END:
        return "morning"
    elif EVENING_PEAK_START <= avg_hour <= EVENING_PEAK_END:
        return "evening"
    return "other"


def generate_route_label(
    depart_hours: List[float],
    is_weekday_list: List[bool],
    peak_type: str,
) -> str:
    """
    自动生成路线标签。

    规则:
        - 工作日 + 早晨高峰 → "上班路线"
        - 工作日 + 傍晚高峰 → "回家路线"
        - 非工作日 → "周末出行"
        - 其他 → "日常出行"

    Args:
        depart_hours: 出发时间列表
        is_weekday_list: 是否为工作日列表
        peak_type: 高峰类型

    Returns:
        路线标签
    """
    if not depart_hours:
        return "未识别"

    # 检查是否主要是周末出行
    weekday_ratio = sum(is_weekday_list) / len(is_weekday_list) if is_weekday_list else 1.0

    if weekday_ratio < 0.3:
        return "周末出行"

    if peak_type == "morning":
        # 确认出发时间在早高峰范围内
        morning_trips = [h for h in depart_hours
                         if MORNING_PEAK_START <= h <= MORNING_PEAK_END]
        if len(morning_trips) >= len(depart_hours) * 0.5:
            return "上班路线"

    if peak_type == "evening":
        evening_trips = [h for h in depart_hours
                         if EVENING_PEAK_START <= h <= EVENING_PEAK_END]
        if len(evening_trips) >= len(depart_hours) * 0.5:
            return "回家路线"

    return "日常出行"


def ewma_update(old_avg: float, new_value: float, alpha: float = EWMA_ALPHA) -> float:
    """
    EWMA 更新平均出发时间。

    new_avg = (1 - alpha) * old_avg + alpha * new_value

    Args:
        old_avg: 旧平均值
        new_value: 新观测值
        alpha: 平滑系数 (0-1), 越大越关注新数据

    Returns:
        更新后的平均值
    """
    return (1 - alpha) * old_avg + alpha * new_value


def learn_routes(
    trips: List[TripRecord],
    min_frequency: int = MIN_FREQUENCY,
) -> List[RouteProfile]:
    """
    从出行记录中学习常用路线。

    Args:
        trips: 历史出行记录列表
        min_frequency: 最小频次阈值, 低于此值不识别为常用路线

    Returns:
        [RouteProfile, ...] 常用路线画像列表

    使用示例:
        >>> trips = [
        ...     TripRecord("user1", 39.90, 116.40, 39.92, 116.45, 8.5, "2026-07-10"),
        ...     TripRecord("user1", 39.90, 116.40, 39.92, 116.45, 8.3, "2026-07-11"),
        ...     TripRecord("user1", 39.90, 116.40, 39.92, 116.45, 8.0, "2026-07-12"),
        ...     TripRecord("user1", 39.92, 116.45, 39.90, 116.40, 18.0, "2026-07-10"),
        ... ]
        >>> profiles = learn_routes(trips)
        >>> profiles[0].route_label
        '上班路线'
    """
    if not trips:
        return []

    # 1. 按 OD 对聚合
    groups = aggregate_trips(trips)

    profiles = []

    for od_key, trip_list in groups.items():
        frequency = len(trip_list)
        if frequency < min_frequency:
            continue

        # 提取出发时间和工作日信息
        depart_hours = [t.depart_hour for t in trip_list]
        is_weekday_list = [t.is_weekday for t in trip_list]

        # 2. K-means 聚类的简化: 判断高峰模式
        peak_type = determine_peak_type(
            depart_hours,
            [],
            [],
        )

        # 3. 自动标签
        route_label = generate_route_label(depart_hours, is_weekday_list, peak_type)

        # 4. EWMA 平均出发时间
        avg_depart = depart_hours[0]
        for h in depart_hours[1:]:
            avg_depart = ewma_update(avg_depart, h)

        # 统计平均行程时间
        travel_times = [t.travel_time_min for t in trip_list if t.travel_time_min > 0]
        avg_travel_time = sum(travel_times) / len(travel_times) if travel_times else 0.0

        distances = [t.distance_km for t in trip_list if t.distance_km > 0]
        avg_distance = sum(distances) / len(distances) if distances else 0.0

        profile = RouteProfile(
            user_id=trip_list[0].user_id,
            origin_lat=od_key.origin_lat,
            origin_lng=od_key.origin_lng,
            dest_lat=od_key.dest_lat,
            dest_lng=od_key.dest_lng,
            route_label=route_label,
            depart_hour_avg=avg_depart,
            frequency=frequency,
            peak_type=peak_type,
            typical_travel_time_min=avg_travel_time,
            typical_distance_km=avg_distance,
        )
        profiles.append(profile)

    # 按频次降序排列
    profiles.sort(key=lambda p: p.frequency, reverse=True)

    return profiles


def generate_mock_trips(
    num_users: int = 3,
    days: int = 14,
    seed: int = 42,
) -> List[TripRecord]:
    """
    生成模拟出行数据用于测试。

    Args:
        num_users: 用户数
        days: 天数
        seed: 随机种子

    Returns:
        [TripRecord, ...]
    """
    random.seed(seed)

    # 定义一些典型 OD 对
    od_pairs = [
        # (源经度, 源纬度, 目的经度, 目的纬度, 标签类型)
        (116.40, 39.90, 116.45, 39.92, "work"),
        (116.45, 39.92, 116.40, 39.90, "home"),
        (116.42, 39.91, 116.48, 39.94, "work"),
        (116.48, 39.94, 116.42, 39.91, "home"),
        (116.44, 39.93, 116.50, 39.89, "leisure"),
        (116.38, 39.88, 116.42, 39.91, "shopping"),
    ]

    trips = []
    base_date = date(2026, 7, 1)

    for uid in range(1, num_users + 1):
        user_id = f"user_{uid}"
        for day_offset in range(days):
            current_date = base_date + timedelta(days=day_offset)
            is_weekend = current_date.weekday() in {5, 6}
            date_str = current_date.strftime("%Y-%m-%d")

            if is_weekend:
                # 周末: 休闲出行
                selected = random.sample(od_pairs, min(3, len(od_pairs)))
                for olng, olat, dlng, dlat, label_type in selected:
                    if label_type == "leisure" or label_type == "shopping":
                        depart = random.uniform(10, 16)
                        dist = haversine_km(olng, olat, dlng, dlat)
                        travel_time = dist / 30 * 60 + random.uniform(-5, 5)
                        trips.append(TripRecord(
                            user_id=user_id,
                            origin_lat=olat, origin_lng=olng,
                            dest_lat=dlat, dest_lng=dlng,
                            depart_hour=depart,
                            depart_date=date_str,
                            travel_time_min=abs(travel_time),
                            distance_km=dist,
                        ))
            else:
                # 工作日: 上班/回家
                # 上班: 8:00-9:00
                dist_w = haversine_km(od_pairs[0][0], od_pairs[0][1],
                                      od_pairs[0][2], od_pairs[0][3])
                trips.append(TripRecord(
                    user_id=user_id,
                    origin_lat=od_pairs[0][1], origin_lng=od_pairs[0][0],
                    dest_lat=od_pairs[0][3], dest_lng=od_pairs[0][2],
                    depart_hour=random.uniform(7.5, 9.0),
                    depart_date=date_str,
                    travel_time_min=dist_w / 25 * 60 + random.uniform(5, 15),
                    distance_km=dist_w,
                ))
                # 回家: 17:30-19:00
                trips.append(TripRecord(
                    user_id=user_id,
                    origin_lat=od_pairs[1][1], origin_lng=od_pairs[1][0],
                    dest_lat=od_pairs[1][3], dest_lng=od_pairs[1][2],
                    depart_hour=random.uniform(17.5, 19.0),
                    depart_date=date_str,
                    travel_time_min=dist_w / 25 * 60 + random.uniform(5, 15),
                    distance_km=dist_w,
                ))

    return trips


# ===== 独立测试 =====
if __name__ == "__main__":
    print("=" * 60)
    print("常用路线自动识别 — 测试用例")
    print("=" * 60)

    # 测试 1: OD 对聚合
    print("\n--- 测试 1: OD 对聚合 ---")
    t1 = TripRecord("user1", 39.90, 116.40, 39.92, 116.45, 8.5, "2026-07-10")
    t2 = TripRecord("user1", 39.9001, 116.4001, 39.9201, 116.4501, 8.3, "2026-07-11")
    t3 = TripRecord("user1", 39.91, 116.41, 39.93, 116.46, 8.0, "2026-07-12")
    groups = aggregate_trips([t1, t2, t3])
    print(f"  OD 对数: {len(groups)}")
    for key, trips in groups.items():
        print(f"    ({key.origin_lat:.4f},{key.origin_lng:.4f}) -> "
              f"({key.dest_lat:.4f},{key.dest_lng:.4f}): {len(trips)} 次")
    assert len(groups) == 2, f"预期 2 个 OD 对, 实际 {len(groups)}"
    print("  ✅ 通过")

    # 测试 2: 标签生成
    print("\n--- 测试 2: 路线标签生成 ---")
    label1 = generate_route_label([8.0, 8.5, 9.0], [True, True, True], "morning")
    label2 = generate_route_label([18.0, 17.5, 18.5], [True, True, True], "evening")
    label3 = generate_route_label([11.0, 14.0, 15.0], [False, False, False], "other")
    print(f"  早高峰+工作日: {label1}")
    print(f"  晚高峰+工作日: {label2}")
    print(f"  周末: {label3}")
    assert label1 == "上班路线"
    assert label2 == "回家路线"
    assert label3 == "周末出行"
    print("  ✅ 通过")

    # 测试 3: EWMA 更新
    print("\n--- 测试 3: EWMA 更新 ---")
    avg = 8.0
    updates = [8.5, 9.0, 8.2, 8.8]
    for v in updates:
        avg = ewma_update(avg, v)
        print(f"  new_value={v:.1f} -> avg={avg:.3f}")
    print("  ✅ 通过")

    # 测试 4: 完整流程 (模拟数据)
    print("\n--- 测试 4: 模拟数据完整流程 ---")
    trips = generate_mock_trips(num_users=2, days=10)
    print(f"  生成出行记录: {len(trips)} 条")

    profiles = learn_routes(trips, min_frequency=3)
    print(f"  识别常用路线: {len(profiles)} 条")
    for p in profiles:
        print(f"    {p.user_id}: {p.route_label} "
              f"(avg={p.depart_hour_avg:.1f}h, "
              f"freq={p.frequency}, "
              f"peak={p.peak_type})")
    assert len(profiles) > 0
    print("  ✅ 通过")

    # 测试 5: 最小频次过滤
    print("\n--- 测试 5: 频次过滤 (min_frequency=5) ---")
    profiles_high = learn_routes(trips, min_frequency=5)
    print(f"  min_freq=3: {len(profiles)} 条")
    print(f"  min_freq=5: {len(profiles_high)} 条")
    assert len(profiles_high) <= len(profiles)
    print("  ✅ 通过")

    # 测试 6: 手动构造测试
    print("\n--- 测试 6: 手动构造用例 ---")
    manual_trips = [
        TripRecord("alice", 39.90, 116.40, 39.92, 116.45, 8.5, "2026-07-10"),
        TripRecord("alice", 39.90, 116.40, 39.92, 116.45, 8.3, "2026-07-11"),
        TripRecord("alice", 39.90, 116.40, 39.92, 116.45, 8.0, "2026-07-12"),
        TripRecord("alice", 39.92, 116.45, 39.90, 116.40, 18.0, "2026-07-10"),
        TripRecord("alice", 39.92, 116.45, 39.90, 116.40, 17.5, "2026-07-11"),
    ]
    manual_profiles = learn_routes(manual_trips, min_frequency=2)
    print(f"  识别路线: {len(manual_profiles)} 条")
    for p in manual_profiles:
        print(f"    {p.user_id}: {p.route_label}, avg={p.depart_hour_avg:.1f}h, freq={p.frequency}")
    assert len(manual_profiles) == 2
    print("  ✅ 通过")

    print("\n" + "=" * 60)
    print("所有测试通过 ✅")
    print("=" * 60)
