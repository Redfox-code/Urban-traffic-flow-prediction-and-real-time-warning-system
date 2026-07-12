# CLAUDE.md — 城市交通流量预测与实时预警系统

> **作用**：每次 AI Agent 启动时自动加载。精简版——只保留每次必读的核心内容。

---

## ⚠️ 核心AI协作规则

> **用户提出的任何需求，若未指定由谁处理，一律由 Agent-Lead 负责：**
> 1. Agent-Lead 读取需求 → 在 `.claude/board/task-board.md` 创建任务，分配给对应 Agent
> 2. 各 Agent 在自己的 Git 分支上开发 → 验证通过 → commit + push
> 3. 每个 Agent 完成后必须写: agent-logs + handoff-queue（如需交接）+ decisions-log（如有决策）
> 4. **协调者（Claude）不得跳过 Agent 直接修改代码。即使一行改动，也必须走 Agent 流程。**

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

## Git 分支规范

```bash
# 每个任务独立分支
git checkout -b feature/{agent-name}/{task-id}-{简短描述}
# 完成后
git add [改动的文件] && git commit -m "[task-id] 描述"
git push -u origin feature/{agent-name}/{task-id}
# 禁止在 master 上直接开发，禁止 force push
```

## 设计文档索引（按需读取，不必每次启动加载）

| 文档 | 路径 | 何时读 |
|------|------|--------|
| 总体架构 | [docs/02-概要设计/总体架构设计与模块划分-20260701.md](docs/02-概要设计/总体架构设计与模块划分-20260701.md) | 新Agent加入时 |
| API规范 | [docs/02-概要设计/API详细接口规范-20260701.md](docs/02-概要设计/API详细接口规范-20260701.md) | 开发API时 |
| 数据库设计 | [docs/02-概要设计/数据库设计与E-R图-20260701.md](docs/02-概要设计/数据库设计与E-R图-20260701.md) | 改表结构时 |
| new_advice需求 | [new_advice/](new_advice/) | 三用户角色平台开发时 |
