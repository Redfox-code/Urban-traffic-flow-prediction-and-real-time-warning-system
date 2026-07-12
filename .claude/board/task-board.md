# 任务看板

## ✅ Done (2026-07-06)

| ID | 任务 | Agent |
|----|------|-------|
| BUG-PROG-01 | 进度条卡21%：.gitignore不生效(git rm --cached) | agent-lead |
| BUG-ORPHAN-01 | SUMO孤儿进程防护(PID文件+启动清理) | agent-lead |
| BUG-SUMO-PAUSE | 暂停信号文件残留修复(finally+优雅终止) | agent-lead |
| BUG-SIM-HANG | 仿真卡死根因修复(TraCI移除→纯Python模拟) | agent-lead |
| FEAT-SIM-REWRITE | 实时仿真业务逻辑重写(去掉TraCI) | agent-lead |
| FEAT-PREDICTION-REAL | 流量预测业务填充(真实模型+API) | agent-lead |
| FEAT-REAL-NETWORK | 国贸CBD真实路网重建(SUMO+前端+后端三端对齐) | agent-lead |
| BUG-OSM-POLYLINE | OSM路网Polyline双修复(去重+贯穿) | agent-lead |

## ✅ Done (2026-07-07)

| ID | 任务 | Agent |
|----|------|-------|
| FEAT-AMAP-SYNC | 创建高德数据同步脚本(sync_amap_traffic.py) | agent-lead |
| FEAT-AMAP-BACKEND | 更新traffic API source字段为'amap' | agent-lead |
| FEAT-AMAP-FRONTEND | 更新前端数据源标签(高德实时/模拟) | agent-lead |
| FEAT-AMAP-SEED | 更新seed_data.py国贸CBD道路列表 | agent-lead |

## ✅ Done (2026-07-07)

| ID | 任务 | Agent |
|----|------|-------|
| FEAT-AMAP-RETRAIN | 高德API真实数据重新训练KNN+RF(463条,17路段) | agent-lead |

## ✅ Done (2026-07-12)

| ID | 任务 | Agent |
|----|------|-------|
| ALGO-SIG-01 | Webster信号配时计算(algorithm/signal/webster.py) | agent-algorithm |
| ALGO-CARB-01 | 碳排放估算模型(algorithm/carbon/emission_model.py) | agent-algorithm |
| ALGO-PROP-01 | 图扩散传播算法(algorithm/propagation/diffusion_model.py) | agent-algorithm |
| ALGO-PROF-01 | 常用路线自动识别(algorithm/profile/route_learning.py) | agent-algorithm |
| ALGO-RTE-01 | 三路线生成算法(algorithm/route/three_route_planner.py) | agent-algorithm |
| ALGO-SCEN-01 | What-If仿真引擎(algorithm/scenario/whatif_engine.py) | agent-algorithm |

## ✅ Done (2026-07-08)

| ID | 任务 | Agent |
|----|------|-------|
| FEAT-REPLAY-MODE | 前端"启动实时仿真"按钮触发回放模式: sync_amap_traffic.py replay() 增强(进度+暂停/停止检测), sumo.py /run_realtime 改为 --replay | agent-lead |

## ✅ Done (2026-07-12) — Agent-Frontend-Map

| ID | 任务 | Agent |
|----|------|-------|
| FE-MAP-01 | SectionInfoCard.vue 路段信息卡弹窗(迷你折线图+流量/趋势+3按钮) | agent-frontend-map |
| FE-MAP-02 | TrafficOverlay.vue 路况着色图层增强(4级颜色+30s刷新+WS增量) | agent-frontend-map |
| FE-MAP-03 | PropagationRipple.vue 拥堵传播涟漪动画(Canvas+多源点+渐变) | agent-frontend-map |
| FE-MAP-04 | EmergencyRoute.vue 应急路线渲染(蓝线2Hz闪烁+方向箭头+气泡) | agent-frontend-map |
| FE-MAP-05 | IntersectionTopology.vue 路口拓扑图(Canvas四向+流量+配时对比) | agent-frontend-map |
| FE-MAP-06 | WizardMap.vue 5步向导地图交互(选起点→终点→路线→参数→完成) | agent-frontend-map |
| FE-MAP-07 | PropagationArrows.vue 传播箭头图层(渐变箭头+实线/虚线/点线) | agent-frontend-map |
| FE-MAP-08 | PropagationTree.vue 传播树可视化(ECharts Tree+概率+延迟) | agent-frontend-map |
| FE-MAP-09 | PropagationReplay.vue 历史传播回放(进度条+播放/暂停/快进) | agent-frontend-map |
| FE-MAP-10 | AreaSelector.vue 场景仿真区域选择(框选+点击多选+高亮) | agent-frontend-map |
| FE-MAP-11 | RoutePlanMap.vue 路径规划地图增强(GPS定位+POI搜索+长按选点) | agent-frontend-map |
| FE-MAP-12 | RouteComparison.vue 路线对比可视化(3路线不同样式+拥堵着色) | agent-frontend-map |
| FE-MAP-13 | MobileMapWrapper.vue 移动端地图适配(<768px 55vh+触摸手势+底部面板) | agent-frontend-map |
| FE-MAP-14 | mapSocket.js 增强版WebSocket地图实时更新(指数退避+断连提示) | agent-frontend-map |

## ✅ Approved (2026-07-12)

| ID | 任务 | Agent | 审查结果 |
|----|------|-------|---------|
| FEAT-SIM-REWRITE | 实时仿真重写 | agent-lead | ✅ APPROVED |
| FEAT-ANALYSIS-REPORT | 预测分析报告模块 | agent-lead | ✅ APPROVED |

## 📋 Backlog

| ID | 任务 | 优先级 | Agent | 备注 |
|----|------|--------|-------|------|
| D12-T01 | 演示视频录制 | P1 | agent-test-docs | |
| FEAT-PREDICTION-REAL | 预测真实模型(修正) | P0 | agent-lead | ⚠️ CHANGES_REQUESTED: metrics.json实际值RF_mae=162.52,R²=-0.307，与声称的MAE=6.16,R²=0.13严重不符。需调查训练管道后重新训练 |

## 🔄 InProgress

（空）

## 📥 待验收

（空）
