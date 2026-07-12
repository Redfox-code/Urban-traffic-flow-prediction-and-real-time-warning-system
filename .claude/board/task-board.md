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

## ✅ Done (2026-07-12) — Agent-Test-Docs

| ID | 任务 | 用例数 | Agent |
|----|------|--------|-------|
| TEST-01 | RBAC权限测试 (test_rbac.py) | 13 | agent-test-docs |
| TEST-02 | 信号优化API测试 (test_signal.py) | 9 | agent-test-docs |
| TEST-03 | 碳排放API测试 (test_carbon.py) | 9 | agent-test-docs |
| TEST-04 | 出行者API测试 (test_traveler.py) | 13 | agent-test-docs |
| TEST-05 | 平台API测试 (test_platform.py) | 21 | agent-test-docs |
| DOCS-01 | 更新run-log.md 7月12日日志 | — | agent-test-docs |
| DOCS-02 | 更新task-board.md 统一所有已完成任务 | — | agent-test-docs |

| ID | 任务 | Agent | 审查结果 |
|----|------|-------|---------|
| FEAT-SIM-REWRITE | 实时仿真重写 | agent-lead | ✅ APPROVED |
| FEAT-ANALYSIS-REPORT | 预测分析报告模块 | agent-lead | ✅ APPROVED |

| FE-MAP-ROUTE | RoutePlanMap 路线渲染(routeData prop + Polyline + 起终点/途经点标记 + setFitView) | agent-frontend-map |

## ✅ Done (2026-07-13)

| ID | 任务 | Agent |
|----|------|-------|
| FE-MODEL-CHART | ModelsView增加模型评估可视化图表（KNN vs RF柱状图 + 预测vs实际散点图） | agent-frontend-main |

## 🔄 InProgress

（空）

## ✅ Done (2026-07-13)

| ID | 任务 | Agent |
|----|------|-------|
| FE-MODEL-CHART | ModelsView增加模型评估可视化图表（KNN vs RF柱状图 + 预测vs实际散点图） | agent-frontend-main |

## ✅ Done (2026-07-12)

| ID | 任务 | Agent |
|----|------|-------|
| FIX-LOGIN-01 | 登录页+注册页增加角色选择下拉框，按角色跳转首页 | agent-lead |
| FE-ANALYST-01~05 | 分析员5个页面填充真实内容(模型管理/拥堵传播/碳排放/数据探索/场景仿真) — 对接后端API+ECharts | agent-frontend-main |
| FE-TRAVELER-01 | 路径规划页(RoutePlanView): 移动端优先+GPS+地图选点+3路线+拥堵度+收藏 | agent-frontend-main |
| FE-TRAVELER-02 | 我的出行页(MyTripsView): 路线卡片网格+路况指示条30s轮询+ECharts时段分布 | agent-frontend-main |
| FE-TRAVELER-03 | 出行提醒页(AlertsView): 通勤开关+无限滚动+类型徽标+未读蓝色竖线标记已读 | agent-frontend-main |
| FE-TRAVELER-04 | 历史记录页(HistoryView): 查询列表+重新加载+单条删除+清空全部 | agent-frontend-main |

## ✅ Done (2026-07-13)

| ID | 任务 | Agent |
|----|------|-------|
| ALGO-EVAL-01 | 新增评估数据API端点 GET /api/v1/predict/evaluation | agent-algorithm |

## 📋 Backlog

| ID | 任务 | 优先级 | Agent | 备注 |
|----|------|--------|-------|------|
| D12-T01 | 演示视频录制 | P1 | agent-test-docs | |
| FE-ADMIN-01~05 | 管理员5个页面填充真实内容 | P2 | agent-frontend-main | 后续 |

## ✅ Done (2026-07-12) — Bug修复

| ID | 任务 | Agent | 审查结果 |
|----|------|-------|---------|
| FEAT-PREDICTION-REAL | 预测真实模型(修正) — 移除硬编码MAE默认值(6.16/5.34)，统一从metrics.json动态读取；增强模型可靠性建议说明 | agent-lead | ✅ 已修复 (91/91测试通过) |

## 🔄 InProgress

（空）

## 📥 待验收

（空）
