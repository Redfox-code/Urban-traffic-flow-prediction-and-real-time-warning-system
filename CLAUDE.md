# CLAUDE.md — 城市交通流量预测与实时预警系统

> **作用**：每次 AI Agent 启动时自动读取，提供项目上下文、约定和约束，避免 Agent 从零猜测。
> **灵感来源**：Addy Osmani Loop Engineering 第三块「技能（持久项目记忆）」中的 SKILL.md。

---

## 一、项目概览

- **课程**：智能运输系统设计与集成综合实验
- **选题**：城市交通流量预测与实时预警系统
- **团队**：5人小组（组长/后端 ×1，算法 ×1，前端 ×2，测试/文档 ×1）
- **总周期**：14天（D1-D14）
- **当前阶段**：需求分析已完成 → 进入概要设计

## 二、系统一句话定义

基于 Flask + SUMO + Scikit-learn + Vue 3 + ECharts + 高德地图，构建集**SUMO微观交通仿真、短时流量预测、拥堵实时预警、最优路径规划**于一体的智能交通管理平台。

## 三、技术栈速查

| 层级 | 技术 | 版本 / 说明 |
|------|------|------------|
| 后端框架 | Python Flask | RESTful API |
| 数据库 ORM | SQLAlchemy | MySQL / SQLite |
| 异步任务 | Celery + Redis | 模型定时重训练、仿真批量运行 |
| 算法 | Scikit-learn (KNN + 随机森林) | 短时流量预测 |
| 仿真 | SUMO + TraCI | 微观交通仿真 |
| 前端框架 | Vue 3 + Element Plus | SPA |
| 图表 | ECharts | 预测曲线、热力图 |
| 地图 | 高德地图 JS API 2.0 | 路况渲染、轨迹回放 |
| 实时推送 | WebSocket (Flask-SocketIO) | 预警弹窗推送 |
| 包管理 | npm (前端) + pip (后端) | — |

## 四、项目目录结构（约定）

```text
project-root/
├── backend/                  # Flask 后端
│   ├── app/                  # 应用主包
│   │   ├── models/           # SQLAlchemy 数据模型
│   │   ├── routes/           # API 蓝图 (auth, traffic, predict, alert, route)
│   │   ├── services/         # 业务逻辑层
│   │   └── utils/            # 工具函数
│   ├── migrations/           # 数据库迁移脚本
│   ├── tests/                # 后端测试 pytest
│   ├── config.py             # 配置类 (Dev/Prod/Test)
│   └── run.py                # 入口
├── frontend/                 # Vue 3 前端
│   ├── src/
│   │   ├── views/            # 页面组件
│   │   ├── components/       # 通用组件
│   │   ├── router/           # 路由
│   │   ├── store/            # Pinia 状态
│   │   ├── api/              # axios 封装
│   │   └── utils/            # 工具
│   └── public/
├── algorithm/                # 算法模块（独立于后端）
│   ├── sumo/                 # SUMO 路网、车流、检测器配置
│   ├── prediction/           # KNN + 随机森林模型
│   ├── data/                 # 训练数据、仿真输出
│   └── notebooks/            # Jupyter 探索笔记
├── docs/                     # 三份报告 + PPT
│   ├── 01-需求分析/
│   ├── 02-概要设计/
│   └── 03-详细设计/
├── CLAUDE.md                 # 本文件 — AI 持久记忆
├── STATE.md                  # 当前工作状态 — 跨会话耐久脊柱
└── run-log.md                # 执行日志 — 每次运行记录
```

## 五、构建与运行命令

### 后端

```bash
cd backend
pip install -r requirements.txt          # 安装依赖
flask --app run.py run --port 5000       # 开发启动
pytest tests/ -v                         # 运行后端测试
flask db migrate -m "message"            # 数据库迁移
flask db upgrade                         # 应用迁移
```

### 前端

```bash
cd frontend
npm install                              # 安装依赖
npm run dev                              # 开发服务器 (Vite)
npm run build                            # 生产构建
npm run lint                             # ESLint 检查
```

### 算法

```bash
cd algorithm
python -m sumo.run_simulation            # 运行 SUMO 仿真
python -m prediction.train_model         # 训练预测模型
python -m prediction.evaluate            # 模型评估
```

## 六、代码约定与禁忌

### 命名规范
- **Python**：文件名 `snake_case`，类名 `PascalCase`，函数/变量 `snake_case`
- **Vue**：组件文件 `PascalCase.vue`，组合式函数 `useCamelCase.js`
- **数据库表**：`snake_case` 复数形式（如 `traffic_records`）

### API 约定
- 所有 API 返回统一格式：`{"code": 200, "data": {...}, "message": "ok"}`
- 分页参数统一：`?page=1&page_size=20`
- 错误码在 `backend/app/utils/error_codes.py` 中集中定义

### 禁忌（上次线上事故学到什么不要再做）
1. **不要**在预测接口中直接加载模型文件——用单例模式在应用启动时预加载到内存
2. **不要**在前端轮询 `/api/traffic/current`——用 WebSocket 推送代替
3. **不要**硬编码 SUMO 路径——用 `config.py` 中的环境变量
4. **不要**在 Windows 路径中使用反斜杠——统一使用正斜杠或 `pathlib.Path`
5. **不要**把数据库密码提交到 Git——使用 `.env` 文件 + `.gitignore`

## 七、小组分工速查

