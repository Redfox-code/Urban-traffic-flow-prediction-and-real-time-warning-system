"""Dijkstra路径规划服务 — Agent-Lead"""
import heapq
from app.models.traffic_section import TrafficSection


def build_graph():
    """从路段构建邻接表图（基于坐标相邻关系简化）"""
    sections = TrafficSection.query.all()
    graph = {}
    for s in sections:
        neighbors = []
        # 简化：基于ID相邻（实际应基于坐标拓扑）
        for other in sections:
            if other.id != s.id and abs(other.id - s.id) <= 6:
                dist = float(s.length + other.length) / 2
                neighbors.append((other.id, dist))
        graph[s.id] = neighbors
    return graph


def dijkstra(graph, start, end):
    """Dijkstra最短路径算法"""
    if start not in graph or end not in graph:
        return None, float('inf')
    distances = {node: float('inf') for node in graph}
    distances[start] = 0
    previous = {node: None for node in graph}
    pq = [(0, start)]
    visited = set()

    while pq:
        current_dist, current = heapq.heappop(pq)
        if current in visited: continue
        visited.add(current)
        if current == end: break
        for neighbor, weight in graph.get(current, []):
            distance = current_dist + weight
            if distance < distances[neighbor]:
                distances[neighbor] = distance
                previous[neighbor] = current
                heapq.heappush(pq, (distance, neighbor))

    if distances[end] == float('inf'):
        return None, float('inf')

    path = []
    node = end
    while node is not None:
        path.append(node)
        node = previous[node]
    path.reverse()
    return path, distances[end]


def plan_route(origin_id, dest_id):
    """规划路径，返回(path, distance, error)"""
    if origin_id == dest_id:
        return None, 0, '起点和终点不能相同'
    graph = build_graph()
    if not graph:
        return None, 0, '路网数据为空'
    path, distance = dijkstra(graph, origin_id, dest_id)
    if path is None:
        return None, 0, f'无法找到从{origin_id}到{dest_id}的可达路径'
    return path, distance, None
