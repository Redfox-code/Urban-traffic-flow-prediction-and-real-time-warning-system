# 六块全栈循环工程系统 — 完整构建计划

---

## 目录

1. [系统概述](#一系统概述)
2. [六大构建块设计](#二六大构建块设计)
3. [文件清单与详细规格](#三文件清单与详细规格)
4. [Agent角色完整定义](#四agent角色完整定义)
5. [运行机制](#五运行机制)
6. [实施步骤](#六实施步骤)
7. [验收标准](#七验收标准)

---

## 一、系统概述

### 1.1 目标

基于 Addy Osmani 的 Loop Engineering 六大构建块，为「城市交通流量预测与实时预警系统」项目构建完整的 AI 循环工程协作系统。

### 1.2 项目背景

| 项 | 值 |
|----|-----|
| 课程 | 智能运输系统设计与集成综合实验 |
| 选题 | 城市交通流量预测与实时预警系统 |
| 小组 | 第二组（5人） |
| 总工期 | 14天（2026年7月1日 – 7月15日） |
| 当前阶段 | 需求分析完成 → 即将进入概要设计(D3-D5) |
| 技术栈 | Flask + Vue 3 + SUMO + Scikit-learn + ECharts + 高德地图 |

### 1.3 五Agent角色映射

| Agent | 对应角色 | 核心职责 |
|-------|---------|---------|
| Agent-Lead | 组长/后端架构师 | 项目管控、Flask后端、API设计、数据库、系统集成 |
| Agent-Algorithm | 算法工程师 | SUMO仿真、KNN/RF模型、数据管道、模型评估 |
| Agent-Frontend-Main | 前端开发（主） | Vue 3核心页面、Element Plus、ECharts、路由 |
| Agent-Frontend-Map | 前端开发（辅）/地图 | 高德地图、WebSocket、响应式、演示视频 |
| Agent-Test-Docs | 测试/文档工程师 | 测试用例、Bug跟踪、三份报告排版、PPT |
| Agent-Judge | 独立审查员 | 不写代码，只审查交付物、独立打分 |

---

## 二、六大构建块设计

### 块1：自动化调度（心跳）

| 机制 | 实现方式 | 频率 | 触发行为 |
|------|---------|------|---------|
| **心跳循环** | `/loop 5m` | 每5分钟 | 扫描 `.claude/board/task-board.md`，发现 `TODO` 且未被阻塞的任务 → 自动唤醒对应Agent执行 |
| **站会** | `/schedule` cron: `*/30 * * * *` | 每30分钟 | Agent-Lead 被唤醒 → 读取所有 agent-log 最后20行 → 统计完成/进行中/阻塞 → 产出站报写入 run-log.md → 必要时重新分配任务 |
| **阶段判定** | 用户手动唤醒 Agent-Judge | 每Sprint结束 | Judge 读取验收条件 → 审查所有交付物 → 独立打分 → 通过/驳回 |

**心跳循环的详细逻辑**：

```
/loop 5m 触发
  │
  ├── 1. 读取 .claude/board/task-board.md
  │     解析 Kanban 表格，提取所有 TODO 状态的任务
  │
  ├── 2. 对每个 TODO 任务：
  │     ├── 检查 BlockedBy 列是否为空
  │     │   ├── 为空 → 可执行，进入步骤3
  │     │   └── 不为空 → 检查阻塞源是否已 Done
  │     │       ├── 已 Done → 可执行
  │     │       └── 未 Done → 跳过，保持 TODO
  │     └── 检查是否有同Agent的InProgress任务
  │         ├── 有 → 跳过（同一Agent一次只做一个任务）
  │         └── 无 → 执行
  │
  ├── 3. 唤醒对应Agent，传入任务ID
  │     Agent 读取自己的角色文件 → 执行任务 → 更新看板 → 写日志
  │
  └── 4. 如果所有TODO都被阻塞，检查是否有超时的InProgress
        └── 超时 > 30分钟 → 在 run-log.md 中标记 ⚠️ ATTENTION
```

**站会的详细逻辑**：

```
/schedule 每30分钟触发
  │
  ├── 1. Agent-Lead 被唤醒
  │
  ├── 2. 收集信息：
  │     ├── 读取 task-board.md 统计各列任务数
  │     ├── 读取每个 agent-log 的最近5条记录
  │     └── 读取 handoff-queue.md 检查未处理的交接
  │
  ├── 3. 产出站报（追加到 run-log.md）：
  │     ## [站报] 2026-07-01 11:00
  │     ### 进度概览
  │     - Todo: 5 | InProgress: 2 | Blocked: 1 | Done: 3
  │     ### 各Agent进展
  │     - Agent-Lead: 总体架构设计中，预计1h完成
  │     - Agent-Algorithm: 等待Leader提供API接口定义（BLOCKED）
  │     - Agent-Frontend-Main: 前端路由设计完成
  │     ...
  │     ### 需要关注
  │     - ⚠️ Agent-Algorithm 已阻塞超过30min
  │
  │ 4. 如果发现已Done的阻塞源 → 将Blocked任务改为TODO
  │
  └── 5. 更新 STATE.md 中的 last_standup 时间戳
```

### 块2：工作树（安全并行）

**使用条件**：仅当多个Agent需要同时修改可能冲突的文件时启用。

**不使用的场景**：
- Agent-Lead 写 `backend/`，Agent-Frontend-Main 写 `frontend/` → 不同目录，无需隔离
- Agent-Test-Docs 写 `docs/` → 与代码目录不冲突

**必须使用的场景**：
- Agent-Lead 和 Agent-Algorithm 同时修改 `backend/app/services/` → 需要隔离
- 两个前端Agent同时修改同一组件 → 需要隔离

**实现方式**：

```bash
# 首先确保项目是git仓库
cd "c:\Users\24924\Desktop\智能运输系统设计与集成综合实验"
git init
git add -A
git commit -m "Initial commit — 需求分析阶段完成"

# Agent以worktree模式启动时
# Claude Code: Agent tool with isolation: "worktree"
# 每个Agent在 .claude/worktrees/agent-xxx/ 下独立工作
# 完成后自动合并回主分支
```

**配置**：在 `.claude/settings.json` 中设置 `worktree.baseRef: "head"`（从当前HEAD分支）

### 块3：技能（持久项目记忆）

**三层记忆架构**：

| 层级 | 文件 | 加载时机 | 内容 |
|------|------|---------|------|
| **L1 全局** | `CLAUDE.md` | 每次会话启动自动加载 | 项目定义、技术栈、构建命令、代码约定、AI辅助规则 |
| **L2 角色** | `.claude/agents/agent-*.md` | Agent被唤醒时加载 | 该Agent的身份、技能、职责边界、依赖、输出规范 |
| **L3 专题** | `.claude/memory/*.md` | 按需加载（通过MEMORY.md索引） | 具体技术规范、架构决策、踩坑记录 |

**L1 CLAUDE.md 更新内容**（在现有基础上增加）：

```markdown
## 十、五Agent循环工程协作模式

### Agent体系
本系统使用6个AI Agent协作推进项目：

| Agent ID | 角色 | 命令唤醒 | 对应目录 |
|----------|------|---------|---------|
| agent-lead | 组长/后端架构师 | @agent-lead | backend/ |
| agent-algorithm | 算法工程师 | @agent-algorithm | algorithm/ |
| agent-frontend-main | 前端开发(主) | @agent-frontend-main | frontend/src/ |
| agent-frontend-map | 前端开发(辅)/地图 | @agent-frontend-map | frontend/src/ |
| agent-test-docs | 测试/文档 | @agent-test-docs | docs/, tests/ |
| agent-judge | 独立审查员 | @agent-judge | 只读，不写代码 |

### 循环节奏
- 心跳：/loop 5m 自动扫描task-board并执行TODO
- 站会：每30分钟 Leader自动汇总进展
- 审查：每Sprint结束 Judge独立打分

### 通信协议
Agent之间不直接对话，通过以下文件通信：
- 任务分配：.claude/board/task-board.md
- 交付交接：.claude/board/handoff-queue.md
- 决策讨论：.claude/board/decisions-log.md
- 各自日志：agent-logs/agent-*-log.md
```

### 块4：MCP连接器

**当前阶段**：项目为本地开发，主要使用 Claude Code 内置工具即可覆盖全部需求：

| 操作类型 | 使用工具 | 说明 |
|----------|---------|------|
| 文件读写 | Write / Edit / Read | 代码和文档 |
| 代码搜索 | Grep / Glob | 查找代码模式 |
| 命令执行 | Bash | pip install, npm run, flask, git |
| 任务管理 | task-board.md | 替代 Linear |
| 通知 | 文件写入 | 替代 Slack — Agent 将消息写入对应文件 |

**后续可扩展**（如课程要求连接真实数据库或在线服务）：
- MySQL MCP Server：让Agent直接查询数据库
- GitHub MCP Server：管理 Issue 和 PR
- 邮件/Slack MCP：真实通知

### 块5：子代理（角色分离）

**核心原则**：写作的Agent不能自己判作业。

```
            ┌──────────────────────┐
            │    Agent-Judge        │
            │   (独立审查员)         │
            │   只读、只评、不写      │
            └──────┬───────────────┘
                   │ 审查打分
    ┌──────────────┼──────────────┐
    │              │              │
    ▼              ▼              ▼
 Agent-Lead   Agent-Algo    Agent-FE-*
 (Implementer) (Implementer) (Implementer)
```

**审查流程**：

```
用户（或心跳）触发 Judge
  │
  ├── 1. Judge 读取 STATE.md → 了解当前阶段
  ├── 2. Judge 读取 task-board.md → 找到 DONE 状态但未审查的任务
  ├── 3. Judge 读取验收条件（从任务描述中提取）
  ├── 4. Judge 逐一检查交付物：
  │     ├── 文件是否存在
  │     ├── 内容是否满足验收条件
  │     ├── 代码风格是否符合规范（读取 naming-conventions.md）
  │     └── 是否有明显的逻辑错误
  │
  ├── 5. Judge 产出审查报告 → 写入 decisions-log.md
  │     每个任务给出：
  │     ✅ APPROVED  — 通过
  │     ⚠️ CHANGES_REQUESTED — 需修改（附具体建议）
  │     ❌ REJECTED — 严重偏离，需重做
  │
  └── 6. Judge 更新 task-board.md：
        ├── APPROVED → 任务移到 Done 列
        └── CHANGES_REQUESTED / REJECTED → 任务移回 TODO，附审查意见链接
```

**Judge Agent 的关键约束**（写在 agent-judge.md 角色文件中）：

```
1. 绝不写代码 — 你的职责是审查，不是修复
2. 绝不修改文件 — 只读模式
3. 逐项对照 — 用验收条件清单打分，不凭感觉
4. 具体反馈 — 不说「代码质量差」，说「traffic_service.py:42 缺少输入校验」
5. 不护短 — 你和Implementer是不同的Agent，不要给面子
```

### 块6：记忆/状态（耐久脊柱）

**三问框架**：

| 问题 | 回答文件 | 更新频率 |
|------|---------|---------|
| 现在在干什么？ | `STATE.md` | 每次阶段变更、每次站会 |
| 上次试了什么、结果如何？ | `run-log.md` + `agent-logs/*.md` | 每次Agent操作后 |
| 有什么在等人类回复？ | `task-board.md` Blocked列 + `STATE.md` 阻塞区 | 实时 |

**STATE.md 结构**：

```markdown
# 项目状态

## 当前
- 阶段：第2阶段 — 概要设计 (D3-D5)
- 开始：2026-07-01
- 预计完成：2026-07-03
- 进度：D3 进行中 (0/5 任务完成)

## 速览
- 全局Todo: 5
- 进行中: 0
- 已阻塞: 0
- 已完成: 0
- 待审查: 0

## 阻塞项
（当前无）

## 时间线
- 2026-07-01 10:00 | 系统初始化 | 五Agent循环系统创建完毕
- 2026-06-30 | 需求分析完成 | 报告+PPT已提交

## 下次站会
2026-07-01 10:30（每30分钟自动触发）
```

**run-log.md 结构**：

```markdown
# 执行日志

> 只追加，不删除。每条记录格式：
> `[时间戳] [来源] [类型] 摘要`
> 来源：🤖AI-Agent | 👤人工 | 🔀混合
> 类型：✅成功 | ❌失败 | ⚠️部分 | 🔄进行中 | 📋站报

---
## 2026-07-01

[10:00] 🤖Agent-Lead | ✅成功 | 系统初始化完成，创建五Agent循环工程体系
[10:30] 📋站报 | D3阶段启动，5个任务待分配
...
```

**task-board.md 结构**（Kanban格式）：

```markdown
# 任务看板

> 状态流转：Backlog → Todo → InProgress → Done → Approved
> 阻塞标记：在 BlockedBy 列填写依赖的任务ID

## 📥 Backlog（待规划）
| ID | 任务 | 阶段 | 优先级 |
|----|------|------|--------|
| BL-01 | 概要设计报告整合 | D5 | P1 |
| BL-02 | Flask项目脚手架搭建 | D6 | P1 |
| ... | ... | ... | ... |

## 📋 Todo（就绪）
| ID | 任务 | Agent | 优先级 | BlockedBy | 预估 |
|----|------|-------|--------|-----------|------|
| D3-T01 | 总体架构设计与模块划分 | agent-lead | P0 | — | 2h |
| D3-T02 | 算法模块设计 | agent-algorithm | P0 | — | 2h |
| D3-T03 | 前端架构与路由设计 | agent-frontend-main | P0 | — | 1.5h |
| D3-T04 | 地图集成方案设计 | agent-frontend-map | P0 | — | 1.5h |
| D3-T05 | 数据库设计与流程图 | agent-test-docs | P0 | D3-T01 | 2h |

## 🔄 InProgress（进行中）
| ID | 任务 | Agent | 开始时间 | 预估剩余 |
|----|------|-------|---------|---------|
| — | — | — | — | — |

## 🚫 Blocked（阻塞）
（当前无）

## ✅ Done（待审查）
（当前无）

## ✔️ Approved（审查通过）
（当前无）
```

---

## 三、文件清单与详细规格

### 共计25个文件

### 3.1 项目根目录（3个）

#### 文件1：`CLAUDE.md` ✅ 已创建，需更新

**更新内容**：在现有CLAUDE.md末尾新增「十、五Agent循环工程协作模式」章节（内容见块3设计）。

#### 文件2：`STATE.md` — 项目全局状态

**初始内容**：见块6设计中的STATE.md结构。初始填充D3阶段信息。

#### 文件3：`run-log.md` — 项目全局执行日志

**初始内容**：
```
# 执行日志

> 格式：`[时间] [来源] [类型] 摘要`

---
## 2026-07-01

[创建时的时间戳] 🤖系统 | ✅成功 | 五Agent循环工程协作系统初始化完成
```

### 3.2 Agent角色文件 `.claude/agents/`（6个）

每个文件约150-200行，包含：身份、技术能力、职责边界、依赖链、输出规范、验收条件、工作指令。

#### 文件4：`agent-lead.md`

```markdown
# Agent-Lead：组长 / 后端架构师

## 身份
- **编号**：Agent #1
- **角色**：组长 / 后端架构师
- **职责**：项目总体规划与进度管控；Flask后端核心架构搭建；RESTful API设计与实现；数据库设计；系统集成与联调；三份报告统稿

## 技术能力
- **精通**：Python Flask、SQLAlchemy ORM、MySQL、RESTful API设计、JWT认证
- **熟悉**：Celery异步任务、Redis、Flask-SocketIO、Git工作流
- **了解**：SUMO交通仿真基础、Vue 3基础、Scikit-learn基础

## 工具集
- Read / Write / Edit：读写项目文件
- Bash：git、pip、flask CLI、pytest
- Grep / Glob：搜索代码

## 职责边界

### ✅ 我负责
- Flask应用工厂模式搭建（`backend/app/`）
- 数据库模型设计（SQLAlchemy ORM，8个核心实体）
- RESTful API蓝图设计（7个路由模块）
- 用户认证（Flask-JWT-Extended，管理员/分析员双角色）
- Celery + Redis异步任务队列搭建
- WebSocket实时推送基础设施（Flask-SocketIO）
- 跨Agent协调（分配任务、站会主持、进度跟踪）
- 概要设计报告 + 详细设计报告的架构章节编写
- 系统集成联调（确保后端-算法-前端三大模块对接）

### ❌ 我不负责（找谁）
- SUMO路网建模、车流配置、仿真运行 → 找 Agent-Algorithm
- KNN/随机森林模型训练与调参 → 找 Agent-Algorithm
- Vue 3前端页面开发 → 找 Agent-Frontend-Main
- ECharts图表配置 → 找 Agent-Frontend-Main
- 高德地图集成、WebSocket前端接收 → 找 Agent-Frontend-Map
- 测试用例编写、报告排版 → 找 Agent-Test-Docs
- 代码质量审查 → 由 Agent-Judge 独立审查

## 依赖链

### 我依赖谁
- Agent-Algorithm：提供模型接口定义（`predict(flow_data) -> prediction`），我才设计预测API
- Agent-Test-Docs：提供数据库E-R图反馈，我才最终定稿数据库设计

### 谁依赖我
- Agent-Algorithm：需要我提供API接口定义，才能设计算法模块对接方案
- Agent-Frontend-Main：需要我提供API文档，才能设计前端数据层
- Agent-Frontend-Map：需要我提供WebSocket事件定义，才能设计地图实时推送
- Agent-Test-Docs：需要我提供数据库Schema，才能编写数据字典和测试用例

## 输出规范

### 代码
- 所有后端代码放在 `backend/` 目录下
- 文件命名：snake_case（如 `traffic_service.py`）
- 类命名：PascalCase（如 `TrafficRecord`）
- API返回格式：`{"code": 200, "data": {...}, "message": "ok"}`
- 遵循 `.claude/memory/api-conventions.md` 规范

### 文档
- 架构设计文档放在 `docs/02-概要设计/` 目录下
- 文件命名：中文描述 + 日期（如 `总体架构设计-20260701.md`）

### 交付流程
1. 完成交付物 → 放入对应目录
2. 更新 `task-board.md`：任务状态 → Done
3. 更新 `handoff-queue.md`：写明交付物路径 + 下游Agent可以开始做什么
4. 写 `agent-logs/agent-lead-log.md`：记录思考过程和关键决策

## 验收条件
我的交付物被 Judge 审查时，需满足：
1. API接口有完整的请求/响应文档（方法、路径、参数、返回值、错误码）
2. 数据库模型包含所有8个核心实体，字段类型和约束明确
3. 项目目录结构清晰，每个模块职责单一
4. 应用入口可启动（`flask run` 不报错）
5. 架构有明确的层次分离（路由层→服务层→数据层）

## 工作指令

当被唤醒时（通过心跳、站会、或用户手动触发），按以下步骤操作：

### 步骤1：定位上下文
1. 读取 `STATE.md` → 确认当前阶段和进度
2. 读取 `CLAUDE.md` → 刷新项目全局记忆
3. 读取 `.claude/board/task-board.md` → 找到分配给 `agent-lead` 的TODO/InProgress任务
4. 读取 `agent-logs/agent-lead-log.md` 最后10行 → 了解自己上次做到哪了

### 步骤2：检查依赖
5. 如果任务有 BlockedBy 标记 → 检查阻塞源是否已Done
   - 已Done → 开始执行
   - 未Done → 更新自己日志，说明等待中，结束本轮

### 步骤3：执行任务
6. 如果是**分配任务**（站会）：
   - 读需求分析报告中的阶段计划
   - 拆分当前阶段的具体可执行任务
   - 更新 task-board.md，为每个Agent分配任务
   
7. 如果是**开发任务**：
   - 先设计（写设计文档）
   - 再实现（写代码）
   - 最后自检（对照验收条件逐项确认）

### 步骤4：记录与交接
8. 更新 `agent-logs/agent-lead-log.md`：记录做了什么、为什么这样做、遇到什么问题
9. 更新 `task-board.md`：任务状态变更
10. 如有产出需要下游Agent使用，更新 `handoff-queue.md`
11. 如有重要技术决策，更新 `.claude/board/decisions-log.md`

### 步骤5：站会主持（如果是站会触发）
12. 收集各Agent最近日志
13. 产出站报写入 `run-log.md`
14. 检查阻塞项是否可解除
15. 更新 `STATE.md` 中的进度统计

## 禁止行为
- ❌ 不要跳过设计直接写代码 — 先写设计文档再动手
- ❌ 不要改其他Agent负责的目录 — 只改 backend/ 和 docs/
- ❌ 不要自己审查自己 — 等待 Judge 独立打分
- ❌ 不要修改 task-board.md 中其他Agent的任务状态 — 只改自己的
- ❌ 不要在代码中硬编码敏感信息 — 用 .env + config.py
```

#### 文件5-8：其他4个Agent角色文件

（采用与Agent-Lead相同的模板结构，根据各自职责填充。具体内容在实施阶段展开编写。）

**各Agent的关键差异点**：

| Agent | 负责目录 | 核心产出 | 不负责（找谁） |
|-------|---------|---------|--------------|
| Agent-Algorithm | `algorithm/` | SUMO路网配置、模型训练脚本、数据预处理、模型评估报告 | 后端API集成（找Lead）、前端可视化（找FE-Main） |
| Agent-Frontend-Main | `frontend/src/` | Vue 3项目、核心页面、路由、ECharts图表 | 地图组件（找FE-Map）、API设计（找Lead） |
| Agent-Frontend-Map | `frontend/src/` | 高德地图集成、WebSocket客户端、热力图、轨迹回放 | 图表组件（找FE-Main）、后端Socket事件（找Lead） |
| Agent-Test-Docs | `docs/`, `backend/tests/` | 测试用例、三份报告排版、PPT、流程图、进度记录 | 代码实现（找Lead/FE）、模型训练（找Algorithm） |

#### 文件9：`agent-judge.md`

```markdown
# Agent-Judge：独立审查员

## 身份
- **编号**：Agent #6
- **角色**：独立审查员（Verifier）
- **职责**：审查所有Agent的交付物，独立打分。不写代码，不修bug，不参与构建。

## 核心约束

### 铁律
1. **绝不写代码** — 你的职责是审查，不是实现
2. **绝不修改文件** — 你对项目文件只有只读权限
3. **逐项对照** — 用验收条件清单逐条检查，不凭感觉
4. **具体反馈** — 不说「代码有问题」，说「traffic_service.py:42 缺少输入类型校验」
5. **不护短** — 你和Implementer是不同的Agent，不存在情面问题

## 审查流程

### 接收审查任务
1. 读取 `STATE.md` → 了解当前阶段
2. 读取 `task-board.md` → 找到 Done 列中待审查的任务
3. 读取任务描述中的验收条件

### 执行审查
对每个待审查任务：
1. 确认交付物文件存在且位置正确
2. 逐项对照验收条件
3. 检查代码风格是否符合规范（读 `.claude/memory/naming-conventions.md`）
4. 检查是否有明显的逻辑缺陷或安全风险
5. 给出审查结论

### 输出审查报告
写入 `.claude/board/decisions-log.md`：
```markdown
## [审查] D3-T01 总体架构设计 — 2026-07-01 14:00

### 审查结果：⚠️ CHANGES_REQUESTED

### 逐项检查
| 验收条件 | 结果 | 说明 |
|----------|------|------|
| 架构图清晰展示三层分离 | ✅ 通过 | — |
| API接口有完整文档 | ⚠️ 需修改 | 缺少错误码定义章节 |
| 数据库8个实体完整 | ✅ 通过 | — |

### 修改建议
1. 在API文档中补充错误码表（参考 api-conventions.md）
2. 在架构图中标注各模块间的数据流方向
```

## 裁决标准

| 判定 | 条件 | 后续操作 |
|------|------|---------|
| ✅ APPROVED | 所有验收条件通过 | task-board → Approved列 |
| ⚠️ CHANGES_REQUESTED | 大部分通过，有少量修改点 | task-board → TODO列，附审查意见 |
| ❌ REJECTED | 交付物缺失或严重偏离需求 | task-board → TODO列，需重新设计和实现 |

## 审查维度

对代码交付物：
1. **完整性**：是否覆盖所有验收条件？
2. **规范性**：命名、格式、注释是否符合团队规范？
3. **正确性**：逻辑是否正确？边界条件是否处理？
4. **安全性**：是否有SQL注入、XSS等明显漏洞？
5. **可维护性**：是否过于复杂？是否有明显的技术债？

对文档交付物：
1. **完整性**：是否覆盖所有要求章节？
2. **准确性**：技术描述是否准确？
3. **可读性**：图表是否清晰？表述是否易懂？

## 禁止行为
- ❌ 绝不修改任何代码文件
- ❌ 绝不说「我自己来改」— 只指出问题，让Implementer改
- ❌ 绝不跳过验收条件 — 每条都要查
- ❌ 不要给出模糊反馈 — 所有问题必须定位到具体文件甚至行
```

### 3.3 共享记忆 `.claude/memory/`（7个）

#### 文件10：`MEMORY.md`

```markdown
# 共享记忆索引

> Agent启动时读取此文件，了解有哪些记忆可用。按需加载具体文件。

- [项目概览](project-overview.md) — 选题名称、小组编号、关键日期、系统定位
- [技术栈](tech-stack.md) — 完整技术选型、版本号、选型理由
- [API规范](api-conventions.md) — RESTful设计规范、统一返回格式、分页标准、错误码
- [命名规范](naming-conventions.md) — Python/Vue/SQL/文件命名规则
- [架构决策](architecture-decisions.md) — 关键ADR，记录为什么选择这个方案
- [踩坑记录](lessons-learned.md) — 已知问题、禁忌清单、上次犯的错不要再犯
```

#### 文件11：`project-overview.md`

```markdown
---
name: project-overview
description: 项目背景、选题名称、小组编号、关键日期、系统定位
metadata:
  type: project
---

# 项目概览

## 基本信息
- **课程**：智能运输系统设计与集成综合实验
- **选题**：城市交通流量预测与实时预警系统
- **小组**：第二组（5人）
- **教师**：hhdong@bjtu.edu.cn
- **提交截止**：2026年7月15日 16:00
- **提交地点**：8号教学楼8407办公室

## 系统定位
构建集 SUMO微观交通仿真、短时流量预测、拥堵实时预警、最优路径规划 于一体的智能交通管理平台。

## 用户角色
1. **交通管理者**：实时路况监控大屏、预警看板、下发调度指令
2. **数据分析员**：预测模型管理、历史数据回溯、模型精度优化

## 六大功能模块
1. 数据采集模块（SUMO仿真 + 检测器数据读取）
2. 流量预测模块（KNN + 随机森林短时预测）
3. 实时监控模块（高德地图路况渲染 + ECharts图表）
4. 拥堵预警模块（WebSocket实时推送 + 规则引擎）
5. 路径规划模块（Dijkstra最优路径）
6. 系统管理模块（用户认证 + 日志管理）

## 阶段时间线
| 阶段 | 日期 | 天数 | 交付物 |
|------|------|------|--------|
| 需求分析 | D1-D2 (6.29-6.30) | 2天 | ✅ 需求分析报告 + PPT |
| 概要设计 | D3-D5 (7.1-7.3) | 3天 | 🔄 概要设计报告 |
| 详细设计+开发 | D6-D10 (7.4-7.8) | 5天 | 系统代码 + 详细设计报告 |
| 收尾交付 | D11-D14 (7.9-7.15) | 5天 | 演示视频 + 最终整合 |
```

#### 文件12：`tech-stack.md`

```markdown
---
name: tech-stack
description: 完整技术栈定义，包含版本号和选型理由
metadata:
  type: reference
---

# 技术栈

## 后端
| 技术 | 版本 | 用途 | 选型理由 |
|------|------|------|----------|
| Python | 3.10+ | 主语言 | 生态丰富，Scikit-learn/Flask支持好 |
| Flask | 3.x | Web框架 | 轻量灵活，适合中小项目 |
| SQLAlchemy | 2.x | ORM | Python最成熟的ORM |
| Flask-JWT-Extended | 4.x | JWT认证 | Flask官方推荐 |
| Celery | 5.x | 异步任务 | 模型定时重训练、批量仿真 |
| Redis | 7.x | 消息队列+缓存 | Celery默认broker |
| Flask-SocketIO | 5.x | WebSocket | 实时预警推送 |

## 算法
| 技术 | 版本 | 用途 |
|------|------|------|
| Scikit-learn | 1.x | KNN回归 + 随机森林 |
| NumPy | 2.x | 矩阵运算 |
| Pandas | 2.x | 数据处理 |
| joblib | 1.x | 模型持久化 |
| SUMO | 1.19+ | 微观交通仿真 |
| TraCI | — | SUMO Python控制接口 |

## 前端
| 技术 | 版本 | 用途 |
|------|------|------|
| Vue 3 | 3.x | 前端框架 |
| Vite | 5.x | 构建工具 |
| Element Plus | 2.x | UI组件库 |
| ECharts | 5.x | 图表可视化 |
| 高德地图 JS API | 2.0 | 地图服务 |
| Pinia | 2.x | 状态管理 |
| Vue Router | 4.x | 路由 |
| Axios | 1.x | HTTP请求 |

## 数据库
| 技术 | 版本 |
|------|------|
| MySQL | 8.x |
```

#### 文件13：`api-conventions.md`

```markdown
---
name: api-conventions
description: RESTful API设计规范、统一返回格式、分页标准、错误码定义
metadata:
  type: reference
---

# API设计规范

## 统一返回格式
```json
{
  "code": 200,
  "data": { ... },
  "message": "ok"
}
```

## HTTP状态码约定
| code | 含义 |
|------|------|
| 200 | 成功 |
| 201 | 创建成功 |
| 400 | 参数错误 |
| 401 | 未认证 |
| 403 | 无权限 |
| 404 | 资源不存在 |
| 500 | 服务器错误 |

## 分页标准
请求：`?page=1&page_size=20`（默认page=1, page_size=20, max_page_size=100）

返回：
```json
{
  "code": 200,
  "data": {
    "items": [...],
    "total": 100,
    "page": 1,
    "page_size": 20
  }
}
```

## API路由前缀 `/api/v1/`

## URL命名：名词复数、层级表达
- `GET /api/v1/sections` — 路段列表
- `GET /api/v1/sections/{id}` — 单个路段
- `GET /api/v1/sections/{id}/traffic` — 某路段流量记录
```

#### 文件14：`naming-conventions.md`

```markdown
---
name: naming-conventions
description: Python/Vue/SQL/文件命名规范
metadata:
  type: reference
---

# 命名规范

## Python
- 文件名：`snake_case`（`traffic_service.py`）
- 类名：`PascalCase`（`TrafficRecord`）
- 函数/变量：`snake_case`（`get_traffic_flow()`）
- 常量：`UPPER_SNAKE_CASE`（`MAX_PAGE_SIZE`）
- 私有方法：`_leading_underscore`

## Vue 3
- 组件文件：`PascalCase.vue`（`TrafficMonitor.vue`）
- 组合式函数：`useCamelCase.js`（`useTrafficData.js`）
- Props：`camelCase`
- Events：`kebab-case`

## SQL / 数据库
- 表名：`snake_case` 复数（`traffic_records`）
- 字段名：`snake_case`（`created_at`）
- 主键：`id`
- 外键：`{table}_id`（`section_id`）
- 时间戳：`created_at`, `updated_at`

## 文件路径
- 统一使用正斜杠 `/`（不用反斜杠）
- 使用 `pathlib.Path` 而非字符串拼接
```

#### 文件15：`architecture-decisions.md`

```markdown
---
name: architecture-decisions
description: 关键架构决策记录，采用ADR格式，记录背景、决策、后果
metadata:
  type: reference
---

# 架构决策记录 (ADR)

## ADR-001：选择Flask而非Django
- **日期**：2026-06-29
- **状态**：已确认
- **背景**：需要轻量级后端，项目工期14天，Django学习成本高
- **决策**：使用Flask 3.x
- **后果**：需自行组装ORM(JWT/Celery等组件，但灵活性更高

## ADR-002：选择KNN+随机森林双模型
- **日期**：2026-06-29
- **状态**：已确认
- **背景**：短时交通流量预测，需要模型可解释且训练快
- **决策**：KNN回归（简单可靠baseline）+ 随机森林（处理非线性特征）
- **后果**：不做深度学习，牺牲一点精度换可解释性和快速迭代

## ADR-003：前后端分离
- **日期**：2026-06-29
- **状态**：已确认
- **背景**：前端Vue 3，后端Flask，需要确定通信方式
- **决策**：完全分离，RESTful API + WebSocket，前端Vite开发代理到后端
- **后果**：需要处理CORS，但开发和部署更灵活

（后续决策在开发过程中持续追加）
```

#### 文件16：`lessons-learned.md`

```markdown
---
name: lessons-learned
description: 项目执行中的踩坑记录、已知问题、禁止重复的错误
metadata:
  type: feedback
---

# 踩坑记录

## 禁忌（不要重复犯错）

1. **不要在预测接口中直接加载模型** — 用单例在启动时预加载
   - 原因：每次请求加载joblib模型导致响应超时
   
2. **不要在前端轮询 `/api/traffic/current`** — 用WebSocket推送
   - 原因：5秒轮询在10个并发用户下后端CPU打满

3. **不要硬编码SUMO路径** — 用config.py环境变量
   - 原因：Windows/Linux路径格式不同

4. **不要在Windows路径中用反斜杠** — 统一正斜杠或pathlib

5. **不要提交数据库密码** — .env + .gitignore

6. **不要跳过设计直接写代码** — 先设计文档 → Judge审查 → 再动手

（持续更新中）
```

### 3.4 任务协调层 `.claude/board/`（3个）

#### 文件17：`task-board.md`

初始内容填充D3阶段的5个任务（见块6设计中的Kanban格式）。

#### 文件18：`handoff-queue.md`

```markdown
# 交付交接队列

> Agent A完成交付物后在此登记，Agent B据此了解可以开始做什么。
> 格式：`[时间] [交付方] → [接收方]：[交付物路径] — [简要说明]`

---

## 当前待处理交接
（当前无）

## 已处理交接
（当前无）

## 交接模板
YYYY-MM-DD HH:MM | Agent-XX → Agent-YY | 交付物路径 | 说明：Agent-YY现在可以开始做XXX了
```

#### 文件19：`decisions-log.md`

```markdown
# 决策日志

> 记录关键技术决策的讨论过程、各方观点、最终决议。
> 格式：`[时间] [标题] — [发起人]`

---

## 决策记录

（当前无。第一个决策将在D3设计阶段产生。）

## 审查记录

（Judge的审查报告将追加在此。）
```

### 3.5 Agent执行日志 `agent-logs/`（5个）

#### 文件20-24：5个Agent日志

每个日志文件初始内容：

```markdown
# [Agent名称] 执行日志

> 记录本Agent的每一次操作、思考过程和关键决策。
> 格式：`[时间戳] [任务ID] [类型] 内容`

---

## 操作记录

[创建时间] | SYSTEM | ✅ 初始化 | Agent #[N] 日志文件创建，等待任务分配。

## 思考轨迹

（Agent每次被唤醒时，在此记录：我理解的任务是什么？我的方案是什么？为什么选择这个方案？有什么风险？）
```

### 3.6 配置更新（1个）

#### 文件25：`.claude/settings.json` 更新

```json
{
  "permissions": {
    "allow": [
      "Bash(npm list *)",
      "Bash(npm install *)",
      "Bash(npm run *)",
      "Bash(pip install *)",
      "Bash(pip list *)",
      "Bash(flask *)",
      "Bash(pytest *)",
      "Bash(git *)",
      "Bash(mkdir *)",
      "Bash(cd *)",
      "Bash(ls *)",
      "Bash(python *)"
    ]
  },
  "worktree": {
    "baseRef": "head"
  }
}
```

---

## 四、Agent角色完整定义

（已在3.2节完整展开，Agent-Lead 和 Agent-Judge 提供了完整规格，其余4个Agent采用相同模板在实施时填充。）

---

## 五、运行机制

### 5.1 系统启动（首次）

```
用户：构建循环工程系统

Claude（本会话）：
1. git init + 初始提交
2. 创建上述25个文件
3. 设置 /loop 5m 心跳
4. 设置 /schedule 每30分钟站会
5. 报告：系统就绪，可以开始D3了
```

### 5.2 Sprint启动（用户触发）

```
用户：Agent-Lead，开始D3概要设计

Agent-Lead 被唤醒：
1. 读 STATE.md → 确认处于D3
2. 读 CLAUDE.md + 需求分析报告 → 理解D3要交付什么
3. 分析任务 → 拆分成5个子任务
4. 更新 task-board.md 的 Todo 列
5. 更新 STATE.md → D3进行中
6. 写 agent-logs/agent-lead-log.md
7. 回复用户：任务已分配，可以逐个唤醒各Agent了
```

### 5.3 心跳自动执行

```
/loop 5m 触发（无需用户干预）：
1. 扫描 task-board.md
2. 发现 Todo + 未阻塞 + Agent空闲 → 自动执行
3. 如果Agent正在忙 → 跳过，等下一轮心跳
```

### 5.4 用户手动推进

```
用户：Agent-Algorithm，完成你的D3任务

Agent-Algorithm 被唤醒：
1. 读角色文件 → 确认身份
2. 读 task-board.md → 找到 D3-T02
3. 检查依赖（可能需要等Leader先完成API设计）
4. 如阻塞 → 写日志说明等待什么 → 告知用户
5. 如就绪 → 执行 → 产出 → 更新看板 → 写日志 → 更新交接队列
```

### 5.5 阶段审查

```
用户：Agent-Judge，审查D3阶段交付物

Agent-Judge 被唤醒：
1. 读 task-board.md → 找到 Done 列
2. 逐项审查 → 写审查报告到 decisions-log.md
3. 通过 → 任务移到 Approved
4. 不通过 → 任务移回 Todo，写明修改建议
5. 告知用户审查结果
```

---

## 六、实施步骤

### Phase 1：基础设施（当前会话）
- [ ] Step 1：`git init` + 初始提交
- [ ] Step 2：创建目录结构（.claude/agents/、.claude/board/、.claude/memory/、agent-logs/）
- [ ] Step 3：更新 CLAUDE.md（新增第十章节）
- [ ] Step 4：更新 .claude/settings.json

### Phase 2：角色文件（当前会话）
- [ ] Step 5：创建 agent-lead.md（完整版 ~200行）
- [ ] Step 6：创建 agent-algorithm.md（完整版 ~150行）
- [ ] Step 7：创建 agent-frontend-main.md（完整版 ~150行）
- [ ] Step 8：创建 agent-frontend-map.md（完整版 ~150行）
- [ ] Step 9：创建 agent-test-docs.md（完整版 ~150行）
- [ ] Step 10：创建 agent-judge.md（完整版 ~120行）

### Phase 3：记忆层（当前会话）
- [ ] Step 11：创建 MEMORY.md
- [ ] Step 12：创建 project-overview.md + tech-stack.md + api-conventions.md + naming-conventions.md + architecture-decisions.md + lessons-learned.md

### Phase 4：协调层和状态层（当前会话）
- [ ] Step 13：创建 task-board.md（预填D3任务）
- [ ] Step 14：创建 handoff-queue.md + decisions-log.md
- [ ] Step 15：创建 STATE.md + run-log.md
- [ ] Step 16：创建 5个 Agent 日志文件

### Phase 5：心跳和站会设置
- [ ] Step 17：`/loop 5m` 心跳
- [ ] Step 18：`/schedule` 每30分钟站会

### Phase 6：验证
- [ ] Step 19：用户手动说「Agent-Lead，开始D3」→ 验证 Leader 正确分配任务
- [ ] Step 20：用户手动唤醒一个Agent → 验证 Agent 正确读取角色并执行

---

## 七、验收标准

系统构建完成后，以下场景应能正常运行：

1. ✅ 用户说「Agent-Lead，开始D3」→ Agent-Lead 正确地读取了角色文件、理解了D3阶段要求、在 task-board 上分配了5个任务
2. ✅ 用户说「Agent-Algorithm，完成你的任务」→ Agent-Algorithm 正确地找到自己在 task-board 上的任务、读取了相关记忆文件、产出了对应交付物
3. ✅ 用户说「Agent-Judge，审查D3」→ Agent-Judge 正确地读取了验收条件、逐项检查了交付物、产出了审查报告
4. ✅ /loop 5m 心跳在运行中，自动发现 TODO 任务并执行（用户可随时查看 run-log.md 确认心跳活动）
5. ✅ 每30分钟 Agent-Lead 自动产出站报到 run-log.md
6. ✅ 用户在 agent-logs/ 中能看到每个 Agent 的完整思考和操作记录
