"""路径规划 — 路段节点图 + 路段裁剪显示

模型: Amap路段=节点，边=同名相邻或空间交叉口。
Dijkstra找最短时间路径(长度÷车速)。
关键优化: 只显示每段路的使用部分，不画整条路段。
"""
import heapq, json, os, math
from app.models.traffic_section import TrafficSection


# ========== 数据加载 ==========

def _load_amap_network():
    json_path = os.path.join(os.path.dirname(__file__), '..', '..', '..',
                             'frontend', 'src', 'data', 'roadNetwork.json')
    if not os.path.exists(json_path): return []
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f).get('segments', [])

_AMAP = _load_amap_network()

def _dist(p1, p2):
    dlng = (p1[0] - p2[0]) * 111000 * math.cos(math.radians((p1[1] + p2[1]) / 2))
    dlat = (p1[1] - p2[1]) * 111000
    return math.sqrt(dlng**2 + dlat**2)

def _path_len_km(path):
    if len(path) < 2: return 0.05
    return max(sum(_dist(path[i-1], path[i]) for i in range(1, len(path))) / 1000, 0.01)


# ========== 图构建 ==========

def _same_road(a, b):
    """是否同一条路"""
    na, nb = a.get('name',''), b.get('name','')
    if not na or not nb: return False
    def root(n):
        import re; n = re.sub(r'[（(][^)）]*[)）]', '', n)
        for c in '东西南北中主辅内外': n = n.replace(c, '')
        return n.strip()
    return root(na) == root(nb) and len(root(na)) >= 2

def _endpoint_dist(a, b):
    pa, pb = a.get('path',[]), b.get('path',[])
    if len(pa) < 2 or len(pb) < 2: return float('inf')
    return min(_dist(pa[0], pb[0]), _dist(pa[0], pb[-1]),
               _dist(pa[-1], pb[0]), _dist(pa[-1], pb[-1]))

