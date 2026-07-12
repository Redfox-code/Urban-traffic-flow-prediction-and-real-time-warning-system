# CLAUDE.md — 城市交通流量预测与实时预警系统

> **作用**：每次 AI Agent 启动时自动加载。精简版——只保留每次必读的核心内容。

---

## ⚠️ 核心AI协作规则

> **协调者（Claude）不得跳过 Agent 直接修改代码。即使一行改动，也必须走 Agent 流程。**
>
> **每次输出时必须标明当前所处阶段**：`[阶段一 需求分析]` / `[阶段二 任务执行]` / `[阶段三 PR审核]` / `[阶段四 审查验收]` / `[阶段五 发布上线]`

### 🚫 禁止自主改代码（最高优先级铁律）

**在完成以下全部步骤之前，协调者（Claude）/ Agent-Lead 绝对不得直接修改任何代码文件：**

1. ❌ **禁止未分析就动手** — 必须先读代码确认问题，写分析日志到 `agent-logs/agent-lead-log.md`
2. ❌ **禁止未分配任务就动手** — 必须先在 `.claude/board/task-board.md` 创建任务，写清 ID/描述/Agent
3. ❌ **禁止跨Agent领地** — Agent-Lead 只能改 `backend/`，不得改 `frontend/`（那是Agent-Frontend-Main/Map的领地）
4. ❌ **禁止跳过Git Flow** — 必须先 `git checkout -b feature/{agent-name}/{task-id}`，不得在 dev 上直接 commit

**违反任何一条 = 流程违规，必须立即停止，回溯补全所有步骤后才能继续。**

**每个任务的标准路径**：
```
用户提出需求
 → 阶段一：读代码 → 写分析日志 → task-board创建任务 → 分配Agent
 → 阶段二：Agent从dev拉feature分支 → 编码 → 验证 → 写日志 → push → PR
 → 阶段三：Agent-Lead审核PR → 全量测试 → --no-ff合并到dev
 → 阶段四：Agent-Judge审查 → 等用户确认测试通过
```

---

## 🔴 改代码前强制自检（每次 Write/Edit/Bash 修改文件前必答）

**协调者（Claude）/ Agent-Lead 在修改任何文件之前，必须先用以下三个问题自问：**

| # | 问题 | 检查方法 |
|---|------|---------|
| 1 | 📝 分析日志写了吗？ | `agent-logs/agent-lead-log.md` 最后一条是本次的 🎯 需求分析？ |
| 2 | 📋 task-board有任务吗？ | `.claude/board/task-board.md` 的 InProgress 列有这个任务ID？ |
| 3 | 👤 分配给正确的Agent了吗？ | 任务在正确Agent的名下？改的文件在该Agent的目录范围内？ |

**三个答案全部是 YES 才能动手。任何一个 NO → 停止，补全缺失步骤。**

> 历史教训：同一问题（传播树）被 Agent-Lead 连改 4 次，每次都跳过上述三步。见 [[lessons-learned]](.claude/memory/lessons-learned.md) #11。

---

## 完整开发流程：从用户需求到代码上线

### 阶段一：需求分析（Agent-Lead）

```
用户提出需求
    │
    ▼
Agent-Lead 读取分析需求
    │
    ├── 读取 STATE.md 了解当前进度
    ├── 读取 task-board.md 了解现有任务
    │
    ├── ⚠️ 先写分析日志（必须，不写完不分配任务）
    │     在 agent-logs/agent-lead-log.md 追加:
    │     🎯 需求原文 + 🔍 现状分析（读相关代码，不要凭空猜测）
    │     📊 任务拆分表(ID/描述/Agent/优先级/预估)
    │     🔗 依赖关系 + 📝 执行策略 + 🎯 关键决策
    │
    ├── 写入 task-board.md（Backlog → Todo列）
    │   格式: | ID | 任务描述 | Agent | 依赖 | 分支 |
    │
    └── @唤醒 对应Agent开始工作
```

> **铁律**：Agent-Lead 在完成需求分析日志之前，**不得**分配任务、**不得**创建分支、**不得**写任何代码。

### 阶段二：任务执行（各Agent — Git Flow）

