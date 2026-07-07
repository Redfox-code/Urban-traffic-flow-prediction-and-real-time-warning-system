"""从SUMO net.xml提取路网坐标 -> 前端roadNetwork数据

用法: python extract_network_coords.py
"""
import os, sys, json, re, random, math
import xml.etree.ElementTree as ET
from pyproj import Transformer

_utm_to_wgs84 = Transformer.from_crs("EPSG:32650", "EPSG:4326")

BASE_DIR = os.path.dirname(__file__)
OSM_FILE = os.path.join(BASE_DIR, 'sumo', 'osm', 'map.osm')
NET_FILE = os.path.join(BASE_DIR, 'sumo', 'osm', 'osm.net.xml')
OUT_JSON = os.path.join(BASE_DIR, '..', 'frontend', 'src', 'data', 'roadNetwork.json')
OUT_ROU = os.path.join(BASE_DIR, 'sumo', 'osm', 'osm.rou.xml')

KEEP_TYPES = {
    'highway.motorway', 'highway.motorway_link',
    'highway.trunk', 'highway.trunk_link',
    'highway.primary', 'highway.primary_link',
    'highway.secondary', 'highway.secondary_link',
    'highway.tertiary', 'highway.tertiary_link',
    'highway.residential', 'highway.unclassified',
}


def build_way_name_map(osm_path):
    way_names = {}
    print(f'[extract] parse OSM: {osm_path}')
    tree = ET.parse(osm_path)
    for way in tree.getroot().findall('way'):
        wid = way.get('id')
        name = highway = None
        for tag in way.findall('tag'):
            k, v = tag.get('k', ''), tag.get('v', '')
            if k == 'name': name = v
            elif k == 'highway': highway = v
        if name and highway and highway in {
            'motorway', 'motorway_link', 'trunk', 'trunk_link',
            'primary', 'primary_link', 'secondary', 'secondary_link',
            'tertiary', 'tertiary_link', 'residential', 'unclassified',
        }:
            way_names[wid] = name
    print(f'[extract] {len(way_names)} named OSM ways found')
    return way_names


def extract_way_id(edge_id):
    clean = edge_id.lstrip('-')
    if '#' in clean:
        clean = clean.split('#')[0]
    return clean if clean.isdigit() else None


def parse_net_xml(path, way_names):
    tree = ET.parse(path)
    root = tree.getroot()
    loc = root.find('location')
    nx, ny = 0.0, 0.0
    if loc is not None:
        parts = loc.get('netOffset', '0,0').split(',')
        nx, ny = float(parts[0]), float(parts[1])

    edges = []
    for edge in root.findall('edge'):
        eid = edge.get('id')
        etype = edge.get('type', '')
        shape_str = edge.get('shape', '')
        if etype not in KEEP_TYPES or eid.startswith(':'):
            continue
        wid = extract_way_id(eid)
        name = way_names.get(wid, '') if wid else ''
        if not name:
            continue

        shape = []
        if shape_str:
            for pt in shape_str.split():
                x, y = pt.split(',')
                lat, lng = _utm_to_wgs84.transform(float(x) - nx, float(y) - ny)
                shape.append([lng, lat])
        if len(shape) < 2:
            continue

        elength = 0
        for lane in edge.findall('lane'):
            ll = float(lane.get('length', 0))
            if ll > elength: elength = ll
        if elength < 50:
            continue

        edges.append({'id': eid, 'name': name, 'way_id': wid,
                      'type': etype, 'length': elength, 'path': shape})
    return edges


# --- 连通图合并 ---

def _ep(shape):
    """endpoints"""
    return (tuple(shape[0]), tuple(shape[-1]))


