# 任务看板

> 最后更新：2026-07-12 | Agent协作系统修复完成，心跳+站会已恢复

---

## 🔄 InProgress

| ID | 任务 | Agent | 分支 |
|----|------|-------|------|
| _(无进行中任务)_ | | |

---

## ✅ Done (2026-07-12)

| ID | 任务 | Agent |
|----|------|-------|
| FE-MAIN-01 | Vue Router增加/admin /analyst /traveler三条路由树；路由守卫按role跳转 | agent-frontend-main |
| FE-MAIN-02 | 管理员布局组件(侧边栏+预警角标+顶栏) | agent-frontend-main |
| FE-MAIN-03 | 分析员布局组件(侧边栏+训练状态灯) | agent-frontend-main |
| FE-MAIN-04 | 出行者布局组件(底部Tab+移动端适配) | agent-frontend-main |
| FIX-01~06 | 基础设施修复(CLAUDE.md精简+Agent角色精简+STATE更新+心跳/站会恢复) | agent-lead |
| RBAC-01 | User模型+role字段+JWT role claim | agent-lead |
| RBAC-02 | @role_required装饰器 + optional_role | agent-lead |
| RBAC-03 | GET /auth/me + GET /auth/roles | agent-lead |
| LEAD-DB-01 | 7张新表模型(propagation/profile/alert/signal/emergency/scenario/carbon) | agent-lead |

---

## 📥 Backlog — Phase 3-5: 后续功能

| ID | 任务 | Agent | 阶段 |
|----|------|-------|------|
| ALGO-PROP-01 | 图扩散传播算法(邻接矩阵+条件概率+递归传播树) | agent-algorithm | Phase 3 |
| ALGO-SIG-01 | Webster配时计算 | agent-algorithm | Phase 3 |
| ALGO-CARB-01 | 碳排放估算模型 | agent-algorithm | Phase 3 |
| ALGO-PROF-01 | 常用路线自动识别(K-means+EWMA) | agent-algorithm | Phase 3 |
| ALGO-SCEN-01 | What-If仿真引擎 | agent-algorithm | Phase 3 |
| ALGO-RTE-01 | 三路线生成算法 | agent-algorithm | Phase 3 |
| LEAD-SIG-01 | 信号优化API | agent-lead | Phase 4 |
| LEAD-EMG-01 | 应急调度API | agent-lead | Phase 4 |
| LEAD-PROP-01 | 拥堵传播API | agent-lead | Phase 4 |
| LEAD-SCEN-01 | 场景仿真API | agent-lead | Phase 4 |
| LEAD-CARB-01 | 碳排放API | agent-lead | Phase 4 |
| LEAD-TRV-01~03 | 出行者API(画像+提醒+历史) | agent-lead | Phase 4 |
| LEAD-WS-01 | WebSocket角色分流(3个namespace) | agent-lead | Phase 4 |
| FE-MAIN-06~19 | 14个新增/增强页面 | agent-frontend-main | Phase 5 |
| FE-MAP-01~14 | 14个地图组件+动画 | agent-frontend-map | Phase 5 |
| TEST-01~10 | 全部测试用例 | agent-test-docs | Phase 6 |
| DOCS-01~06 | 文档+PPT+视频 | agent-test-docs | Phase 6 |

---

## ✅ Done（历史记录 — 2026-07-06至2026-07-08）

| ID | 任务 | Agent |
|----|------|-------|
| FEAT-REPLAY-MODE | 回放模式：前端按钮触发回放 | agent-lead |
| FEAT-AMAP-RETRAIN | 高德API真实数据重新训练KNN+RF | agent-lead |
| FEAT-AMAP-SYNC/BACKEND/FRONTEND/SEED | 高德API四件套 | agent-lead |
| BUG-ORPHAN-01 | SUMO孤儿进程防护(PID文件) | agent-lead |
| BUG-SIM-HANG | 仿真卡死根因修复(TraCI移除) | agent-lead |
| FEAT-SIM-REWRITE | 实时仿真业务逻辑重写 | agent-lead |
| FEAT-PREDICTION-REAL | 流量预测真实模型+API | agent-lead |
| FEAT-REAL-NETWORK | 国贸CBD真实路网重建 | agent-lead |
| BUG-OSM-POLYLINE | OSM路网Polyline双修复 | agent-lead |
| FEAT-ANALYSIS-REPORT | 预测分析报告模块 | agent-lead |

---

## 📥 待验收（等待Agent-Judge审查）

| ID | 任务 | 验收标准 | Agent |
|----|------|---------|-------|
| FEAT-SIM-REWRITE | 实时仿真重写 | 启动→运行→暂停→继续→停止 全流程 | agent-lead |
| FEAT-PREDICTION-REAL | 预测真实模型 | using_trained_model:true + RF: MAE=6.16 | agent-lead |
| FEAT-ANALYSIS-REPORT | 预测分析报告 | API /predict/analysis返回5区块 | agent-lead |
