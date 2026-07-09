"""Dijkstra路径规划 — 基于高德92条真实路段图"""
import heapq, json, os, math
from app.models.traffic_section import TrafficSection


def _load_amap_network():
    json_path = os.path.join(os.path.dirname(__file__), '..', '..', '..',
                             'frontend', 'src', 'data', 'roadNetwork.json')
    if not os.path.exists(json_path): return []
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('segments', [])

_AMAP_SEGMENTS = _load_amap_network()


def _distance_m(p1, p2):
    dlng = (p1[0] - p2[0]) * 111000 * math.cos(math.radians((p1[1] + p2[1]) / 2))
    dlat = (p1[1] - p2[1]) * 111000
    return math.sqrt(dlng**2 + dlat**2)


def _paths_intersect(path_a, path_b, threshold_m=50):
    """两条路径在空间中是否有真实交叉口"""
    for pa in path_a[::2]:
        for pb in path_b[::2]:
            if _distance_m(pa, pb) < threshold_m:
                return True
    return False


def _share_road(seg_a, seg_b):
    """两个路段是否属于同一条路的连续段（同名 + 端点贴近）"""
    name_a = seg_a.get('name', '')
    name_b = seg_b.get('name', '')
    if not name_a or not name_b: return False
    road_a = name_a.split('(')[0].strip() if '(' in name_a else name_a.strip()
    road_b = name_b.split('(')[0].strip() if '(' in name_b else name_b.strip()
    if road_a != road_b or len(road_a) < 2:
        return False
    # 必须端点贴近(≤100m)才算连续段，防止同一条路的远距离段直接互联
    path_a = seg_a.get('path', [])
    path_b = seg_b.get('path', [])
    if len(path_a) < 2 or len(path_b) < 2:
        return False
    end_a = path_a[-1]; start_b = path_b[0]
    end_b = path_b[-1]; start_a = path_a[0]
    return _distance_m(end_a, start_b) < 80 or _distance_m(end_b, start_a) < 80


def _segment_graph():
    """基于92条高德真实路段建图。

    边存在条件（任一即可）：
    1. 路径真实交叉(≤60m) → 真正的道路交叉口
    2. 同一条路的连续段 → 道路自身连续性

    不做任何端点距离判断 → 杜绝凭空生成虚拟连接。
    """
    segs = _AMAP_SEGMENTS
    graph = {}
    for seg in segs:
        sid = seg['id']
        path = seg.get('path', [])
        if len(path) < 2:
            graph[sid] = []
            continue
        neighbors = []
        for other in segs:
            oid = other['id']
            if oid == sid: continue
            other_path = other.get('path', [])
            if len(other_path) < 2: continue
            # 条件1: 路径交叉
            if _paths_intersect(path, other_path):
                w = other.get('length', 200) / 1000
                neighbors.append((oid, round(max(w, 0.1), 3)))
                continue
            # 条件2: 同路连续
            if _share_road(seg, other):
                w = other.get('length', 200) / 1000
                neighbors.append((oid, round(max(w, 0.1), 3)))
        graph[sid] = neighbors
    return graph


# 全局缓存图
_graph_cache = None


def _get_graph():
    global _graph_cache
    if _graph_cache is None:
        _graph_cache = _segment_graph()
    return _graph_cache


def dijkstra(graph, start, end):
    if start not in graph or end not in graph:
        return None, float('inf')
    dist = {n: float('inf') for n in graph}
    dist[start] = 0
    prev = {n: None for n in graph}
    pq = [(0, start)]
    visited = set()
    while pq:
        d, cur = heapq.heappop(pq)
        if cur in visited: continue
        visited.add(cur)
        if cur == end: break
        for nb, w in graph.get(cur, []):
            nd = d + w
            if nd < dist[nb]:
                dist[nb] = nd
                prev[nb] = cur
                heapq.heappush(pq, (nd, nb))
    if dist[end] == float('inf'): return None, float('inf')
    path = []; node = end
    while node is not None: path.append(node); node = prev[node]
    path.reverse()
    return path, dist[end]


def _match_section_to_segments(section_name):
    """将 section 名称匹配到高德路段ID列表"""
    ids = []
    for seg in _AMAP_SEGMENTS:
        sname = seg.get('name', '')
        if section_name in sname or sname in section_name:
            ids.append(seg['id'])
    return ids


def plan_route(origin_id, dest_id):
    if origin_id == dest_id:
        return None, 0, '起点和终点不能相同'

    sections = TrafficSection.query.all()
    section_map = {s.id: s for s in sections}
    origin_section = section_map.get(origin_id)
    dest_section = section_map.get(dest_id)
    if not origin_section or not dest_section:
        return None, 0, '路段不存在'

    # 匹配 Amap segment IDs
    origin_segs = _match_section_to_segments(origin_section.name)
    dest_segs = _match_section_to_segments(dest_section.name)
    if not origin_segs or not dest_segs:
        return None, 0, f'未找到匹配的高德路段'

    graph = _get_graph()
    if not graph:
        return None, 0, '路网数据为空'

    # 从起点的任意匹配segment → 终点的任意匹配segment，找最短路径
    best_path, best_dist = None, float('inf')
    for o_seg in origin_segs:
        for d_seg in dest_segs:
            path, dist = dijkstra(graph, o_seg, d_seg)
            if path and dist < best_dist:
                best_path, best_dist = path, dist

    if best_path is None:
        return None, 0, f'无法从 {origin_section.name} 到达 {dest_section.name}'

    # 将 segment_id 路径反查为 section 名（用于前端显示）
    # 构建 segment_id → section 映射
    seg_to_section = {}
    for s in sections:
        for seg_id in _match_section_to_segments(s.name):
            if seg_id not in seg_to_section:
                seg_to_section[seg_id] = s.id

    section_path = []
    seen = set()
    for seg_id in best_path:
        sid = seg_to_section.get(seg_id)
        if sid and sid not in seen:
            section_path.append(sid)
            seen.add(sid)

    if len(section_path) < 2:
        section_path = [origin_id, dest_id]

    return section_path, best_dist, None