| 角色 | 负责人 | 主要职责 |
|------|--------|----------|
| 组长/后端架构师 | （待填） | Flask 核心、API、数据库、系统集成 |
| 算法工程师 | （待填） | SUMO 仿真、KNN/RF 模型、数据管道 |
| 前端（主） | （待填） | Vue 3 核心页面、Element Plus、ECharts |
| 前端（辅）/ 地图 | （待填） | 高德地图、WebSocket、响应式、演示视频 |
| 测试/文档 | （待填） | 测试用例、三份报告排版、PPT、进度记录 |

## 八、AI 辅助规则

### 每次修改代码后
1. 更新对应的测试用例
2. 在 `run-log.md` 中记录变更摘要

### 每次会话开始时
1. 读取 `STATE.md` 了解当前进度
2. 读取 `run-log.md` 最后 20 行了解最近动态

### 每次会话结束时
1. 更新 `STATE.md` 中的当前任务状态
2. 将本次操作摘要追加到 `run-log.md`

## 九、报告文件索引

| 文件 | 路径 |
|------|------|
| 需求分析报告 (Markdown) | [需求分析报告-城市交通流量预测与实时预警系统.md](需求分析报告-城市交通流量预测与实时预警系统.md) |
| 需求分析报告 (Word) | [第二组-城市交通流量预测与实时预警系统-需求分析报告.doc](第二组-城市交通流量预测与实时预警系统-需求分析报告.doc) |
| PPT 演示 | [智能物流运输安全与运维集成系统设计.pptx](智能物流运输安全与运维集成系统设计.pptx) |
| 指导书 PDF | [《智能运输系统设计与集成综合实验》指导书(1).pdf](《智能运输系统设计与集成综合实验》指导书(1).pdf) |
| PDF 提取文本 | [pdf_text.txt](pdf_text.txt) |

## 十、五Agent循环工程协作模式

> 本系统采用 Addy Osmani Loop Engineering 六大构建块框架。

### Agent 体系

| Agent ID | 角色文件 | 命令唤醒 | 负责目录 |
|----------|---------|---------|---------|
| agent-lead | [.claude/agents/agent-lead.md](.claude/agents/agent-lead.md) | `@agent-lead` | `backend/` |
| agent-algorithm | [.claude/agents/agent-algorithm.md](.claude/agents/agent-algorithm.md) | `@agent-algorithm` | `algorithm/` |
| agent-frontend-main | [.claude/agents/agent-frontend-main.md](.claude/agents/agent-frontend-main.md) | `@agent-frontend-main` | `frontend/src/` |
| agent-frontend-map | [.claude/agents/agent-frontend-map.md](.claude/agents/agent-frontend-map.md) | `@agent-frontend-map` | `frontend/src/` |
| agent-test-docs | [.claude/agents/agent-test-docs.md](.claude/agents/agent-test-docs.md) | `@agent-test-docs` | `docs/`, `backend/tests/` |
| agent-judge | [.claude/agents/agent-judge.md](.claude/agents/agent-judge.md) | `@agent-judge` | 只读，不写代码 |

### 循环节奏
- **心跳**：`/loop 5m` — 每5分钟自动扫描 [.claude/board/task-board.md](.claude/board/task-board.md)，发现TODO+未阻塞 → 自动唤醒对应Agent
- **站会**：`/schedule */30 * * * *` — 每30分钟 Agent-Lead 自动汇总进展，产出站报到 [run-log.md](run-log.md)
- **审查**：每Sprint结束，手动唤醒 Agent-Judge 独立打分 → 审查报告写入 [.claude/board/decisions-log.md](.claude/board/decisions-log.md)

### 通信协议（Agent之间不直接对话）
| 用途 | 文件 | 说明 |
|------|------|------|
| 任务分配 | [.claude/board/task-board.md](.claude/board/task-board.md) | Kanban看板：Backlog→Todo→InProgress→Done→Approved |
| 交付交接 | [.claude/board/handoff-queue.md](.claude/board/handoff-queue.md) | Agent A完成 → Agent B接手 |
| 决策记录 | [.claude/board/decisions-log.md](.claude/board/decisions-log.md) | 关键决策 + Judge审查报告 |
| 各自日志 | [agent-logs/](agent-logs/) | 每个Agent的完整思考轨迹 |

### Agent 唤醒后的标准流程
1. 读取自己的角色文件（`.claude/agents/agent-*.md`）
2. 读取 `CLAUDE.md` + `STATE.md` + `.claude/memory/MEMORY.md`
3. 读取 `.claude/board/task-board.md` 找到自己的任务
4. 检查依赖关系（BlockedBy）
5. 执行任务 → 产出交付物
6. 更新 `task-board.md` + 自己的 `agent-logs/` + `handoff-queue.md`（如有交接）

### 六大构建块映射
| 块 | Addy 概念 | 本项目实现 |
|----|----------|-----------|
| 1 | 自动化调度 | `/loop 5m` 心跳 + `/schedule */30 * * * *` 站会 + Agent-Judge 阶段判定 |
| 2 | 工作树 | git worktree — Agent并行时 `isolation: "worktree"` |
| 3 | 技能/SKILL.md | `CLAUDE.md`(L1) + `.claude/agents/`(L2) + `.claude/memory/`(L3) |
| 4 | MCP连接器 | 内置工具(文件/Bash/Git) + 预留MySQL/GitHub MCP接口 |
| 5 | 子代理 | 5个Implementer + 1个独立Verifier(Judge) — 写代码和审查分离 |
| 6 | 记忆/状态 | `STATE.md` + `run-log.md` + `task-board.md` + `agent-logs/` |