def _cross(pa, pb, th=50):
    """两条路径空间距离是否<th米"""
    for i in range(0, len(pa), max(1, len(pa)//20)):
        for j in range(0, len(pb), max(1, len(pb)//20)):
            if _dist(pa[i], pb[j]) < th: return True
    return False

def _build_graph():
    segs = _AMAP; graph = {}
    for s in segs:
        sid = s['id']; p = s.get('path',[])
        if len(p) < 2: graph[sid] = []; continue
        nbs = []
        for o in segs:
            oid = o['id']
            if oid == sid: continue
            op = o.get('path',[]);
            if len(op) < 2: continue
            # 同名路段：端点相邻(<200m) 或 路径接近(<50m任意点)
            same_road_connected = _same_road(s, o) and (
                _endpoint_dist(s, o) < 200 or _cross(p, op, 50))
            if same_road_connected or _cross(p, op):
                spd = max(float(o.get('speed', 30) or 30), 5)
                cost = _path_len_km(op) / spd + 0.005  # +0.005跳惩罚，偏好少跳路径
                nbs.append((oid, round(cost, 5)))
        graph[sid] = nbs
    return graph

_graph = None
def _get_graph():
    global _graph
    if _graph is None: _graph = _build_graph()
    return _graph


# ========== Dijkstra ==========

def _dijkstra(start, end):
    g = _get_graph()
    if start not in g or end not in g: return None, float('inf')
    dist = {n: float('inf') for n in g}; dist[start] = 0
    prev = {n: None for n in g}
    pq = [(0, start)]; vis = set()
    while pq:
        d, cur = heapq.heappop(pq)
        if cur in vis: continue
        vis.add(cur)
        if cur == end: break
        for nb, w in g.get(cur, []):
            nd = d + w
            if nd < dist[nb]: dist[nb] = nd; prev[nb] = cur; heapq.heappush(pq, (nd, nb))
    if dist[end] == float('inf'): return None, float('inf')
    path = []; node = end
    while node is not None: path.append(node); node = prev[node]
    path.reverse()
    return path, dist[end]


# ========== 路段裁剪 ==========

def _seg_by_id(sid):
    for s in _AMAP:
        if s['id'] == sid: return s
    return None

def _find_nearest_point(path, target):
    """找路径上离target最近的点索引"""
    best_i, best_d = 0, float('inf')
    for i, pt in enumerate(path):
        d = _dist(pt, target)
        if d < best_d: best_d = d; best_i = i
    return best_i

def _trim_segment_path(seg_id, entry_pt, exit_pt):
    """裁剪路段路径：只保留entry到exit之间的部分"""
    seg = _seg_by_id(seg_id)
    if not seg: return [], 0
    full = seg.get('path', [])
    if len(full) < 2: return [], 0
    # 找到最近entry和exit的索引
    ei = _find_nearest_point(full, entry_pt)
    xi = _find_nearest_point(full, exit_pt)
    if ei > xi: ei, xi = xi, ei  # 确保方向
    # 扩展2个点确保覆盖
    ei = max(0, ei - 2)
    xi = min(len(full) - 1, xi + 2)
    trimmed = full[ei:xi+1]
    return trimmed, _path_len_km(trimmed)


# ========== 匹配 ==========

def _match_name(section_name):
    ids = []
    def norm(n):
        import re; n = re.sub(r'[（(][^)）]*[)）]', '', n)
        for c in '东西南北': n = n.replace(c, '')
        return n.strip()
    ns = norm(section_name)
    for seg in _AMAP:
        sn = seg.get('name','')
        if section_name == sn: ids.append(seg['id']); continue
        if section_name in sn or sn in section_name: ids.append(seg['id']); continue
        if ns and norm(sn) and (ns == norm(sn) or ns in norm(sn) or norm(sn) in ns): ids.append(seg['id'])
    return ids

def _section_center_point(section):
    """DB路段的中心坐标"""
    c = section.coordinates
    if not c: return None
    wp = c.get('waypoints', []) or c.get('path', [])
    if not wp: return None
    return wp[len(wp) // 2]


def _match_coord(section):
    c = section.coordinates
    if not c: return []
    wp = c.get('waypoints',[]) or c.get('path',[]);
    if not wp: return []
    ct = wp[len(wp)//2]
    best, bd = None, float('inf')
    for seg in _AMAP:
        for pt in seg.get('path',[])[::2]:
            d = _dist(ct, pt)
            if d < bd: bd = d; best = seg['id']
    return [best] if best and bd < 500 else []

def _match_best(section):
    """综合匹配：名字匹配和坐标兜底合并，按距离排序取最近的5个"""
    center = _section_center_point(section)
    by_name = _match_name(section.name)
    by_coord = _match_coord(section)
    all_ids = list(set(by_name + by_coord))
    if not all_ids:
        return []
    if not center:
        return all_ids[:5]
    # 按坐标距离排序
    scored = []
    for sid in all_ids:
        seg = _seg_by_id(sid)
        if not seg: continue
        best_d = float('inf')
        for pt in seg.get('path', [])[::2]:
            d = _dist(center, pt)
            if d < best_d: best_d = d
        scored.append((best_d, sid))
    scored.sort()
    return [sid for _, sid in scored[:5]]


# ========== 主入口 ==========

def plan_route(origin_id, dest_id):
    if origin_id == dest_id:
        return None, 0, [], 0, '起点和终点不能相同'

    sections = TrafficSection.query.all()
    sm = {s.id: s for s in sections}
    os = sm.get(origin_id); ds = sm.get(dest_id)
    if not os or not ds: return None, 0, [], 0, '路段不存在'

    # 匹配：名字+坐标综合排序，优先取最近的Amap路段
    osegs = _match_best(os)
    dsegs = _match_best(ds)
    if not osegs or not dsegs:
        return None, 0, [], 0, f'未找到路网匹配: {os.name} 或 {ds.name}'

    # 找路径
    best_path, best_cost = None, float('inf')
    for o in osegs[:5]:
        for d in dsegs[:5]:
            p, c = _dijkstra(o, d)
            if p and c < best_cost: best_path, best_cost = p, c

    if not best_path:
        return None, 0, [], 0, f'无法从 {os.name} 到达 {ds.name}'

    # 确定起点/终点在路段上的实际位置
    orig_center = _section_center_point(os)
    dest_center = _section_center_point(ds)

    # 裁剪每条路段——只显示使用的部分
    trimmed = []
    for i, sid in enumerate(best_path):
        seg = _seg_by_id(sid)
        if not seg: continue
        full = seg.get('path', [])

        if len(best_path) == 1:
            # 起终点在同一路段：从起点中心到终点中心
            sub, lkm = _trim_segment_path(sid,
                orig_center or full[0],
                dest_center or full[-1])
        elif i == 0:
            # 第一段（起点段）：从section中心到与下一段的连接点
            start_pt = _nearest_point_on_segment(sid, orig_center) if orig_center else full[0]
            next_seg = _seg_by_id(best_path[1])
            end_pt = _connection_point(seg, next_seg)
            sub, lkm = _trim_segment_path(sid, start_pt, end_pt)
        elif i == len(best_path) - 1:
            # 最后一段（终点段）：从上一段连接点到section中心
            prev_seg = _seg_by_id(best_path[i-1])
            start_pt = _connection_point(prev_seg, seg)
            end_pt = _nearest_point_on_segment(sid, dest_center) if dest_center else full[-1]
            sub, lkm = _trim_segment_path(sid, start_pt, end_pt)
        else:
            # 中间段：从上一段连接点到下一段连接点
            prev_seg = _seg_by_id(best_path[i-1])
            next_seg = _seg_by_id(best_path[i+1])
            start_pt = _connection_point(prev_seg, seg)
            end_pt = _connection_point(seg, next_seg)
            sub, lkm = _trim_segment_path(sid, start_pt, end_pt)

        if len(sub) >= 2:
            trimmed.append({
                'seg_id': sid,
                'name': seg.get('name', str(sid)),
                'path': sub,
                'length_km': round(lkm, 3),
            })

    # 合并连续同名路段
    def _road_root(n):
        for c in '东西南北中主辅内外': n = n.replace(c, '')
        return n.strip()
    merged = []
    for e in trimmed:
        if merged and _road_root(e['name']) == _road_root(merged[-1]['name']) and len(_road_root(e['name'])) >= 2:
            merged[-1]['path'] = merged[-1]['path'] + e['path'][1:]
            merged[-1]['length_km'] = round(merged[-1]['length_km'] + e['length_km'], 3)
            merged[-1]['seg_id'] = e['seg_id']  # use latest seg_id
        else:
            merged.append(dict(e))
    trimmed = merged

    # 总距离
    total_dist = round(sum(e['length_km'] for e in trimmed), 2)
    total_time = max(1, round(total_dist / 30 * 60))

    # seg -> section 映射
    seg_to_sec = {}
    for s in sections:
        for sid in _match_best(s):
            if sid not in seg_to_sec: seg_to_sec[sid] = s.id

    path_detail = []
    seen = set()
    for e in trimmed:
        sid = e['seg_id']
        if sid and sid not in seen:
            s = sm.get(seg_to_sec.get(sid))
            path_detail.append({
                'section_id': seg_to_sec.get(sid, origin_id),
                'name': s.name if s else e['name'],
                'length': e['length_km'],  # 用裁剪后的实际长度
                'coordinates': e['path'],
            })
            seen.add(sid)

    if len(path_detail) < 2:
        path_detail = [
            {'section_id': origin_id, 'name': os.name, 'length': float(os.length), 'coordinates': []},
            {'section_id': dest_id, 'name': ds.name, 'length': float(ds.length), 'coordinates': []},
        ]

    return path_detail, total_dist, trimmed, total_time, None


def _connection_point(seg_a, seg_b):
    """找两个路段之间的连接点（最近点对的中点）"""
    pa = seg_a.get('path', []); pb = seg_b.get('path', [])
    if len(pa) < 2 or len(pb) < 2: return pa[-1] if pa else [0,0]
    best_d = float('inf'); best_pt = pa[-1]
    # 每条路径取最多15个采样点
    step_a = max(1, len(pa) // 15)
    step_b = max(1, len(pb) // 15)
    for i in range(0, len(pa), step_a):
        for j in range(0, len(pb), step_b):
            d = _dist(pa[i], pb[j])
            if d < best_d:
                best_d = d
                best_pt = [(pa[i][0]+pb[j][0])/2, (pa[i][1]+pb[j][1])/2]
    return best_pt


def _nearest_point_on_segment(seg_id, target_pt):
    """找到路段上离target最近的点坐标"""
    seg = _seg_by_id(seg_id)
    if not seg: return target_pt
    path = seg.get('path', [])
    if len(path) < 2: return target_pt
    best_i, best_d = 0, float('inf')
    for i, pt in enumerate(path):
        d = _dist(pt, target_pt)
        if d < best_d: best_d = d; best_i = i
    return path[best_i]
