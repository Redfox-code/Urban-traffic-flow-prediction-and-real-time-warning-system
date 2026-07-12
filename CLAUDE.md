# CLAUDE.md — 城市交通流量预测与实时预警系统

> **作用**：每次 AI Agent 启动时自动加载。精简版——只保留每次必读的核心内容。

---

## ⚠️ 核心AI协作规则

> **协调者（Claude）不得跳过 Agent 直接修改代码。即使一行改动，也必须走 Agent 流程。**

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
    ├── 拆分为可执行任务（每个任务 ≤ 1个Agent）
    ├── 写入 task-board.md（Backlog → Todo列）
    │   格式: | ID | 任务描述 | Agent | 依赖 | 分支 |
    └── @唤醒 对应Agent开始工作
```

### 阶段二：任务执行（各Agent — Git Flow）

```
Agent被唤醒后:
    │
    ├─ 1. 读自己的角色文件 .claude/agents/agent-*.md
    ├─ 2. 读 STATE.md + task-board.md 找自己的Todo任务
    ├─ 3. 检查依赖(BlockedBy) — 阻塞则等，非阻塞则开始
    │
    ├─ 4. 从dev拉feature分支
    │      git checkout dev && git pull origin dev
    │      git checkout -b feature/{agent-name}/{task-id}-{描述}
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
    ├── 检查代码在正确目录下（不碰其他Agent文件）
    ├── 检查验证命令已通过（PR描述中有验证结果）
    ├── 检查追踪文件已更新（agent-log + task-board）
    ├── 检查无merge冲突（有则让作者先rebase dev解决）
    │
    └── 全部通过 → GitHub点 Merge PR → 通知Agent同步dev
```

### 阶段四：审查验收（Agent-Judge，周期性）

```
Agent-Judge 被唤醒后:
    │
    ├── 定位 Done列任务 → 读取交付物
    ├── 逐项对照验收条件检查 → 存在性/完整性/规范性/正确性
    ├── 写审查报告到 decisions-log.md
    └── 更新看板: ✅Approved / ⚠️Changes Requested / ❌Rejected
```

### 阶段五：发布上线（Agent-Lead）

```
阶段性功能稳定后:
    │
    ├── git checkout dev && git pull
    ├── git checkout -b release/x.x
    ├── 最终测试 + 文档完善 + 版本号
    ├── git push → 创建PR: release/x.x → master + dev
    └── 合并 → 生产上线
```

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

## 设计文档索引（按需读取，不必每次启动加载）

| 文档 | 路径 | 何时读 |
|------|------|--------|
| 总体架构 | [docs/02-概要设计/总体架构设计与模块划分-20260701.md](docs/02-概要设计/总体架构设计与模块划分-20260701.md) | 新Agent加入时 |
| API规范 | [docs/02-概要设计/API详细接口规范-20260701.md](docs/02-概要设计/API详细接口规范-20260701.md) | 开发API时 |
| 数据库设计 | [docs/02-概要设计/数据库设计与E-R图-20260701.md](docs/02-概要设计/数据库设计与E-R图-20260701.md) | 改表结构时 |
| new_advice需求 | [new_advice/](new_advice/) | 三用户角色平台开发时 |
