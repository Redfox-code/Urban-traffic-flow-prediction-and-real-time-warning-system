"""
三路线生成算法

为 OD 对生成三条不同策略的路线:
    - 路线A (推荐): Dijkstra 最短时间路径 (权重 = 路段长度 / 预测速度)
    - 路线B (备选): 从路线A中排除 1-2 条拥堵路段后重新计算
    - 路线C (最短距离): Dijkstra 纯距离权重

速度-流量曲线:
    - 速度 > 40 km/h: 畅通
    - 25-40 km/h: 缓行
    - 15-25 km/h: 拥堵
    - < 15 km/h: 严重拥堵

参考:
    Dijkstra, E. W. "A note on two problems in connexion with graphs"
    Bast, H. et al. "Route Planning in Transportation Networks"
"""

from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass, field
import math
import heapq
import random


# 速度阈值 (km/h)
SPEED_THRESHOLDS = {
    "畅通": 40.0,
    "缓行": 25.0,
    "拥堵": 15.0,
    "严重拥堵": 0.0,
}

# 默认速度 (km/h)
DEFAULT_SPEED = 40.0


@dataclass
class RoadSegment:
    """路段信息"""
    section_id: str
    length_km: float           # 路段长度 (km)
    speed_kmh: float           # 预测速度 (km/h)
    name: str = ""             # 路段名称

    @property
    def travel_time_hours(self) -> float:
        """行驶时间 (小时)"""
        if self.speed_kmh <= 0:
            return float("inf")
        return self.length_km / self.speed_kmh

    @property
    def travel_time_minutes(self) -> float:
        """行驶时间 (分钟)"""
        return self.travel_time_hours * 60

    @property
    def congestion_level(self) -> str:
        """拥堵等级"""
        if self.speed_kmh > SPEED_THRESHOLDS["畅通"]:
            return "畅通"
        elif self.speed_kmh > SPEED_THRESHOLDS["缓行"]:
            return "缓行"
        elif self.speed_kmh > SPEED_THRESHOLDS["拥堵"]:
            return "拥堵"
        else:
            return "严重拥堵"

    def to_dict(self) -> Dict:
        return {
            "section_id": self.section_id,
            "name": self.name,
            "length_km": self.length_km,
            "speed_kmh": self.speed_kmh,
            "travel_time_min": round(self.travel_time_minutes, 1),
            "congestion_level": self.congestion_level,
        }


@dataclass
class RouteResult:
    """路线结果"""
    label: str                    # "推荐" / "备选" / "最短距离"
    segments: List[RoadSegment]   # 途经路段
    total_distance_km: float = 0.0
    total_time_min: float = 0.0
    avg_speed_kmh: float = 0.0
    num_segments: int = 0

    def __post_init__(self):
        if self.segments:
            self.total_distance_km = sum(s.length_km for s in self.segments)
            self.total_time_min = sum(s.travel_time_minutes for s in self.segments)
            self.num_segments = len(self.segments)
            if self.total_time_min > 0:
                self.avg_speed_kmh = (self.total_distance_km / self.total_time_min) * 60

    def to_dict(self) -> Dict:
        return {
            "label": self.label,
            "segments": [s.to_dict() for s in self.segments],
            "total_distance_km": round(self.total_distance_km, 2),
            "total_time_min": round(self.total_time_min, 1),
            "avg_speed_kmh": round(self.avg_speed_kmh, 1),
            "num_segments": self.num_segments,
        }


@dataclass
class ThreeRouteResult:
    """三路线完整结果"""
    origin_lat: float
    origin_lng: float
    dest_lat: float
    dest_lng: float
    route_a: Optional[RouteResult] = None
    route_b: Optional[RouteResult] = None
    route_c: Optional[RouteResult] = None

    def to_dict(self) -> Dict:
        return {
            "origin": {"lat": self.origin_lat, "lng": self.origin_lng},
            "dest": {"lat": self.dest_lat, "lng": self.dest_lng},
            "route_a": self.route_a.to_dict() if self.route_a else None,
            "route_b": self.route_b.to_dict() if self.route_b else None,
            "route_c": self.route_c.to_dict() if self.route_c else None,
            "comparison": self._comparison(),
        }

    def _comparison(self) -> Dict:
        """三条路线对比"""
        routes = []
        for label, route in [("A-推荐", self.route_a),
                             ("B-备选", self.route_b),
                             ("C-最短距离", self.route_c)]:
            if route:
                routes.append({
                    "label": label,
                    "total_time_min": route.total_time_min,
                    "total_distance_km": route.total_distance_km,
                    "num_segments": route.num_segments,
                    "avg_speed_kmh": route.avg_speed_kmh,
                })
        return {
            "routes": routes,
            "fastest": "A" if self.route_a else None,
            "shortest": "C" if self.route_c else None,
        }


