"""Dijkstra路径规划服务 — Agent-Lead (D11: 改进为坐标距离)"""
import heapq
import math
from app.models.traffic_section import TrafficSection


def haversine(coord1, coord2):
    """计算两个坐标点之间的距离(km)"""
    lat1, lon1 = math.radians(coord1[1]), math.radians(coord1[0])
    lat2, lon2 = math.radians(coord2[1]), math.radians(coord2[0])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return 6371 * 2 * math.asin(math.sqrt(a))


def build_graph():
    """D11改进: 基于坐标距离构建邻接表（替代D9的ID相邻简化）"""
    sections = TrafficSection.query.all()
    graph = {}
    for s in sections:
        if not s.coordinates or 'start' not in s.coordinates:
            graph[s.id] = []
            continue
        end_coord = s.coordinates.get('end', s.coordinates['start'])
        neighbors = []
        for other in sections:
            if other.id == s.id or not other.coordinates or 'start' not in other.coordinates:
                continue
            start_coord = other.coordinates['start']
            dist = haversine(end_coord, start_coord)
            if dist < 1.0:  # 1km内视为相邻
                neighbors.append((other.id, dist))
        graph[s.id] = neighbors
    return graph


def dijkstra(graph, start, end):
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
    if distances[end] == float('inf'): return None, float('inf')
    path = []; node = end
    while node is not None: path.append(node); node = previous[node]
    path.reverse()
    return path, distances[end]


def plan_route(origin_id, dest_id):
    if origin_id == dest_id: return None, 0, '起点和终点不能相同'
    graph = build_graph()
    if not graph: return None, 0, '路网数据为空'
    path, distance = dijkstra(graph, origin_id, dest_id)
    if path is None: return None, 0, f'无法找到从{origin_id}到{dest_id}的可达路径'
    return path, distance, None
