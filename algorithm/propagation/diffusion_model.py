"""
拥堵传播图扩散模型

基于图论和条件概率的拥堵传播预测算法。

核心算法:
    1. 从 roadNetwork.json 或路网文件提取路段连接关系, 构建邻接矩阵
    2. 从源路段 s0 出发, 计算相邻路段的拥堵传播概率
    3. 递归多跳传播: 从已有传播路径继续向外扩展
    4. 剪枝条件: 概率 < 阈值 或 深度 > 最大深度

传播概率模型:
    P(B|A) = base_prob * exp(-alpha * distance_km) * speed_factor

    其中:
    - base_prob: 基础传播概率 (默认 0.6)
    - alpha: 距离衰减系数 (默认 0.5)
    - speed_factor: 源路段速度因子 (拥堵越严重, 传播概率越高)

参考:
    Long, J. et al. "Congestion Propagation in Urban Traffic Networks"
    Saberi, M. et al. "A Complex Network Perspective on Traffic Congestion"
"""

from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass, field
import math
import json
import os


# ===== 邻接矩阵构建 =====

def haversine_km(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """计算两点间的大圆距离 (km)."""
    R = 6371.0
    dlon = math.radians(lon2 - lon1)
    dlat = math.radians(lat2 - lat1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * \
        math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    return R * c


def load_road_network(json_path: str = None) -> List[Dict]:
    """
    加载 roadNetwork.json 路段数据。

    Args:
        json_path: 文件路径, None 则自动搜索

    Returns:
        路段列表 [{id, name, path, ...}]
    """
    if json_path is None:
        # 自动搜索常见位置
        candidates = [
            "frontend/src/data/roadNetwork.json",
            "../frontend/src/data/roadNetwork.json",
            "../../frontend/src/data/roadNetwork.json",
        ]
        for path in candidates:
            if os.path.exists(path):
                json_path = path
                break
        if json_path is None:
            raise FileNotFoundError(
                "未找到 roadNetwork.json, 请指定路径"
            )

    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    segments = data.get("segments", [])
    return segments


def build_adjacency_matrix(
    segments: List[Dict],
    proximity_threshold_m: float = 100.0,
) -> Dict[int, List[int]]:
    """
    构建路段邻接矩阵。

    两个路段相邻的条件: 一条路段的端点与另一条路段的端点的距离 < threshold。

    Args:
        segments: 路段列表 [{id, path, ...}]
        proximity_threshold_m: 相邻判定阈值 (米), 默认 100m

    Returns:
        {section_id: [相邻的section_id列表]}
    """
    adj = {s["id"]: [] for s in segments}

    # 提取每条路段的起点和终点
    endpoints = {}
    for s in segments:
        path = s["path"]
        if path:
            endpoints[s["id"]] = {
                "start": (path[0][0], path[0][1]),
                "end": (path[-1][0], path[-1][1]),
            }
        else:
            endpoints[s["id"]] = None

    # 两两比较
    threshold_km = proximity_threshold_m / 1000.0
    seg_ids = [s["id"] for s in segments]

    for i in range(len(seg_ids)):
        id_i = seg_ids[i]
        ep_i = endpoints.get(id_i)
        if ep_i is None:
            continue

        # 只检查未配对的, 减少重复计算
        for j in range(i + 1, len(seg_ids)):
            id_j = seg_ids[j]
            ep_j = endpoints.get(id_j)
            if ep_j is None:
                continue

            # 检查端点间距离 (4 种组合)
            dists = [
                haversine_km(ep_i["start"][0], ep_i["start"][1],
                             ep_j["start"][0], ep_j["start"][1]),
                haversine_km(ep_i["start"][0], ep_i["start"][1],
                             ep_j["end"][0], ep_j["end"][1]),
                haversine_km(ep_i["end"][0], ep_i["end"][1],
                             ep_j["start"][0], ep_j["start"][1]),
                haversine_km(ep_i["end"][0], ep_i["end"][1],
                             ep_j["end"][0], ep_j["end"][1]),
            ]

            if any(d <= threshold_km for d in dists):
                adj[id_i].append(id_j)
                adj[id_j].append(id_i)

    return adj


def build_adjacency_from_sumo(net_xml_path: str) -> Dict[int, List[int]]:
    """
    从 SUMO .net.xml 文件中提取路段连接关系。

    Args:
        net_xml_path: .net.xml 文件路径

    Returns:
        {edge_id: [相邻edge_id列表]}
    """
    import xml.etree.ElementTree as ET

    tree = ET.parse(net_xml_path)
    root = tree.getroot()

    # 收集所有非 internal 的 edge
    edges = {}
    for edge in root.findall("edge"):
        edge_id = edge.get("id", "")
        if edge_id.startswith(":"):
            continue  # 跳过 internal edges
        edges[edge_id] = {"from": edge.get("from"), "to": edge.get("to")}

    # 构建邻接: 通过 junction 连接
    adj = {eid: [] for eid in edges}
    junction_edges = {}  # {junction_id: [edge_ids]}

    for eid, conn in edges.items():
        from_j = conn["from"]
        to_j = conn["to"]
        if from_j:
            junction_edges.setdefault(from_j, []).append(eid)
        if to_j:
            junction_edges.setdefault(to_j, []).append(eid)

    # 属于同一 junction 的 edge 彼此相邻
    for junction_id, edge_list in junction_edges.items():
        for i in range(len(edge_list)):
            for j in range(i + 1, len(edge_list)):
                eid_i = edge_list[i]
                eid_j = edge_list[j]
                if eid_j not in adj[eid_i]:
                    adj[eid_i].append(eid_j)
                if eid_i not in adj[eid_j]:
                    adj[eid_j].append(eid_i)

    return adj


# ===== 传播模型 =====

@dataclass
class PropagationNode:
    """传播树节点"""
    section_id: str
    from_section: Optional[str]  # 父节点 ID
    probability: float            # 传播概率
    delay_minutes: float          # 预计延迟 (分钟)
    depth: int                    # 传播深度
    children: List["PropagationNode"] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "section_id": self.section_id,
            "from": self.from_section,
            "probability": round(self.probability, 3),
            "delay_minutes": round(self.delay_minutes, 1),
            "depth": self.depth,
            "children": [c.to_dict() for c in self.children],
        }


@dataclass
class PropagationResult:
    """传播结果"""
    root_section_id: str
    tree: PropagationNode
    total_nodes: int = 0
    max_depth: int = 0
    avg_probability: float = 0.0

    def to_flat_list(self) -> List[Dict]:
        """展平为列表格式"""
        flat = []

        def dfs(node: PropagationNode):
            flat.append({
                "from": node.from_section,
                "to": node.section_id,
                "probability": round(node.probability, 3),
                "delay_minutes": round(node.delay_minutes, 1),
                "depth": node.depth,
            })
            for child in node.children:
                dfs(child)

        dfs(self.tree)
        return flat

    def to_dict(self) -> Dict:
        return {
            "root_section_id": self.root_section_id,
            "tree": self.tree.to_dict(),
            "total_nodes": self.total_nodes,
            "max_depth": self.max_depth,
            "avg_probability": round(self.avg_probability, 3),
            "flat_list": self.to_flat_list(),
        }


def calculate_propagation_probability(
    source_speed_kmh: float,
    target_speed_kmh: float,
    distance_km: float,
    base_prob: float = 0.6,
    alpha: float = 0.5,
) -> float:
    """
    计算从源路段到目标路段的拥堵传播概率。

    P = base_prob * exp(-alpha * distance) * speed_factor

    speed_factor:
        - 源路段速度 < 20 km/h (严重拥堵): factor = 1.2
        - 源路段速度 20-40 km/h (拥堵): factor = 1.0
        - 源路段速度 40-60 km/h (缓行): factor = 0.7
        - 源路段速度 > 60 km/h (畅通): factor = 0.3

    Args:
        source_speed_kmh: 源路段速度
        target_speed_kmh: 目标路段当前速度 (用于估计延误)
        distance_km: 两路段端点距离 (km)
        base_prob: 基础传播概率
        alpha: 距离衰减系数

    Returns:
        传播概率 [0, 1]
    """
    # 速度因子
    if source_speed_kmh < 20:
        speed_factor = 1.2
    elif source_speed_kmh < 40:
        speed_factor = 1.0
    elif source_speed_kmh < 60:
        speed_factor = 0.7
    else:
        speed_factor = 0.3

    # 距离衰减
    distance_factor = math.exp(-alpha * max(distance_km, 0.01))

    prob = base_prob * speed_factor * distance_factor
    return min(1.0, max(0.0, prob))


def estimate_delay_minutes(
    source_speed_kmh: float,
    target_speed_kmh: float,
    distance_km: float,
) -> float:
    """
    估计传播导致的目标路段延误 (分钟)。

    基于速度差异和距离:
    delay = distance * (1/target_speed - 1/source_speed) * 60 (min)

    Args:
        source_speed_kmh: 源路段速度
        target_speed_kmh: 目标路段当前速度
        distance_km: 路段长度 (km)

    Returns:
        延误 (分钟), 最小 0
    """
    freeflow_speed = max(source_speed_kmh, 40.0)  # 假设自由流速度
    current_speed = max(target_speed_kmh, 1.0)

    delay_hours = distance_km * (1.0 / current_speed - 1.0 / freeflow_speed)
    delay_min = max(0.0, delay_hours * 60.0)
    return delay_min


def propagate_congestion(
    source_section_id: int,
    adjacency_matrix: Dict[int, List[int]],
    section_speeds: Dict[int, float],
    section_delays: Optional[Dict[int, float]] = None,
    max_depth: int = 3,
    prob_threshold: float = 0.3,
    base_prob: float = 0.6,
    alpha: float = 0.5,
    distances: Optional[Dict[Tuple[int, int], float]] = None,
) -> PropagationResult:
    """
    递归多跳拥堵传播计算。

    Args:
        source_section_id: 源路段 ID
        adjacency_matrix: 邻接矩阵 {section_id: [相邻section_id]}
        section_speeds: {section_id: avg_speed_kmh}
        section_delays: {section_id: delay_minutes}, 未提供则自动计算
        max_depth: 最大传播深度 (默认 3)
        prob_threshold: 概率剪枝阈值 (默认 0.3)
        base_prob: 基础传播概率
        alpha: 距离衰减系数
        distances: {(from_id, to_id): distance_km}, 未提供则默认 0.5km

    Returns:
        PropagationResult
    """

    def _dfs(
        current_id: int,
        from_id: Optional[int],
        current_depth: int,
        visited: Set[int],
    ) -> Optional[PropagationNode]:
        """递归 DFS 构建传播树"""
        if current_depth > max_depth:
            return None

        # 计算传播概率
        prob = 1.0
        delay = 0.0
        distance = 0.5  # 默认距离

        if from_id is not None:
            source_speed = section_speeds.get(from_id, 40)
            target_speed = section_speeds.get(current_id, 40)

            if distances and (from_id, current_id) in distances:
                distance = distances[(from_id, current_id)]
            elif distances and (current_id, from_id) in distances:
                distance = distances[(current_id, from_id)]

            prob = calculate_propagation_probability(
                source_speed, target_speed, distance,
                base_prob, alpha,
            )

            if section_delays and current_id in section_delays:
                delay = section_delays[current_id]
            else:
                delay = estimate_delay_minutes(source_speed, target_speed, distance)

        # 剪枝
        if prob < prob_threshold and from_id is not None:
            return None

        node = PropagationNode(
            section_id=str(current_id),
            from_section=str(from_id) if from_id is not None else None,
            probability=prob,
            delay_minutes=delay,
            depth=current_depth,
        )

        visited.add(current_id)

        # 递归处理相邻路段
        for neighbor in adjacency_matrix.get(current_id, []):
            if neighbor not in visited:
                child = _dfs(neighbor, current_id, current_depth + 1, visited)
                if child is not None:
                    node.children.append(child)

        return node

    visited: Set[int] = set()
    tree = _dfs(source_section_id, None, 0, visited)

    if tree is None:
        tree = PropagationNode(
            section_id=str(source_section_id),
            from_section=None,
            probability=1.0,
            delay_minutes=0.0,
            depth=0,
        )

    # 统计
    total_nodes = 0
    total_prob = 0.0
    max_d = 0

    def _stats(node: PropagationNode):
        nonlocal total_nodes, total_prob, max_d
        total_nodes += 1
        total_prob += node.probability
        max_d = max(max_d, node.depth)
        for child in node.children:
            _stats(child)

    _stats(tree)

    result = PropagationResult(
        root_section_id=str(source_section_id),
        tree=tree,
        total_nodes=total_nodes,
        max_depth=max_d,
        avg_probability=total_prob / total_nodes if total_nodes > 0 else 0.0,
    )

    return result


def build_proximity_distances(
    segments: List[Dict],
    adjacency: Dict[int, List[int]],
) -> Dict[Tuple[int, int], float]:
    """
    构建相邻路段之间的距离映射。

    Args:
        segments: 路段列表
        adjacency: 邻接矩阵

    Returns:
        {(from_id, to_id): distance_km}
    """
    seg_paths = {}
    for s in segments:
        path = s.get("path", [])
        if path:
            seg_paths[s["id"]] = path

    distances = {}
    for from_id, neighbors in adjacency.items():
        path_from = seg_paths.get(from_id, [])
        if not path_from:
            continue
        end_from = path_from[-1] if len(path_from) > 1 else path_from[0]

        for to_id in neighbors:
            path_to = seg_paths.get(to_id, [])
            if not path_to:
                continue
            start_to = path_to[0] if len(path_to) > 1 else path_to[-1]

            dist = haversine_km(
                end_from[0], end_from[1],
                start_to[0], start_to[1],
            )
            distances[(from_id, to_id)] = max(dist, 0.01)

    return distances


def get_connected_components(
    adjacency: Dict[int, List[int]],
) -> List[List[int]]:
    """
    获取连通分量 (用于理解路网拓扑).

    Args:
        adjacency: 邻接矩阵

    Returns:
        [[section_id, ...], ...] 连通分量列表
    """
    visited = set()
    components = []

    def _bfs(start: int) -> List[int]:
        component = []
        queue = [start]
        while queue:
            node = queue.pop(0)
            if node in visited:
                continue
            visited.add(node)
            component.append(node)
            for neighbor in adjacency.get(node, []):
                if neighbor not in visited:
                    queue.append(neighbor)
        return component

    for node in adjacency:
        if node not in visited:
            comp = _bfs(node)
            if comp:
                components.append(comp)

    return components


# ===== 独立测试 =====
if __name__ == "__main__":
    print("=" * 60)
    print("拥堵传播图扩散模型 — 测试用例")
    print("=" * 60)

    # 测试 1: 构建邻接矩阵
    print("\n--- 测试 1: 邻接矩阵构建 ---")
    try:
        segments = load_road_network()
        print(f"  加载路段数: {len(segments)}")

        adj = build_adjacency_matrix(segments, proximity_threshold_m=150)
        connected = sum(1 for v in adj.values() if v)
        total_edges = sum(len(v) for v in adj.values()) // 2
        print(f"  有连接的路段数: {connected}/{len(segments)}")
        print(f"  总连接边数: {total_edges}")

        components = get_connected_components(adj)
        print(f"  连通分量数: {len(components)}")
        for i, comp in enumerate(components[:5]):
            print(f"    分量 {i+1}: {len(comp)} 个路段")
        print("  [PASS] 通过")
    except FileNotFoundError as e:
        print(f"  [WARN] {e}, 使用模拟路网测试")
        # 创建模拟路网
        mock_segments = []
        for i in range(1, 21):
            mock_segments.append({
                "id": i,
                "name": f"Road_{i}",
                "path": [
                    [116.4 + i * 0.001, 39.90 + i * 0.0005],
                    [116.4 + i * 0.001 + 0.01, 39.90 + i * 0.0005],
                ],
            })
        print(f"  模拟路段数: {len(mock_segments)}")
        adj = build_adjacency_matrix(mock_segments, proximity_threshold_m=2000)
        connected = sum(1 for v in adj.values() if v)
        print(f"  有连接的路段数: {connected}/{len(mock_segments)}")

    # 测试 2: 传播概率计算
    print("\n--- 测试 2: 传播概率计算 ---")
    scenarios = [
        ("严重拥堵 -> 相邻", 15, 40, 0.3),
        ("拥堵 -> 相邻", 30, 45, 0.3),
        ("缓行 -> 相邻", 50, 50, 0.3),
        ("畅通 -> 相邻", 70, 55, 0.3),
        ("远距离衰减", 15, 40, 1.5),
    ]
    for label, src_speed, tgt_speed, dist in scenarios:
        prob = calculate_propagation_probability(src_speed, tgt_speed, dist)
        delay = estimate_delay_minutes(src_speed, tgt_speed, dist)
        print(f"  {label}: P={prob:.3f}, delay={delay:.1f}min")
    print("  [PASS] 通过")

    # 测试 3: 模拟传播路径
    print("\n--- 测试 3: 模拟路网传播 ---")
    mock_adj = {i: [] for i in range(1, 13)}
    # 创建链式路网: 1-2-3-4-5-6-7-8-9-10-11-12
    for i in range(1, 12):
        mock_adj[i].append(i + 1)
        mock_adj[i + 1].append(i)
    # 添加分支: 3-13, 7-14
    mock_adj[3].append(13)
    mock_adj[13] = [3]
    mock_adj[7].append(14)
    mock_adj[14] = [7]

    # 速度数据
    speeds = {
        1: 10, 2: 15, 3: 25, 4: 35, 5: 40, 6: 45,
        7: 20, 8: 30, 9: 40, 10: 50, 11: 55, 12: 60,
        13: 30, 14: 25,
    }

    print("  路网结构: 1-2-3-4-5-6-7-8-9-10-11-12")
    print("               |         |")
    print("              13        14")
    print(f"  源路段 1 (速度 {speeds[1]} km/h, 严重拥堵)")

    result = propagate_congestion(
        source_section_id=1,
        adjacency_matrix=mock_adj,
        section_speeds=speeds,
        max_depth=3,
        prob_threshold=0.2,
    )

    print(f"  总节点数: {result.total_nodes}")
    print(f"  最大深度: {result.max_depth}")
    print(f"  平均概率: {result.avg_probability:.3f}")
    print("  传播路径:")
    for item in result.to_flat_list():
        if item["from"] is not None:
            print(f"    {item['from']} -> {item['to']}: "
                  f"P={item['probability']:.3f}, "
                  f"delay={item['delay_minutes']:.1f}min, "
                  f"depth={item['depth']}")
    assert result.total_nodes > 1
    print("  [PASS] 通过")

    # 测试 4: 剪枝测试
    print("\n--- 测试 4: 概率剪枝测试 (threshold=0.5) ---")
    result_pruned = propagate_congestion(
        source_section_id=1,
        adjacency_matrix=mock_adj,
        section_speeds=speeds,
        max_depth=3,
        prob_threshold=0.5,
    )
    print(f"  剪枝前节点数: {result.total_nodes}")
    print(f"  剪枝后节点数: {result_pruned.total_nodes}")
    assert result_pruned.total_nodes <= result.total_nodes
    print("  [PASS] 通过")

    # 测试 5: 深度限制测试
    print("\n--- 测试 5: 深度限制 (max_depth=1) ---")
    result_shallow = propagate_congestion(
        source_section_id=1,
        adjacency_matrix=mock_adj,
        section_speeds=speeds,
        max_depth=1,
        prob_threshold=0.2,
    )
    print(f"  max_depth=3 节点数: {result.total_nodes}")
    print(f"  max_depth=1 节点数: {result_shallow.total_nodes}")
    assert result_shallow.total_nodes < result.total_nodes
    print("  [PASS] 通过")

    print("\n" + "=" * 60)
    print("所有测试通过 [PASS]")
    print("=" * 60)