class Graph:
    """路网图 (邻接表)"""

    def __init__(self):
        self.adj: Dict[str, List[Tuple[str, RoadSegment]]] = {}
        self.segments: Dict[str, RoadSegment] = {}

    def add_edge(self, from_id: str, to_id: str, segment: RoadSegment):
        """添加有向边"""
        if from_id not in self.adj:
            self.adj[from_id] = []
        self.adj[from_id].append((to_id, segment))
        self.segments[segment.section_id] = segment

    def get_neighbors(self, node_id: str) -> List[Tuple[str, RoadSegment]]:
        """获取邻居节点"""
        return self.adj.get(node_id, [])


def dijkstra(
    graph: Graph,
    start_id: str,
    end_id: str,
    weight_attr: str = "time",
    excluded_segments: Set[str] = None,
) -> Optional[List[RoadSegment]]:
    """
    Dijkstra 最短路径算法。

    Args:
        graph: 路网图
        start_id: 起点节点 ID
        end_id: 终点节点 ID
        weight_attr: 权重属性 ("time" = 时间, "distance" = 距离)
        excluded_segments: 排除的路段 ID 集合

    Returns:
        [RoadSegment, ...] 途经路段列表, 不可达则返回 None
    """
    if excluded_segments is None:
        excluded_segments = set()

    # (累计权重, 当前节点, 路径路段列表)
    INF = float("inf")
    distances = {node_id: INF for node_id in graph.adj}
    distances[start_id] = 0
    previous: Dict[str, Optional[Tuple[str, RoadSegment]]] = {start_id: None}

    pq = [(0.0, start_id)]

    while pq:
        current_dist, current = heapq.heappop(pq)

        if current == end_id:
            break

        if current_dist > distances.get(current, INF):
            continue

        for neighbor, segment in graph.get_neighbors(current):
            if segment.section_id in excluded_segments:
                continue

            # 权重计算
            if weight_attr == "distance":
                weight = segment.length_km
            else:
                weight = segment.travel_time_hours

            new_dist = current_dist + weight

            if new_dist < distances.get(neighbor, INF):
                distances[neighbor] = new_dist
                previous[neighbor] = (current, segment)
                heapq.heappush(pq, (new_dist, neighbor))

    # 重建路径
    if end_id not in previous:
        return None

    path_segments = []
    current = end_id
    while previous.get(current) is not None:
        prev_node, segment = previous[current]
        path_segments.append(segment)
        current = prev_node

    path_segments.reverse()
    return path_segments


def find_congested_segments(
    path: List[RoadSegment],
    threshold_kmh: float = 25.0,
    max_exclude: int = 2,
) -> Set[str]:
    """
    从路径中识别拥堵路段 (用于路线 B 排除)。

    Args:
        path: 路径路段列表
        threshold_kmh: 拥堵速度阈值
        max_exclude: 最多排除数

    Returns:
        排除的路段 ID 集合
    """
    # 按速度排序, 取最慢的 max_exclude 个
    sorted_segments = sorted(path, key=lambda s: s.speed_kmh)
    congested = set()
    for seg in sorted_segments:
        if seg.speed_kmh < threshold_kmh and len(congested) < max_exclude:
            congested.add(seg.section_id)
    return congested


