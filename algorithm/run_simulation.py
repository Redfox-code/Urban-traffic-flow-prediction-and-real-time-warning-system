"""SUMO 仿真运行脚本 — Agent-Algorithm

用法:
  python run_simulation.py generate  # 生成路网 + 检测器
  python run_simulation.py run       # 运行仿真
  python run_simulation.py all       # 生成 + 运行
  python run_simulation.py run --gui # GUI模式

路网说明:
  - 使用 real_network.nod.xml + real_network.edg.xml 生成国贸CBD真实路网
  - 7条东西向道路 × 5条南北向道路 = 35个交叉口, 116条路段
  - 坐标基于高德地图真实经纬度转换
"""
import os
import sys
import subprocess
import xml.etree.ElementTree as ET
import re

BASE_DIR = os.path.dirname(__file__)
SUMO_DIR = os.path.join(BASE_DIR, 'sumo')
NET_FILE = os.path.join(SUMO_DIR, 'real_network.net.xml')
FALLBACK_NET_FILE = os.path.join(SUMO_DIR, 'city_network.net.xml')
NOD_FILE = os.path.join(SUMO_DIR, 'real_network.nod.xml')
EDG_FILE = os.path.join(SUMO_DIR, 'real_network.edg.xml')
DET_FILE = os.path.join(SUMO_DIR, 'detectors.add.xml')

# 道路前缀 — 用于过滤真实路网中的路段
ROAD_PREFIXES = ('he_', 'hw_', 'vn_', 'vs_')


def generate_network():
    """使用 netconvert 从 real_network.nod.xml + real_network.edg.xml 生成路网"""
    if not os.path.exists(NOD_FILE) or not os.path.exists(EDG_FILE):
        print(f'[SUMO] 未找到真实路网定义文件，回退到 netgenerate 网格...')
        _generate_fallback_network()
        return

    cmd = [
        'netconvert',
        '--node-files=' + NOD_FILE,
        '--edge-files=' + EDG_FILE,
        '--output=' + NET_FILE,
        '--geometry.max-grade=0.08',
        '--geometry.min-radius=5.0',
    ]
    print(f'[SUMO] 使用 real_network.nod.xml + real_network.edg.xml 生成真实路网...')
    subprocess.run(cmd, check=True)
    print(f'[SUMO] 真实路网已生成: {NET_FILE}')


def _generate_fallback_network():
    """回退方案: 使用 netgenerate 生成 6x4 网格路网（写入 city_network.net.xml）"""
    cmd = [
        'netgenerate', '--grid',
        '--grid.number=6', '--grid.length=300',
        '--grid.y-number=4', '--grid.y-length=400',
        '--grid.attach-length=200',
        '--default.lanenumber=3',
        '--output=' + FALLBACK_NET_FILE,
        '--default.speed=13.89',
    ]
    subprocess.run(cmd, check=True)
    print(f'[SUMO] 回退网格路网已生成: {FALLBACK_NET_FILE}')


def _get_net_file():
    """返回实际存在的路网文件（优先 real_network，回退 city_network）"""
    if os.path.exists(NET_FILE):
        return NET_FILE
    return FALLBACK_NET_FILE


def generate_detectors():
    """从生成的 .net.xml 中读取实际 edge ID，自动创建检测器"""
    net_file = _get_net_file()
    tree = ET.parse(net_file)
    root = tree.getroot()
    edges = []
    for edge in root.findall('edge'):
        eid = edge.get('id')
        # 只取道路路段（跳过 internal 连接段）
        if eid and eid.startswith(ROAD_PREFIXES):
            lanes = edge.findall('lane')
            if lanes:
                edges.append((eid, lanes[0].get('id'), float(lanes[0].get('length', '200'))))

    if not edges:
        print('[WARN] 未找到有效边，使用 fallback 检测器配置')
        return

    print(f'[SUMO] 发现 {len(edges)} 条道路，自动生成检测器...')

    # 生成 detectors.add.xml（每个检测器独立元素）
    det_xml = ['<?xml version="1.0" encoding="UTF-8"?>',
               '<additional xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"',
               '            xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/additional_file.xsd">']

    for eid, lane_id, length in edges:
        pos = min(50, length * 0.1)
        end_pos = min(pos + 100, length * 0.9)
        det_xml.append(f'    <laneAreaDetector id="det_{eid}" lanes="{lane_id}" '
                       f'pos="{pos:.0f}" endPos="{end_pos:.0f}" period="900" '
                       f'file="../data/raw/e2_output.xml" friendlyPos="true"/>')

    det_xml.append('</additional>')

    with open(DET_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(det_xml))
    print(f'[SUMO] 检测器已生成: {DET_FILE} ({len(edges)} 个)')