```
Agent被唤醒后:
    │
    ├─ 1. 读自己的角色文件 .claude/agents/agent-*.md
    ├─ 2. 读 STATE.md + task-board.md 找自己的Todo任务
    ├─ 3. 检查依赖(BlockedBy) — 阻塞则等，非阻塞则开始
    │
    ├─ 4. 从dev拉feature分支（必须新建分支！禁止在dev上直接修改！！！）
    │      git checkout dev && git pull origin dev
    │      git checkout -b feature/{agent-name}/{task-id}-{描述}
    **铁律**：Agent在**拉取创建分支**之前，**不得**写任何代码。
    │
    ├─ 5. 编码开发（只改自己负责的目录）
    │      Agent-Lead:          backend/app/routes/ + services/ + models/
    │      Agent-Algorithm:     algorithm/ + backend/app/routes/traffic.py + prediction.py
    │      Agent-Frontend-Main: frontend/src/views/ + router/ + store/ + api/
    │      Agent-Frontend-Map:  frontend/src/components/map/ + socketio/
    │      Agent-Test-Docs:     backend/tests/ + docs/
    │
    ├─ 6. 运行验证命令（必须通过，不通过不算完成）
    │      Agent-Lead:          flask run + curl测试关键端点200
    │      Agent-Algorithm:     python run_simulation.py all
    │      Agent-Frontend-*:    npx vite build（零错误）
    │      Agent-Test-Docs:     pytest tests/ -v（全部通过）
    │
    ├─ 7. git add + git commit + git push feature分支
    │
    ├─ 8. 到GitHub创建 Pull Request: feature/* → dev
    │      PR标题: [task-id] 任务描述
    │      PR描述: 改动摘要 + 验证结果
    │
    ├─ 9. 写追踪文件（缺一不可）
    │      agent-logs/{agent-name}-log.md  — 追加 🎯→💭→📝→✅
    │      task-board.md                   — 任务状态 → Done
    │      handoff-queue.md                — 如有下游依赖，登记交付
    │      decisions-log.md                — 如有技术决策，记录背景+选项+决议
    │
    └─ 10. 等待Agent-Lead审核PR → 合并后 git checkout dev && git pull
```

### 阶段三：PR审核合并（Agent-Lead）

```
Agent-Lead 收到PR通知:
    │
    ├── ⚠️ 运行全量测试确认PR合并后不会破坏dev
    │      cd backend && pytest tests/ -v     # 必须91+ passed
    │      cd frontend && npx vite build       # 必须0 errors
    │
    ├── 检查代码在正确目录下（不碰其他Agent文件）
    ├── 检查验证命令已通过（PR描述中有验证结果）
    ├── 检查追踪文件已更新（agent-log + task-board）
    ├── 检查无merge冲突（有则让作者先rebase dev解决）
    │
    └── 全部通过 → 用 git merge --no-ff 合并（保留分支历史痕迹）
         GitHub必须选 "Create a merge commit"，禁止 Squash/Rebase
```

> **铁律**：任何PR合并前必须跑全量测试。测试不通过 → 打回，不让合并。

### 阶段四：审查验收（Agent-Judge，周期性）

```
Agent-Judge 被唤醒后:
    │
    ├── 定位 Done列任务 → 读取交付物
    ├── 逐项对照验收条件检查 → 存在性/完整性/规范性/正确性
    ├── 写审查报告到 decisions-log.md
    └── 更新看板:
         ✅ APPROVED          → 任务移到 Approved 列
         ⚠️ CHANGES_REQUESTED → 向 Agent-Lead 反馈具体问题
         ❌ REJECTED          → 向 Agent-Lead 反馈具体问题
```

**Judge 审查不通过时的修复流程（回到阶段一）**：
```
Agent-Judge 向 Agent-Lead 反馈问题
    │
    ▼
Agent-Lead 分析问题 → 写分析日志 → 拆分修复任务 → 分配Agent
    │
    ▼
回到 阶段二（任务执行）→ 阶段三（PR审核）→ 阶段四（重新审查）
```

**阶段四结束标志**：dev 分支合并完毕 + Agent-Judge 审查 APPROVED。

> ⚠️ **阶段四结束后，立即停止，等待用户手动测试。** 未经用户确认，不得进入阶段五。

### 阶段五：发布上线（Agent-Lead，用户确认后方可执行）

```
用户确认测试通过后:
    │
    ├── git checkout dev && git pull origin dev
    ├── git checkout -b release/x.x
    ├── 更新版本号 + 文档完善
    ├── git push -u origin release/x.x
    └── 通知用户：release/x.x 已就绪，请用户自行合并到 master
```

> 🔒 **禁止推送 master**：Agent-Lead 不得 push 到 master。master 合并只能由用户手动执行。
> 🔒 **禁止未经用户确认就创建 release**：阶段五必须在用户明确说"可以发布"之后才能启动。

### 紧急修复流程（hotfix）

```
生产紧急Bug:
    │
    ├── git checkout master
    ├── git checkout -b hotfix/{描述}
    ├── 修复 → 验证 → push
    └── 创建两个PR: hotfix → master + dev
```

---

## Agent 速查表