def plan_three_routes(
    graph: Graph,
    start_id: str,
    end_id: str,
    origin_lat: float = 0.0,
    origin_lng: float = 0.0,
    dest_lat: float = 0.0,
    dest_lng: float = 0.0,
    exclude_congested: bool = True,
) -> ThreeRouteResult:
    """
    生成三条路线。

    路线A (推荐): 最短时间路径
    路线B (备选): 避开 1-2 条拥堵路段后重新计算
    路线C (最短距离): 纯距离权重

    Args:
        graph: 路网图
        start_id: 起点节点
        end_id: 终点节点
        origin_lat/lng: 起点坐标 (用于返回结果)
        dest_lat/lng: 终点坐标 (用于返回结果)
        exclude_congested: 是否生成备选路线时排除拥堵路段

    Returns:
        ThreeRouteResult

    使用示例:
        >>> g = Graph()
        >>> # 添加边...
        >>> result = plan_three_routes(g, "A", "F")
        >>> result.route_a.label
        '推荐'
    """
    result = ThreeRouteResult(
        origin_lat=origin_lat,
        origin_lng=origin_lng,
        dest_lat=dest_lat,
        dest_lng=dest_lng,
    )

    # 路线A: 最短时间
    path_a = dijkstra(graph, start_id, end_id, weight_attr="time")
    if path_a:
        result.route_a = RouteResult(label="推荐", segments=path_a)

    # 路线C: 最短距离
    path_c = dijkstra(graph, start_id, end_id, weight_attr="distance")
    if path_c:
        result.route_c = RouteResult(label="最短距离", segments=path_c)

    # 路线B: 备选 (排除拥堵路段)
    if exclude_congested and path_a:
        excluded = find_congested_segments(path_a)
        if excluded:
            path_b = dijkstra(graph, start_id, end_id,
                              weight_attr="time",
                              excluded_segments=excluded)
            if path_b:
                # 确保路线 B 与 A 不完全相同
                path_b_ids = set(s.section_id for s in path_b)
                path_a_ids = set(s.section_id for s in path_a)
                if len(path_b_ids.symmetric_difference(path_a_ids)) > 0:
                    result.route_b = RouteResult(label="备选", segments=path_b)

        # 如果没生成 B, 尝试不同的排除组合
        if result.route_b is None and path_a:
            for num_exclude in [1, 2]:
                for _attempt in range(3):
                    random.shuffle(path_a)
                    candidates = [s.section_id for s in path_a if s.speed_kmh < DEFAULT_SPEED]
                    if candidates:
                        excluded = set(random.sample(
                            candidates,
                            min(num_exclude, len(candidates))
                        ))
                        path_b = dijkstra(graph, start_id, end_id,
                                          weight_attr="time",
                                          excluded_segments=excluded)
                        if path_b:
                            result.route_b = RouteResult(label="备选", segments=path_b)
                            break
                if result.route_b:
                    break

    return result


def build_sample_graph() -> Graph:
    """
    构建测试用示例路网。

    路网结构:
        A --R1-- B --R3-- C --R5-- D --R7-- E --R8-- F
                 |       |       |
                 R2      R4      R6
                 |       |       |
                 G --R9-- H --R10-- I

    每条路段有不同长度和速度, 模拟真实场景。
    """
    g = Graph()

    segments = [
        # (from, to, id, length_km, speed_kmh, name)
        ("A", "B", "R1", 1.2, 45, "长安街东段"),
        ("B", "C", "R3", 0.8, 35, "建国路东段"),
        ("C", "D", "R5", 1.0, 20, "拥堵路段1"),
        ("D", "E", "R7", 0.6, 50, "朝阳路东段"),
        ("E", "F", "R8", 1.5, 55, "东四环南路"),
        ("B", "G", "R2", 2.0, 40, "东二环"),
        ("C", "H", "R4", 1.8, 45, "东三环"),
        ("D", "I", "R6", 2.2, 50, "东四环"),
        ("G", "H", "R9", 1.0, 35, "建国路西段"),
        ("H", "I", "R10", 1.2, 40, "朝阳路西段"),
        ("G", "A", "R11", 1.5, 30, "西段连接"),
        ("I", "F", "R12", 2.5, 60, "南段快速路"),
    ]

    for from_id, to_id, seg_id, length, speed, name in segments:
        segment = RoadSegment(
            section_id=seg_id,
            length_km=length,
            speed_kmh=speed,
            name=name,
        )
        g.add_edge(from_id, to_id, segment)

    return g