def _dist(p1, p2):
    return ((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)**0.5


def _merge_connected(edges):
    """按端点连通关系合并edges，保留原始道路形状(无锯齿)"""
    if len(edges) == 1:
        return list(edges[0]['path']), edges[0]['length']

    n = len(edges)
    shapes = [e['path'] for e in edges]
    TH = 0.001  # ~100m 连通阈值

    # 建连通图
    adj = [[] for _ in range(n)]
    for i in range(n):
        for j in range(i+1, n):
            s0, e0 = _ep(shapes[i])
            s1, e1 = _ep(shapes[j])
            if min(_dist(s0,s1), _dist(s0,e1), _dist(e0,s1), _dist(e0,e1)) < TH:
                adj[i].append(j); adj[j].append(i)

    # 找端点(度<=1) -> 遍历
    visited = [False]*n
    chains = []
    starts = [i for i in range(n) if len(adj[i]) <= 1] or [0]

    for start in starts:
        if visited[start]: continue
        chain = []
        cur = start
        while cur is not None and not visited[cur]:
            visited[cur] = True; chain.append(cur)
            nxt = None
            for nb in adj[cur]:
                if not visited[nb]: nxt = nb; break
            cur = nxt
        if chain: chains.append(chain)

    for i in range(n):
        if not visited[i]: chains.append([i])

    # 逐链拼接shape
    all_merged = []; total_len = 0
    for chain in chains:
        if len(chain) == 1:
            all_merged.append(list(shapes[chain[0]]))
            total_len += edges[chain[0]]['length']
            continue
        result = list(shapes[chain[0]])
        for idx in range(1, len(chain)):
            prev_end = tuple(result[-1])
            curr = shapes[chain[idx]]
            if _dist(prev_end, tuple(curr[-1])) < _dist(prev_end, tuple(curr[0])):
                curr = curr[::-1]
            if _dist(prev_end, tuple(curr[0])) < 0.00001:
                result.extend(curr[1:])
            else:
                result.extend(curr)
        all_merged.append(result)
        total_len += sum(edges[i]['length'] for i in chain)

    merged = all_merged[0]
    for extra in all_merged[1:]:
        merged.extend(extra)
    return merged, total_len


# --- 相似路名合并 ---

def _build_similarity_groups(names):
    adj = {n: [] for n in names}
    for i, n1 in enumerate(names):
        for j in range(i+1, len(names)):
            n2 = names[j]
            if n1 in n2 or n2 in n1:
                adj[n1].append(n2); adj[n2].append(n1)
    visited = set()
    groups = {}
    for name in names:
        if name in visited: continue
        group, q = [], [name]
        while q:
            node = q.pop(0)
            if node in visited: continue
            visited.add(node); group.append(node)
            for nb in adj[node]:
                if nb not in visited: q.append(nb)
        rep = max(group, key=lambda n: (len(n), n))
        groups[rep] = group
    return groups


def generate_segments(edges):
    by_name = {}
    for e in edges:
        by_name.setdefault(e['name'], []).append(e)

    sim_groups = _build_similarity_groups(list(by_name.keys()))
    merged_groups = {}
    for rep, names in sim_groups.items():
        combined = []
        for n in names: combined.extend(by_name[n])
        merged_groups[rep] = combined

    type_rank = {'highway.motorway':1,'highway.motorway_link':2,
                 'highway.trunk':3,'highway.trunk_link':4,
                 'highway.primary':5,'highway.primary_link':6,
                 'highway.secondary':7,'highway.secondary_link':8,
                 'highway.tertiary':9,'highway.tertiary_link':10,
                 'highway.residential':11,'highway.unclassified':12}

    segments = []
    for name, group in merged_groups.items():
        shape, length = _merge_connected(group)
        if len(shape) < 2: continue
        best = max(group, key=lambda e: e['length'])
        segments.append({
            'id': len(segments)+1, 'name': name, 'path': shape,
            'length': length, 'sumo_id': best['id'],
            'type': best['type'], 'merged_from': len(group),
        })
        if len(segments) >= 50: break

    segments.sort(key=lambda s: type_rank.get(s['type'],99))
    for i, s in enumerate(segments): s['id'] = i+1
    return segments


def generate_routes(edges, output_path):
    major = [e for e in edges if e['length']>150] or edges[:10]
    n = min(20, len(major))
    fro, to = major[:n], major[max(1,n//2):max(1,n//2)+n]
    if len(to) < len(fro): to = to*(len(fro)//len(to)+1)
    to = to[:len(fro)]
    lines = ['<?xml version="1.0" encoding="UTF-8"?>','<routes>',
             '    <vType id="passenger" accel="2.6" decel="4.5" sigma="0.5" length="5.0" maxSpeed="60"/>',
             '    <vType id="bus" accel="1.5" decel="3.5" sigma="0.5" length="12.0" maxSpeed="40"/>']
    for i,(f,t) in enumerate(zip(fro,to)):
        v = random.randint(300,800)
        lines.append(f'    <flow id="flow_{i}" begin="0" end="3600" from="{f["id"]}" to="{t["id"]}" number="{v}" type="passenger"/>')
    lines.append('</routes>')
    with open(output_path,'w',encoding='utf-8') as f: f.write('\n'.join(lines))
    print(f'[extract] routes: {output_path} ({len(fro)} flows)')


def main():
    way_names = build_way_name_map(OSM_FILE)
    edges = parse_net_xml(NET_FILE, way_names)
    print(f'[extract] {len(edges)} named edges parsed')
    for i, e in enumerate(sorted(edges, key=lambda x: x['length'], reverse=True)[:10]):
        print(f'  {i+1}. {e["name"]} type={e["type"]} len={e["length"]:.0f}m')

    segments = generate_segments(edges)
    print(f'[extract] {len(segments)} merged segments')

    output = {'coordinate_system': 'WGS-84',
              'description': 'OSM road network',
              'segments_count': len(segments), 'segments': segments}
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON,'w',encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    generate_routes(edges, OUT_ROU)

    for s in segments:
        m = f' ({s["merged_from"]} merged)' if s.get('merged_from',1)>1 else ''
        print(f'  [{s["id"]}] {s["name"]} {s["length"]:.0f}m{m}')


if __name__ == '__main__':
    main()
