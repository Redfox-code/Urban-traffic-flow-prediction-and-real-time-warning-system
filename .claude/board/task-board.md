# 任务看板

> **状态流转**：Backlog → Todo → InProgress → Done → Approved
> **阻塞标记**：在 BlockedBy 列填写依赖的任务ID
> **更新时间**：每次状态变更时更新

---

## 📥 Backlog（待规划：后续阶段任务）

| ID | 任务 | 阶段 | 优先级 | 备注 |
|----|------|------|--------|------|
| BL-D5-01 | 概要设计报告整合 | D5 | P1 | 所有Agent设计文档汇总 |
| BL-D6-01 | Flask项目脚手架搭建 | D6 | P0 | 后端初始化 |
| BL-D6-02 | SUMO路网搭建 | D6 | P0 | Agent-Algorithm |
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
---

## 🔄 InProgress（进行中）

| ID | 任务 | Agent | 开始时间 | 预估剩余 |
|----|------|-------|---------|---------|
| — | — | — | — | — |

---

## 🚫 Blocked（阻塞）

| ID | 任务 | Agent | 阻塞原因 | 阻塞于 | 阻塞开始 |
|----|------|-------|---------|--------|---------|
| — | — | — | — | — | — |

---

## ✅ Done（待审查）

| ID | 任务 | Agent | 完成时间 | 交付物 |
|----|------|-------|---------|--------|
| — | — | — | — | — |

---

## ✔️ Approved（审查通过）

| ID | 任务 | Agent | 审查人 | 通过时间 |
|----|------|-------|--------|---------|
| D3-T01 | 总体架构设计与模块划分 | agent-lead | Agent-Judge | 2026-07-01 |
| D3-T02 | 算法模块设计（含数据管道） | agent-algorithm | Agent-Judge | 2026-07-01 |
| D3-T03 | 前端架构与路由设计 | agent-frontend-main | Agent-Judge | 2026-07-01 |
| D3-T04 | 地图集成方案设计 | agent-frontend-map | Agent-Judge | 2026-07-01 |
| D3-T05 | 数据库设计与E-R图 | agent-test-docs | Agent-Judge | 2026-07-01 |

---

## 🐛 Bugs（缺陷）

| ID | 描述 | 严重程度 | 发现者 | 分配给 | 状态 |
|----|------|---------|--------|--------|------|
| — | — | — | — | — | — |
