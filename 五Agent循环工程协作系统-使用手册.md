# 五Agent循环工程协作系统 — 使用手册

> **系统构建日期**：2026-07-01
> **框架来源**：Addy Osmani — Loop Engineering 六大构建块
> **状态**：🟢 系统就绪，等待启动

---

## 一、系统概述

你拥有一个由 **6个AI Agent** 组成的虚拟开发团队，通过「循环工程」方式协作推进「城市交通流量预测与实时预警系统」项目。你是旁观者，通过以下指令观察和管理整个开发过程。

### Agent 阵容

| Agent | 角色 | 负责目录 | 一句话职责 |
|-------|------|---------|-----------|
| **Agent-Lead** | 组长/后端架构师 | `backend/`, `docs/` | 分配任务、主持站会、Flask后端、API设计、系统集成 |
| **Agent-Algorithm** | 算法工程师 | `algorithm/` | SUMO仿真、KNN+随机森林模型、数据管道 |
| **Agent-Frontend-Main** | 前端开发（主） | `frontend/src/` | Vue 3核心页面、Element Plus、ECharts、路由 |
| **Agent-Frontend-Map** | 前端开发（辅）/地图 | `frontend/src/` | 高德地图、WebSocket客户端、热力图、演示视频 |
| **Agent-Test-Docs** | 测试/文档工程师 | `docs/`, `backend/tests/` | 测试用例、Bug跟踪、三份报告排版、PPT |
| **Agent-Judge** | 独立审查员 | 只读 | 审查交付物、独立打分（不写代码） |

---

## 二、核心指令速查

### 2.1 Sprint启动：让组长分配任务

```
Agent-Lead，开始D3概要设计，分配任务给各成员
```

> Agent-Lead 会：读取STATE.md → 理解D3阶段 → 拆分任务 → 写入task-board.md → 告知你任务已分配

### 2.2 逐个唤醒Agent执行任务

```
Agent-Algorithm，完成你的D3任务
Agent-Frontend-Main，完成你的D3任务
Agent-Frontend-Map，完成你的D3任务
Agent-Test-Docs，完成你的D3任务
```

> 每个Agent会：读角色文件 → 读task-board → 检查依赖 → 执行 → 产出交付物 → 写日志

### 2.3 阶段审查：让Judge独立打分

```
Agent-Judge，审查D3阶段交付物
```

> Judge会：读Done列 → 逐项检查验收条件 → 产出审查报告 → APPROVED/CHANGES_REQUESTED/REJECTED

### 2.4 组长汇总阶段成果

```
Agent-Lead，汇总D3阶段成果
```

### 2.5 推进到下一阶段

```
Agent-Lead，开始D4 API接口设计，分配任务
```

---

## 三、完整Sprint工作流（以D3为例）

```
第1步（你）：
  Agent-Lead，开始D3概要设计，分配任务给各成员

第2步（你，逐个）：
  Agent-Algorithm，完成你的D3任务
  Agent-Frontend-Main，完成你的D3任务
  Agent-Frontend-Map，完成你的D3任务

第3步（你）：
  Agent-Test-Docs，完成你的D3任务
  （D3-T05依赖D3-T01，如果在第1步Leader已完成总体架构设计，此任务就绪）

第4步（你）：
  Agent-Judge，审查D3阶段交付物

第5步（你，如果Judge要求修改）：
  Agent-XXX，根据Judge的审查意见修改你的交付物

第6步（你，全部通过后）：
  Agent-Lead，汇总D3阶段成果，推进到D4
```

---

## 四、自动化机制

### 4.1 心跳（每5分钟自动运行）

`/loop 5m` — 无需你干预，系统自动：
- 扫描 `task-board.md` 的TODO列
- 检查阻塞是否解除
- 发现可执行任务 → 自动唤醒对应Agent执行
- 所有TODO被阻塞 → 检查超时InProgress → 标记⚠️

**你可以在 `run-log.md` 中看到心跳活动记录。**

### 4.2 站会（每30分钟自动运行）

`/schedule */30 * * * *` — 无需你干预，Agent-Lead 自动：
- 读取所有Agent日志最新进展
- 统计看板各列任务数
- 产出站报写入 `run-log.md`
- 检查阻塞项是否可解除

**站报格式示例**：
```
## [站报] 2026-07-01 11:00
### 进度概览
- Todo: 2 | InProgress: 2 | Blocked: 1 | Done: 1 | Approved: 0
### 各Agent进展
- Agent-Lead: 总体架构设计中，预计30min完成
- Agent-Algorithm: 算法模块设计进行中
...
```

---

## 五、追踪学习：你可以随时查看的文件

### 想了解全局状态？
- 📍 [STATE.md](STATE.md) — 当前阶段、进度、阻塞项

### 想追某个Agent的思路？
- 📝 [agent-logs/agent-lead-log.md](agent-logs/agent-lead-log.md)
- 📝 [agent-logs/agent-algorithm-log.md](agent-logs/agent-algorithm-log.md)
- 📝 [agent-logs/agent-frontend-main-log.md](agent-logs/agent-frontend-main-log.md)
- 📝 [agent-logs/agent-frontend-map-log.md](agent-logs/agent-frontend-map-log.md)
- 📝 [agent-logs/agent-test-docs-log.md](agent-logs/agent-test-docs-log.md)

