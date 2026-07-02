"""SUMO 仿真运行脚本 — Agent-Algorithm

用法:
  python run_simulation.py generate  # 生成路网 + 检测器
  python run_simulation.py run       # 运行仿真
  python run_simulation.py all       # 生成 + 运行
  python run_simulation.py run --gui # GUI模式
"""
import os
import sys
import subprocess
import xml.etree.ElementTree as ET

BASE_DIR = os.path.dirname(__file__)
SUMO_DIR = os.path.join(BASE_DIR, 'sumo')
NET_FILE = os.path.join(SUMO_DIR, 'city_network.net.xml')
DET_FILE = os.path.join(SUMO_DIR, 'detectors.add.xml')


def generate_network():
    """使用 netgenerate 生成 6x4 网格路网"""
    cmd = [
        'netgenerate', '--grid',
        '--grid.number=6', '--grid.length=300',
        '--grid.y-number=4', '--grid.y-length=400',
        '--grid.attach-length=200',
        '--default.lanenumber=3',
        '--output=' + NET_FILE,
        '--default.speed=13.89',
    ]
    print(f'[SUMO] 生成路网...')
    subprocess.run(cmd, check=True)
    print(f'[SUMO] 路网已生成: {NET_FILE}')


def generate_detectors():
    """从生成的 .net.xml 中读取实际 edge ID，自动创建检测器"""
    tree = ET.parse(NET_FILE)
    root = tree.getroot()
    edges = []
    for edge in root.findall('edge'):
        eid = edge.get('id')
        # 只取内部道路（非进出口连接段）
        if eid and (eid.startswith('left') or eid.startswith('right') or
                     eid.startswith('top') or eid.startswith('bottom')):
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
    """从 .net.xml 中读取实际 edge ID，自动创建车流文件"""
    tree = ET.parse(NET_FILE)
    root = tree.getroot()
    edge_ids = []
    for edge in root.findall('edge'):
        eid = edge.get('id')
        if eid and (eid.startswith('left') or eid.startswith('right') or
                     eid.startswith('top') or eid.startswith('bottom')):
            edge_ids.append(eid)

    if len(edge_ids) < 4:
        edge_ids = [f'edge{i}' for i in range(4)]  # fallback

    routes_xml = ['<?xml version="1.0" encoding="UTF-8"?>',
                  '<routes xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"',
                  '        xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/routes_file.xsd">',
                  '    <vType id="passenger" accel="2.6" decel="4.5" sigma="0.5" length="5.0" maxSpeed="60"/>',
                  '    <vType id="bus" accel="1.5" decel="3.5" sigma="0.5" length="12.0" maxSpeed="40"/>',
                  '    <vType id="truck" accel="1.0" decel="3.0" sigma="0.5" length="10.0" maxSpeed="30"/>']

    # 取两对相反方向的边作为主干道
    ns_in, ns_out = edge_ids[0], edge_ids[1]
    if len(edge_ids) > 3:
        ew_in, ew_out = edge_ids[2], edge_ids[3]
    else:
        ew_in, ew_out = edge_ids[0], edge_ids[1]

    flows = [
        (0, 7200, 'am'), (7200, 14400, 'md'), (14400, 21600, 'pm')
    ]
    for begin, end, label in flows:
        factor = 1.0 if label == 'am' else (0.5 if label == 'md' else 0.9)
        routes_xml.append(f'    <flow id="{label}_ns" begin="{begin}" end="{end}" '
                          f'from="{ns_in}" to="{ns_out}" number="{int(2400*factor)}" type="passenger"/>')
        routes_xml.append(f'    <flow id="{label}_sn" begin="{begin}" end="{end}" '
                          f'from="{ns_out}" to="{ns_in}" number="{int(2200*factor)}" type="passenger"/>')

    routes_xml.append('</routes>')

    route_file = os.path.join(SUMO_DIR, 'city_flows.rou.xml')
    with open(route_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(routes_xml))
    print(f'[SUMO] 车流已生成: {route_file} ({len(edge_ids)} 条边)')


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
