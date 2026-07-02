"""SUMO 仿真运行脚本 — Agent-Algorithm"""
import os
import sys
import subprocess


def generate_network():
    """使用 netgenerate 生成 6×4 网格路网（24路段/12交叉口）"""
    output = os.path.join(os.path.dirname(__file__), 'sumo', 'city_network.net.xml')
    cmd = [
        'netgenerate',
        '--grid',
        '--grid.number=6',           # 6列（南北向道路）
        '--grid.length=300',         # 每格300m → 总长1.8km
        '--grid.y-number=4',         # 4行（东西向道路）
        '--grid.y-length=400',       # 每格400m → 总长1.6km
        '--grid.attach-length=200',  # 出入口连接段200m
        '--default.lanenumber=3',    # 主干道3车道
        '--output=' + output,
        '--default.speed=13.89',     # 50km/h 默认限速
    ]
    print(f'[SUMO] 生成路网: {" ".join(cmd)}')
    subprocess.run(cmd, check=True)
    print(f'[SUMO] 路网已生成: {output}')


def run_simulation(gui=False):
    """运行 SUMO 仿真"""
    config = os.path.join(os.path.dirname(__file__), 'sumo', 'config.sumocfg')
    executable = 'sumo-gui' if gui else 'sumo'
    cmd = [executable, '-c', config]
    print(f'[SUMO] 运行仿真: {" ".join(cmd)}')
    subprocess.run(cmd, check=True)


if __name__ == '__main__':
    action = sys.argv[1] if len(sys.argv) > 1 else 'run'

    if action == 'generate':
        generate_network()
    elif action == 'run':
        run_simulation(gui='--gui' in sys.argv)
    elif action == 'all':
        generate_network()
        run_simulation()
    else:
        print('Usage: python run_simulation.py [generate|run|all]')