### 想看任务分配？
- 📋 [.claude/board/task-board.md](.claude/board/task-board.md) — Kanban看板

### 想看Agent之间如何交接？
- 🔗 [.claude/board/handoff-queue.md](.claude/board/handoff-queue.md)

### 想了解关键技术决策？
- 💬 [.claude/board/decisions-log.md](.claude/board/decisions-log.md) — 决策记录 + Judge审查报告

### 想看完整历史？
- 📜 [run-log.md](run-log.md) — 全局执行日志（含站报）

---

## 六、Agent角色文件速查

每位Agent的完整角色定义（技能、职责边界、依赖链、验收条件）：

| Agent | 角色文件 |
|-------|---------|
| Agent-Lead | [.claude/agents/agent-lead.md](.claude/agents/agent-lead.md) |
| Agent-Algorithm | [.claude/agents/agent-algorithm.md](.claude/agents/agent-algorithm.md) |
| Agent-Frontend-Main | [.claude/agents/agent-frontend-main.md](.claude/agents/agent-frontend-main.md) |
| Agent-Frontend-Map | [.claude/agents/agent-frontend-map.md](.claude/agents/agent-frontend-map.md) |
| Agent-Test-Docs | [.claude/agents/agent-test-docs.md](.claude/agents/agent-test-docs.md) |
| Agent-Judge | [.claude/agents/agent-judge.md](.claude/agents/agent-judge.md) |

---

## 七、共享记忆速查

Agent被唤醒时自动读取这些文件，确保所有Agent基于同一套规范工作：

| 记忆文件 | 内容 |
|---------|------|
| [.claude/memory/project-overview.md](.claude/memory/project-overview.md) | 项目背景、选题、关键日期 |
| [.claude/memory/tech-stack.md](.claude/memory/tech-stack.md) | 技术栈 + 版本 + 选型理由 |
| [.claude/memory/api-conventions.md](.claude/memory/api-conventions.md) | API设计规范 |
| [.claude/memory/naming-conventions.md](.claude/memory/naming-conventions.md) | Python/Vue/SQL命名规范 |
| [.claude/memory/architecture-decisions.md](.claude/memory/architecture-decisions.md) | 关键架构决策(ADR) |
| [.claude/memory/lessons-learned.md](.claude/memory/lessons-learned.md) | 禁忌清单、踩过的坑 |

---

## 八、完整阶段指令序列

### D3 概要设计（7月1日）
```
Agent-Lead，开始D3概要设计，分配任务给各成员
Agent-Algorithm，完成你的D3任务
Agent-Frontend-Main，完成你的D3任务
Agent-Frontend-Map，完成你的D3任务
Agent-Test-Docs，完成你的D3任务
Agent-Judge，审查D3阶段交付物
Agent-Lead，汇总D3阶段成果
```

### D4 API接口设计 + 数据库设计（7月2日）
```
Agent-Lead，开始D4 API接口设计，分配任务
（按需逐个唤醒各Agent）
Agent-Judge，审查D4阶段交付物
Agent-Lead，汇总D4阶段成果
```

### D5 概要设计报告整合 + 开发环境搭建（7月3日）
```
Agent-Lead，开始D5，整合概要设计报告
（各Agent搭建自己的开发环境）
Agent-Test-Docs，整合D3-D5概要设计报告，生成最终Word文档
Agent-Judge，审查概要设计报告
```

### D6-D10 详细设计 + 开发实现（7月4日-8日）
```
Agent-Lead，开始D6，搭建Flask项目脚手架
Agent-Algorithm，开始D6，搭建SUMO路网
Agent-Frontend-Main，开始D6，初始化Vue 3项目
（每天依次类推）
```

### D11-D14 收尾交付（7月9日-15日）
```
Agent-Test-Docs，整合三份最终报告
Agent-Frontend-Map，录制演示视频
Agent-Judge，最终审查所有交付物
```

---

## 九、六大构建块状态

| 块 | Addy概念 | 实现 | 状态 |
|----|----------|------|------|
| 1 | 自动化调度 | `/loop 5m`(job:`9063aed2`) + `/schedule */30 * * * *`(job:`2be09c2b`) + Agent-Judge | 🟢 |
| 2 | 工作树 | git worktree — `isolation: "worktree"` | 🟢 |
| 3 | 技能/SKILL.md | CLAUDE.md(L1) + 6个Agent角色(L2) + 7个共享记忆(L3) | 🟢 |
| 4 | MCP连接器 | Bash/Git/文件权限 + 预留MySQL/GitHub MCP | 🟢 |
| 5 | 子代理 | 5 Implementer + 1 Verifier(Judge) | 🟢 |
| 6 | 记忆脊柱 | STATE.md + run-log.md + task-board + 5个agent-log | 🟢 |

---

## 十、你现在可以开始

系统已完全就绪。说第一句话：

> **Agent-Lead，开始D3概要设计，分配任务给各成员**

然后观察Agent-Lead的完整思考过程。每个Agent的操作都会写入对应日志文件，你可以随时打开阅读，追踪他们的思路和决策。