| Agent | 唤醒命令 | 负责目录 | 关键文件 |
|-------|---------|---------|----------|
| agent-lead | `@agent-lead` | `backend/` (auth/sections/warning/route/stats/sumo) | config.py, app/__init__.py, app/models/ |
| agent-algorithm | `@agent-algorithm` | `algorithm/` + `backend/app/routes/traffic.py` + `prediction.py` | KNN/RF模型, SUMO仿真 |
| agent-frontend-main | `@agent-frontend-main` | `frontend/src/` (views/router/store/api) | Vue页面, ECharts, Pinia |
| agent-frontend-map | `@agent-frontend-map` | `frontend/src/components/map/` | 高德地图, WebSocket客户端 |
| agent-test-docs | `@agent-test-docs` | `backend/tests/` + `docs/` | pytest, 报告, PPT |
| agent-judge | `@agent-judge` | 只读审查 | 审查Done列→打分 |

---

## 技术栈

Python Flask + SQLAlchemy + Celery + Redis | Scikit-learn (KNN+RF) + SUMO | Vue 3 + Element Plus + ECharts + 高德地图 JS API 2.0 | WebSocket (Flask-SocketIO)

## 构建与验证

```bash
# 后端
cd backend && pip install -r requirements.txt && flask --app run.py run --port 5000

# 前端
cd frontend && npm install && npm run dev

# 测试
cd backend && pytest tests/ -v

# 算法
cd algorithm && python run_simulation.py all
```

## 禁忌

1. 不在预测接口中直接加载模型文件 — 用单例模式在启动时预加载
2. 不轮询 `/api/traffic/current` — 用 WebSocket 推送代替
3. 不硬编码路径 — 用 `config.py` 环境变量或 `pathlib.Path`
4. Windows 路径统一用正斜杠或 `pathlib.Path`
5. 不提交密码到 Git — 用 `.env` + `.gitignore`
6. 不写代码不验证就标记 Done — 每个 Agent 必须运行验证通过

## 当前状态 → 详见 [STATE.md](STATE.md)

## Agent 通信协议

| 文件 | 用途 |
|------|------|
| [.claude/board/task-board.md](.claude/board/task-board.md) | Kanban看板：Backlog→Todo→InProgress→Done→Approved |
| [.claude/board/handoff-queue.md](.claude/board/handoff-queue.md) | 交付交接：Agent A完成→Agent B接手 |
| [.claude/board/decisions-log.md](.claude/board/decisions-log.md) | 关键决策 + Judge审查报告 |
| [agent-logs/](agent-logs/) | 每个Agent的完整思考轨迹 |
| [run-log.md](run-log.md) | 项目级执行日志 |

## Git Flow 分支规范（Vincent Driessen 模型，强制执行）

```
master   — 生产就绪（只从 release/* 或 hotfix/* 合并，禁止直接提交）
dev      — 开发主线（只从 feature/* PR 合并，禁止直接提交）
feature/{agent-name}/{task-id}-{描述} — 新功能分支（从dev拉出→完成后PR到dev）
release/* — 发布准备（从dev拉出→合并到master+dev）
hotfix/*  — 紧急修复（从master拉出→合并到master+dev）
```

### 每个任务的标准流程
```bash
# Agent从dev拉feature分支
git checkout dev && git pull origin dev
git checkout -b feature/{agent-name}/{task-id}-{描述}

# 开发 → 验证 → 推送
git add [文件] && git commit -m "[task-id] 描述"
git push -u origin feature/{agent-name}/{task-id}-{描述}

# 到GitHub创建PR: feature/* → dev → Agent-Lead审核合并
# 完成后切回dev同步
git checkout dev && git pull origin dev
```

### Git Flow 禁忌（所有Agent必须遵守）
- ❌ 禁止在 master 上直接 commit — 只从 release/hotfix 合并
- ❌ 禁止在 dev 上直接 commit — 只从 feature PR 合并
- ❌ 禁止绕过 PR 直接 push 到 dev — 必须先 push feature 分支再提 PR
- ❌ 禁止自己合并自己的 PR — 由 Agent-Lead 审核合并
- ❌ 禁止 force push 到 master/dev
- ❌ 禁止推送未验证代码 — 每个Agent必须先运行验证命令通过
- ❌ 禁止 Fast-Forward 合并 — 合并必须用 `git merge --no-ff` 或 GitHub "Create a merge commit"，保留分支历史痕迹

## 设计文档索引（按需读取，不必每次启动加载）

| 文档 | 路径 | 何时读 |
|------|------|--------|
| 总体架构 | [docs/02-概要设计/总体架构设计与模块划分-20260701.md](docs/02-概要设计/总体架构设计与模块划分-20260701.md) | 新Agent加入时 |
| API规范 | [docs/02-概要设计/API详细接口规范-20260701.md](docs/02-概要设计/API详细接口规范-20260701.md) | 开发API时 |
| 数据库设计 | [docs/02-概要设计/数据库设计与E-R图-20260701.md](docs/02-概要设计/数据库设计与E-R图-20260701.md) | 改表结构时 |
| new_advice需求 | [new_advice/](new_advice/) | 三用户角色平台开发时 |
