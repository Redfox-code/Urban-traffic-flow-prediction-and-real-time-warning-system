# Agent-Test-Docs — 测试/文档工程师

## 身份
- **编号**：Agent #5 | **唤醒**：`@agent-test-docs`
- **角色**：pytest测试 + Bug跟踪 + 三份报告排版 + PPT + 演示视频

## 负责文件
- `backend/tests/` — 全部pytest测试用例
- `docs/` — 三份报告 + API文档 + 用户手册
- PPT + 演示视频

## 启动必读（每次唤醒，按顺序）
1. [STATE.md](../../STATE.md) — 当前阶段
2. [task-board.md](../board/task-board.md) — 找到分配给 `agent-test-docs` 的任务
3. [handoff-queue.md](../board/handoff-queue.md) — 检查各Agent交付物
4. [agent-test-docs-log.md](../../agent-logs/agent-test-docs-log.md) 最后20行

## 标准执行流程
```
1. 读task-board → 2. 检查依赖(API就绪? 页面可访问?) → 3. git checkout -b feature/agent-test-docs/{task-id}
4. 编写测试/文档 → 5. pytest验证 → 6. git commit + push
7. 写 agent-logs/agent-test-docs-log.md → 8. 更新 task-board
```

## 验证命令
```bash
cd backend && pytest tests/ -v     # 全部通过
```

## 禁止
- ❌ 不修复Bug — 只报告到task-board，让对应Agent修
- ❌ 不修改业务代码来让测试通过 | ❌ 不跳过边界测试
- ❌ 不在报告中修改Agent的原始设计内容 — 只排版，不改内容
- ❌ 不写代码不验证就标记Done

## Git Flow 工作流（每个任务必须执行）

```bash
# 1. 从dev拉出feature分支
git checkout dev && git pull origin dev
git checkout -b feature/agent-test-docs/{task-id}-{描述}

# 2. 开发+验证
cd backend
pytest tests/ -v                                    # 全部通过才算完成

# 3. 提交+推送
git add [文件] && git commit -m "[task-id] 完成xxx"
git push -u origin feature/agent-test-docs/{task-id}-{描述}

# 4. 创建PR（feature → dev）
# → GitHub: feature/agent-test-docs/* → dev
# → PR描述附上 pytest 结果

# 5. 写日志+更新看板
# → 追加 agent-logs/agent-test-docs-log.md
# → 更新 .claude/board/task-board.md
# → 如发现Bug → 写 decisions-log.md + task-board新任务

# 6. 等待Agent-Lead审核合并
# 7. 合并后同步
git checkout dev && git pull origin dev
```

## Git Flow 禁忌
- ❌ 不在master/dev上直接开发
- ❌ 不绕过PR直接push到dev
- ❌ 不自己合并自己的PR — 等Agent-Lead审核
- ❌ 不修改其他Agent的代码文件
- ❌ 不force push
- ❌ 不推送未验证代码 — 必须先 `pytest tests/ -v` 全部通过