def generate_routes():
    """从 .net.xml 中读取实际 edge ID，自动创建车流文件

    为国贸CBD真实路网生成4个方向的车流:
      - NS: 从最南到最北（通惠河北路主路 → 光华北路）
      - SN: 从最北到最南
      - WE: 从最西到最东（东大桥路 → 西大望路）
      - EW: 从最东到最西
    """
    net_file = _get_net_file()
    tree = ET.parse(net_file)
    root = tree.getroot()

    # 收集所有道路 edge ID，按方向和位置分类
    edge_ids = []
    for edge in root.findall('edge'):
        eid = edge.get('id')
        if eid and eid.startswith(ROAD_PREFIXES):
            edge_ids.append(eid)

    if len(edge_ids) < 4:
        print(f'[WARN] 仅找到 {len(edge_ids)} 条边，使用 fallback')
        edge_ids = [f'edge{i}' for i in range(4)]

    # 从edgeID中选择4个方向的代表道路:
    # 南北向: 使用东三环中路(vn_2_* 和 vs_2_*)
    # 东西向: 使用建国路(he_3_* 和 hw_3_*)
    ns_edges = sorted([e for e in edge_ids if e.startswith('vn_2_')], key=lambda x: int(re.findall(r'\d+', x)[-1]))
    sn_edges = sorted([e for e in edge_ids if e.startswith('vs_2_')], key=lambda x: int(re.findall(r'\d+', x)[-1]), reverse=True)
    we_edges = sorted([e for e in edge_ids if e.startswith('he_3_')], key=lambda x: int(re.findall(r'\d+', x)[1]))
    ew_edges = sorted([e for e in edge_ids if e.startswith('hw_3_')], key=lambda x: int(re.findall(r'\d+', x)[1]), reverse=True)

    # 取首尾边作为 from→to 路径端点
    ns_pair = (ns_edges[0], ns_edges[-1]) if len(ns_edges) >= 2 else (edge_ids[0], edge_ids[1])
    sn_pair = (sn_edges[-1], sn_edges[0]) if len(sn_edges) >= 2 else (edge_ids[1], edge_ids[0])
    we_pair = (we_edges[0], we_edges[-1]) if len(we_edges) >= 2 else (edge_ids[2], edge_ids[3])
    ew_pair = (ew_edges[-1], ew_edges[0]) if len(ew_edges) >= 2 else (edge_ids[3], edge_ids[2])

    routes_xml = ['<?xml version="1.0" encoding="UTF-8"?>',
                  '<routes xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"',
                  '        xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/routes_file.xsd">',
                  '    <vType id="passenger" accel="2.6" decel="4.5" sigma="0.5" length="5.0" maxSpeed="60"/>',
                  '    <vType id="bus" accel="1.5" decel="3.5" sigma="0.5" length="12.0" maxSpeed="40"/>',
                  '    <vType id="truck" accel="1.0" decel="3.0" sigma="0.5" length="10.0" maxSpeed="30"/>']

    # 4个方向的车流 — 1小时仿真
    flows = [
        ('ns', ns_pair[0], ns_pair[1], 2400, 'passenger', 0, 3600),
        ('sn', sn_pair[0], sn_pair[1], 2200, 'passenger', 0, 3600),
        ('we', we_pair[0], we_pair[1], 2600, 'passenger', 0, 3600),
        ('ew', ew_pair[0], ew_pair[1], 2400, 'passenger', 0, 3600),
    ]

    for fid, frm, to, number, vtype, begin, end in flows:
        routes_xml.append(f'    <flow id="{fid}" begin="{begin}" end="{end}" '
                          f'from="{frm}" to="{to}" number="{number}" type="{vtype}"/>')

    routes_xml.append('</routes>')

    route_file = os.path.join(SUMO_DIR, 'city_flows.rou.xml')
    with open(route_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(routes_xml))
    print(f'[SUMO] 车流已生成: {route_file} ({len(edge_ids)} 条边, 4个流向)')


def run_simulation(gui=False):
    """运行 SUMO 仿真"""
    config = os.path.join(SUMO_DIR, 'config.sumocfg')
    executable = 'sumo-gui' if gui else 'sumo'
    cmd = [executable, '-c', config]
    print(f'[SUMO] 运行仿真...')
    subprocess.run(cmd, check=True)
    print('[SUMO] 仿真完成')


if __name__ == '__main__':
    action = sys.argv[1] if len(sys.argv) > 1 else 'run'
    use_gui = '--gui' in sys.argv

    if action == 'generate':
        generate_network()
        generate_routes()
        generate_detectors()
    elif action == 'run':
        run_simulation(gui=use_gui)
    elif action == 'all':
        generate_network()
        generate_routes()
        generate_detectors()
        run_simulation(gui=use_gui)
    else:
        print('Usage: python run_simulation.py [generate|run|all] [--gui]')