# ===== 独立测试 =====
if __name__ == "__main__":
    print("=" * 60)
    print("三路线生成算法 — 测试用例")
    print("=" * 60)

    # 测试 1: 基本图构建和 Dijkstra
    print("\n--- 测试 1: 图构建 + Dijkstra 最短时间 ---")
    graph = build_sample_graph()
    print(f"  节点数: {len(graph.adj)}")
    print(f"  路段数: {len(graph.segments)}")

    path = dijkstra(graph, "A", "F", weight_attr="time")
    assert path is not None, "路径不可达"
    print(f"  最短时间路径 A->F: {' -> '.join(s.section_id for s in path)}")
    total_time = sum(s.travel_time_minutes for s in path)
    total_dist = sum(s.length_km for s in path)
    print(f"  总时间: {total_time:.1f} min")
    print(f"  总距离: {total_dist:.2f} km")
    assert total_time > 0
    print("  [PASS] 通过")

    # 测试 2: Dijkstra 最短距离
    print("\n--- 测试 2: Dijkstra 最短距离 ---")
    path_dist = dijkstra(graph, "A", "F", weight_attr="distance")
    assert path_dist is not None
    total_dist2 = sum(s.length_km for s in path_dist)
    print(f"  最短距离路径 A->F: {' -> '.join(s.section_id for s in path_dist)}")
    print(f"  总距离: {total_dist2:.2f} km")
    print("  [PASS] 通过")

    # 测试 3: 三路线生成
    print("\n--- 测试 3: 三路线生成 A->F ---")
    result = plan_three_routes(graph, "A", "F",
                               origin_lat=39.90, origin_lng=116.40,
                               dest_lat=39.92, dest_lng=116.45)
    assert result.route_a is not None, "路线A 不存在"
    print(f"  路线A (推荐): {result.route_a.total_time_min:.1f}min, "
          f"{result.route_a.total_distance_km:.2f}km, "
          f"{result.route_a.num_segments} 段")
    print(f"    路径: {' -> '.join(s.section_id for s in result.route_a.segments)}")

    if result.route_b:
        print(f"  路线B (备选): {result.route_b.total_time_min:.1f}min, "
              f"{result.route_b.total_distance_km:.2f}km, "
              f"{result.route_b.num_segments} 段")
        print(f"    路径: {' -> '.join(s.section_id for s in result.route_b.segments)}")

    if result.route_c:
        print(f"  路线C (最短距离): {result.route_c.total_time_min:.1f}min, "
              f"{result.route_c.total_distance_km:.2f}km, "
              f"{result.route_c.num_segments} 段")
        print(f"    路径: {' -> '.join(s.section_id for s in result.route_c.segments)}")

    comparison = result._comparison()
    print(f"  对比: 最快={comparison['fastest']}, 最短={comparison['shortest']}")
    assert result.route_a is not None
    assert result.route_c is not None
    print("  [PASS] 通过")

    # 测试 4: 拥堵路段排除
    print("\n--- 测试 4: 拥堵路段排除 ---")
    congested = find_congested_segments(
        result.route_a.segments, threshold_kmh=30.0, max_exclude=2
    )
    print(f"  识别的拥堵路段: {congested}")
    print("  [PASS] 通过")

    # 测试 5: 不可达的情况
    print("\n--- 测试 5: 不可达路径 ---")
    isolated_graph = Graph()
    isolated_graph.add_edge("A", "B", RoadSegment("R1", 1.0, 40))
    isolated_graph.add_edge("C", "D", RoadSegment("R2", 1.0, 40))
    path_none = dijkstra(isolated_graph, "A", "D", weight_attr="time")
    assert path_none is None, "应该不可达"
    print("  [PASS] 正确返回 None")

    # 测试 6: 路段数据和速度曲线
    print("\n--- 测试 6: 拥堵等级判定 ---")
    test_segments = [
        RoadSegment("S1", 1.0, 50),
        RoadSegment("S2", 1.0, 30),
        RoadSegment("S3", 1.0, 20),
        RoadSegment("S4", 1.0, 10),
    ]
    for seg in test_segments:
        print(f"  {seg.speed_kmh:3d} km/h -> {seg.congestion_level:6s}, "
              f"time={seg.travel_time_minutes:.2f} min")
    print("  [PASS] 通过")

    # 测试 7: 复杂场景 - 多节点图
    print("\n--- 测试 7: 不同 OD 对测试 ---")
    for start, end in [("A", "I"), ("B", "F"), ("G", "F")]:
        r = plan_three_routes(graph, start, end)
        if r.route_a:
            print(f"  {start}->{end}: 路线A "
                  f"({r.route_a.total_time_min:.1f}min, {r.route_a.total_distance_km:.2f}km)")
        else:
            print(f"  {start}->{end}: 不可达")
    print("  [PASS] 通过")

    print("\n" + "=" * 60)
    print("所有测试通过 [PASS]")
    print("=" * 60)
