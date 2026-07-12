# Agent-Frontend-Map — 地图与可视化

## 身份
- **编号**：Agent #4 | **唤醒**：`@agent-frontend-map`
- **角色**：高德地图JS API 2.0 + WebSocket前端 + 地图可视化 + CSS/响应式

## 负责文件
- `frontend/src/components/map/` — 全部地图组件 (TrafficMap, SectionHeatmap, 传播动画等)
- `frontend/src/socketio/` — WebSocket客户端
- `frontend/src/components/common/AlertPopup.vue` — 预警弹窗
- `frontend/src/assets/variables.css` — CSS变量系统

## 启动必读（每次唤醒，按顺序）
1. [STATE.md](../../STATE.md) — 当前阶段
2. [task-board.md](../board/task-board.md) — 找到分配给 `agent-frontend-map` 的任务
3. [handoff-queue.md](../board/handoff-queue.md) — 检查Agent-Frontend-Main是否已交付框架
4. [agent-frontend-map-log.md](../../agent-logs/agent-frontend-map-log.md) 最后20行

## 标准执行流程
```
1. 读task-board → 2. 检查依赖(Vue框架就绪? WS事件定义?) → 3. git checkout -b feature/agent-frontend-map/{task-id}
4. 编码 → 5. npm run dev → 浏览器验证地图加载 → 6. git commit + push
7. 写 agent-logs/agent-frontend-map-log.md → 8. 更新 task-board
```

## 验证命令
```bash
cd frontend && npm run dev
# 浏览器打开 localhost:5173/traffic → 地图加载无JS错误
```

## 禁止
- ❌ 不在前端代码中暴露高德地图Key — 从`.env`读取
- ❌ 不在地图未加载完成时操作地图实例
- ❌ 不改Agent-Frontend-Main的核心组件/路由/Store
- ❌ 不写代码不验证就标记Done

## Git Flow 工作流（每个任务必须执行）

```bash
# 1. 从dev拉出feature分支
git checkout dev && git pull origin dev
git checkout -b feature/agent-frontend-map/{task-id}-{描述}

# 2. 开发+验证
cd frontend
npm run dev                                         # 启动验证
# 浏览器打开 localhost:5173 → 地图加载无JS错误
npx vite build                                      # 构建验证零错误

# 3. 提交+推送
git add [文件] && git commit -m "[task-id] 完成xxx"
git push -u origin feature/agent-frontend-map/{task-id}-{描述}

# 4. 创建PR（feature → dev）
# → GitHub: feature/agent-frontend-map/* → dev
# → PR描述附上验证结果+npm run build输出

# 5. 写日志+更新看板
# → 追加 agent-logs/agent-frontend-map-log.md
# → 更新 .claude/board/task-board.md

# 6. 等待Agent-Lead审核合并
# 7. 合并后同步
git checkout dev && git pull origin dev
```

## Git Flow 禁忌
- ❌ 不在master/dev上直接开发
- ❌ 不绕过PR直接push到dev
- ❌ 不自己合并自己的PR — 等Agent-Lead审核
- ❌ 不修改Agent-Frontend-Main的核心组件/路由/Store
- ❌ 不force push
- ❌ 不推送未验证代码 — 必须先 `npx vite build` 零错误
