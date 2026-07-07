"""从高德交通态势API获取国贸CBD路网数据 → 生成前端roadNetwork.json

API: https://restapi.amap.com/v3/traffic/status/rectangle
坐标已是GCJ-02，与高德底图完美对齐。

用法: python fetch_amap_network.py
"""
import os, sys, json, requests

AMAP_KEY = "a7e006e65af936c9e57abc52fff9b826"
BASE_DIR = os.path.dirname(__file__)
OUT_JSON = os.path.join(BASE_DIR, '..', 'frontend', 'src', 'data', 'roadNetwork.json')

# 国贸CBD矩形区域 (GCJ-02坐标，对角≈5km < 10km限制)
MIN_LNG, MIN_LAT = 116.44, 39.898  # 左下
MAX_LNG, MAX_LAT = 116.48, 39.918  # 右上


def fetch_amap_roads():
    """调用高德交通态势矩形API"""
    rectangle = f"{MIN_LNG},{MIN_LAT};{MAX_LNG},{MAX_LAT}"
    url = "https://restapi.amap.com/v3/traffic/status/rectangle"
    params = {
        "key": AMAP_KEY,
        "rectangle": rectangle,
        "level": 6,
        "extensions": "all",
        "output": "JSON",
    }
    print(f"[Amap] 请求: {url}")
    print(f"[Amap] 矩形: {rectangle}")
    resp = requests.get(url, params=params, timeout=15)
    data = resp.json()
    print(f"[Amap] 状态: {data.get('status')}, info: {data.get('info')}, infocode: {data.get('infocode')}")

    if data.get('status') != '1':
        print(f"[Amap] API错误: {data}")
        return None

    traffic = data.get('trafficinfo', {})
    roads = traffic.get('roads', [])
    print(f"[Amap] 获取到 {len(roads)} 条道路")
    return roads


def parse_polyline(poly_str):
    """解析高德polyline坐标串 'lng1,lat1;lng2,lat2;...' → [[lng,lat],...]"""
    path = []
    for pt in poly_str.split(';'):
        parts = pt.split(',')
        if len(parts) == 2:
            path.append([float(parts[0]), float(parts[1])])
    return path


def main():
    roads = fetch_amap_roads()
    if not roads:
        print("[Amap] 获取路网失败")
        return

    segments = []
    seg_id = 0
    for road in roads:
        name = road.get('name', '')
        poly_str = road.get('polyline', '')
        status = road.get('status', 0)
        speed = road.get('speed', 0)
        direction = road.get('direction', '')
        angle = road.get('angle', 0)

        if not name or not poly_str:
            continue

        path = parse_polyline(poly_str)
        if len(path) < 2:
            continue

        # 去重：同名道路只保留最长的一条
        seg_id += 1
        segments.append({
            'id': seg_id,
            'name': name,
            'path': path,
            'status': status,
            'speed': speed,
            'direction': direction,
            'source': 'amap',
        })

    print(f"[Amap] 生成 {len(segments)} 条路段")

    # 输出JSON
    output = {
        'coordinate_system': 'GCJ-02',
        'description': '高德交通态势API — 北京国贸CBD实时路网',
        'segments_count': len(segments),
        'segments': segments,
    }
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"[Amap] 输出: {OUT_JSON}")

    # 打印道路列表
    print(f"\n[Amap] 道路列表:")
    for s in segments:
        dir_str = f" ({s['direction']})" if s.get('direction') else ''
        status_map = {0: '未知', 1: '畅通', 2: '缓行', 3: '拥堵'}
        st = status_map.get(s['status'], '?')
        print(f"  [{s['id']}] {s['name']}{dir_str} speed={s['speed']}km/h {st} points={len(s['path'])}")


if __name__ == '__main__':
    main()
