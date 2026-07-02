# 任务看板

> **状态流转**：Backlog → Todo → InProgress → Done → Approved
> **更新时间**：2026-07-02 D6 Sprint启动

---

## 📥 Backlog（D7-D13）

| ID | 任务 | 阶段 | 优先级 | 备注 |
|----|------|------|--------|------|
| BL-D7-01 | 用户认证JWT实现 | D7 | P0 | Agent-Lead |
| BL-D7-02 | SUMO数据解析和预处理 | D7 | P0 | Agent-Algorithm |
| BL-D8-01 | 预测API实现 | D8 | P0 | Agent-Lead |
| BL-D8-02 | KNN模型训练 | D8 | P0 | Agent-Algorithm |
| BL-D9-01 | 随机森林模型训练 | D9 | P0 | Agent-Algorithm |
| BL-D9-02 | Dijkstra路径规划 | D9 | P1 | Agent-Lead |
| BL-D10-01 | 前后端联调 | D10 | P0 | Agent-Lead (协调) |
| BL-D11-01 | Bug修复 | D11 | P0 | 各Agent |
| BL-D12-01 | 演示视频录制 | D12 | P1 | Agent-Frontend-Map |
| BL-D13-01 | 三份报告最终整合 | D13 | P0 | Agent-Test-Docs |

---

## 📋 Todo（就绪待执行）

| ID | 任务 | Agent | 优先级 | BlockedBy | 预估 | 验收条件 |
|----|------|-------|--------|-----------|------|----------|
| D6-T03 | Vue 3项目初始化 | agent-frontend-main | P0 | — | 1.5h | npm run dev启动+Vite+路由+Axios+布局 |
| D6-T04 | 高德地图Key+基础地图 | agent-frontend-map | P0 | D6-T03 | 1h | 地图加载无报错 |
| D6-T05 | 测试框架搭建 | agent-test-docs | P0 | — | 1h | pytest+conftest+fixture可运行 |

---

## 🔄 InProgress（进行中）

（无）

---

## ✅ Done（待审查）

| ID | 任务 | Agent | 完成时间 | 交付物 |
|----|------|-------|---------|--------|
| D6-T01 | Flask项目脚手架搭建 | agent-lead | 2026-07-02 | 28文件，7 Blueprint + 8 Model |
| D6-T02 | SUMO路网搭建 | agent-algorithm | 2026-07-02 | city_flows.rou.xml + detectors.add.xml + config.sumocfg + run_simulation.py |
| D6-T03 | Vue 3项目初始化 | agent-frontend-main | P0 | — | 1.5h | npm run dev启动+Vite+路由+Axios+布局 |
| D6-T04 | 高德地图Key+基础地图 | agent-frontend-map | P0 | D6-T03 | 1h | 地图加载无报错 |
| D6-T05 | 测试框架搭建 | agent-test-docs | P0 | — | 1h | pytest+conftest+fixture可运行 |

---

## 🔄 InProgress（进行中）

（无）

---

## ✅ Done（待审查）

| ID | 任务 | Agent | 完成时间 | 交付物 |
|----|------|-------|---------|--------|
| D6-T01 | Flask项目脚手架搭建 | agent-lead | 2026-07-02 | 28个文件，7 Blueprint + 8 Model + config + utils |

---

## ✔️ Approved（概要设计阶段）

| ID | 任务 | Agent | 审查人 | 通过时间 |
|----|------|-------|--------|---------|
| D3-T01 | 总体架构设计与模块划分 | agent-lead | Agent-Judge | 2026-07-01 |
| D3-T02 | 算法模块设计 | agent-algorithm | Agent-Judge | 2026-07-01 |
| D3-T03 | 前端架构与路由设计 | agent-frontend-main | Agent-Judge | 2026-07-01 |
| D3-T04 | 地图集成方案设计 | agent-frontend-map | Agent-Judge | 2026-07-01 |
| D3-T05 | 数据库设计与E-R图 | agent-test-docs | Agent-Judge | 2026-07-01 |
| D4-T01 | API详细接口规范 | agent-lead | Agent-Judge | 2026-07-02 |
| D4-T02 | 模型接口详细规范 | agent-algorithm | Agent-Judge | 2026-07-02 |
| D4-T03 | 前端API对接+Mock | agent-frontend-main | Agent-Judge | 2026-07-02 |
| D4-T04 | WebSocket消息格式规范 | agent-frontend-map | Agent-Judge | 2026-07-02 |
| D4-T05 | API测试用例设计 | agent-test-docs | Agent-Judge | 2026-07-02 |
| D5-T01 | 概要设计报告整合 | agent-test-docs | Agent-Judge | 2026-07-02 |
