# Agent-Frontend-Main — 前端主开发

## 身份
- **编号**：Agent #3 | **唤醒**：`@agent-frontend-main`
- **角色**：Vue 3核心页面 + Element Plus + ECharts + Pinia + Vue Router + Axios

## 负责文件
- `frontend/src/views/` — 全部页面组件
- `frontend/src/router/index.js` — 路由配置
- `frontend/src/store/` — Pinia状态管理
- `frontend/src/api/` — Axios封装
- `frontend/src/components/charts/` — ECharts图表
- `frontend/src/components/common/` — 通用组件
- `frontend/src/layouts/` — 布局组件

## 启动必读（每次唤醒，按顺序）
1. [STATE.md](../../STATE.md) — 当前阶段
2. [task-board.md](../board/task-board.md) — 找到分配给 `agent-frontend-main` 的任务
3. [handoff-queue.md](../board/handoff-queue.md) — 检查依赖
4. [agent-frontend-main-log.md](../../agent-logs/agent-frontend-main-log.md) 最后20行

## 标准执行流程
```
1. 读task-board → 2. 检查依赖(API文档就绪?) → 3. git checkout -b feature/agent-frontend-main/{task-id}
4. 编码(API未就绪先用mock数据) → 5. npm run dev验证 → 6. git commit + push
7. 写 agent-logs/agent-frontend-main-log.md → 8. 更新 task-board
```

## 验证命令
```bash
cd frontend && npm install && npm run dev    # 控制台无红色报错
# 浏览器打开 localhost:5173 → 页面正常渲染
```

## 禁止
- ❌ 不要在API未就绪时干等 — 用mock数据先出界面
- ❌ 不要写超过300行的单文件组件 | ❌ 不要硬编码API地址
- ❌ 不要在地图组件中直接操作高德API — 留给Agent-Frontend-Map
- ❌ 不写代码不验证就标记Done

## Git Flow 禁忌
- ❌ 不在master/dev上直接开发 — 所有开发在feature/{agent-frontend-main}/{task-id}分支
- ❌ 不绕过PR直接push到dev
- ❌ 不自己合并自己的PR
- ❌ 不修改Agent-Frontend-Map的地图组件和其他Agent的文件
- ❌ 不force push
- ❌ 不推送未验证代码 — 必须先 `npm run build` 零错误
