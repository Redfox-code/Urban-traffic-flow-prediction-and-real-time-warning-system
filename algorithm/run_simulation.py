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

    # 生成 detectors.add.xml
    det_xml = ['<?xml version="1.0" encoding="UTF-8"?>',
               '<additional xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"',
               '            xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/additional_file.xsd">',
               '    <e2detector id="e2_output" file="../data/raw/e2_output.xml" period="900">']

    for i, (eid, lane_id, length) in enumerate(edges):
        pos = min(50, length * 0.1)
        det_xml.append(f'        <item id="det_{eid}" lane="{lane_id}" pos="{pos:.0f}"/>')

    det_xml.append('    </e2detector>')
    det_xml.append('</additional>')

    with open(DET_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(det_xml))
    print(f'[SUMO] 检测器已生成: {DET_FILE} ({len(edges)} 个)')


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
        generate_detectors()
    elif action == 'run':
        run_simulation(gui=use_gui)
    elif action == 'all':
        generate_network()
        generate_detectors()
        run_simulation(gui=use_gui)
    else:
        print('Usage: python run_simulation.py [generate|run|all] [--gui]')
