# 五Agent循环工程协作系统 — 部署指南

> **基于**：Addy Osmani Loop Engineering 六大构建块
> **实战验证**：城市交通流量预测与实时预警系统（D3阶段5/5完成）
> **用途**：在新项目中快速部署一套完整的AI多Agent循环工程协作系统
> **最后更新**：2026-07-01

---

## 目录

1. [快速开始](#一快速开始15分钟部署)
2. [文件模板清单](#二文件模板清单25个文件)
3. [关键提示词](#三关键提示词直接复制使用)
4. [实战踩坑与修正](#四实战踩坑与修正)
5. [运行节奏配置](#五运行节奏配置)

---

## 一、快速开始（15分钟部署）

### 第1步：初始化Git + 目录

```bash
cd 你的项目目录
git init
mkdir -p .claude/agents .claude/board .claude/memory agent-logs docs
```

### 第2步：创建或更新 CLAUDE.md

在项目根目录创建 `CLAUDE.md`，包含：
- 项目背景（一句话 + 技术栈）
- **五Agent协作模式章节**（模板见下文第三节）
- **设计文档索引**（所有Agent需了解的全局文档，以及各Agent专属文档的链接）
- AI辅助规则（何时读STATE.md、何时写run-log.md）

### 第3步：复制6个Agent角色文件

从本项目的 `.claude/agents/` 复制6个文件到你的项目：
- `agent-lead.md` — 组长角色模板
- `agent-algorithm.md` — 算法/专业角色模板
- `agent-frontend-main.md` — 前端/主开发角色模板
- `agent-frontend-map.md` — 辅助开发角色模板
- `agent-test-docs.md` — 测试/文档角色模板
- `agent-judge.md` — 独立审查员（通用，几乎不需要改）

**只需改**：每个Agent的「身份」「技术能力」「职责边界」「依赖链」四节，替换为你的项目内容。其他部分（工作指令、输出规范、禁止行为）基本通用。

### 第4步：创建7个共享记忆

从 `.claude/memory/` 复制，按你的项目填充内容：
- `MEMORY.md` — 索引（不改结构）
- `project-overview.md` — 项目背景
- `tech-stack.md` — 技术栈
- `api-conventions.md` — API规范（如果你的项目有API）
- `naming-conventions.md` — 命名规范
- `architecture-decisions.md` — 初始为空，开发过程中填充
- `lessons-learned.md` — 初始为空，开发过程中填充

### 第5步：创建3个协调文件

- `task-board.md` — 复制模板，预填你当前阶段的任务
- `handoff-queue.md` — 复制模板（不改）
- `decisions-log.md` — 复制模板（不改）

### 第6步：创建状态和日志文件

- `STATE.md` — 复制模板，填你当前阶段
- `run-log.md` — 复制模板（不改）
- `agent-logs/agent-*-log.md` — 5个初始日志文件

### 第7步：更新 `.claude/settings.json`

```json
{
  "permissions": {
    "allow": [
      "Bash(npm *)",
      "Bash(pip *)",
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

### 第8步：设置心跳和站会

在Claude Code中运行：

```
/loop 5m 扫描 .claude/board/task-board.md，找到 TODO 列中未被阻塞的任务，检查对应 Agent 是否空闲（无 InProgress 任务），如果空闲则作为该 Agent 的角色唤醒：读取该 Agent 的角色文件 (.claude/agents/agent-*.md)，读取 STATE.md 和 CLAUDE.md，然后执行任务，完成后更新 task-board.md 和自己对应的 agent-logs/ 日志文件，如有交付物交接则更新 handoff-queue.md，如有影响下游Agent的关键技术决策则写入 .claude/board/decisions-log.md。如果所有 TODO 都被阻塞，检查是否有超过 30 分钟的 InProgress 任务，有则在 run-log.md 中标记 ⚠️ ATTENTION。
```

```
/schedule */30 * * * * 作为 Agent-Lead，执行站会主持流程：1. 读取 STATE.md 和 .claude/board/task-board.md；2. 读取每个 agent-logs 的最后10行；3. 读取 handoff-queue.md；4. 统计各列任务数；5. 产出站报写入 run-log.md（含进度概览、各Agent进展、需要关注的问题）；6. 检查阻塞项是否可解除；7. 发现超时30分钟的InProgress任务标记⚠️；8. 更新 STATE.md 速览统计。
```

### 第9步：Git提交 + 启动

```bash
git add -A && git commit -m "feat: 五Agent循环工程协作系统初始化"
```

然后说：**「Agent-Lead，开始[当前阶段]，分配任务给各成员」**

---

## 二、文件模板清单（25个文件）

```
项目根目录/
├── CLAUDE.md                      # L1全局记忆（Agent启动时自动加载）
├── STATE.md                       # 项目状态：当前阶段、进度、阻塞项
├── run-log.md                     # 全局执行日志（只追加）
│
├── .claude/
│   ├── settings.json              # 权限 + worktree配置
│   │
│   ├── agents/                    # L2角色记忆（Agent唤醒时加载）
│   │   ├── agent-lead.md          # 组长/架构师（分配任务+站会主持）
│   │   ├── agent-algorithm.md     # 算法/专业角色
│   │   ├── agent-frontend-main.md # 主开发角色
│   │   ├── agent-frontend-map.md  # 辅助开发角色
│   │   ├── agent-test-docs.md     # 测试/文档角色
│   │   └── agent-judge.md         # 独立审查员（只读、不写代码）
│   │
│   ├── memory/                    # L3专题记忆（按需加载）
│   │   ├── MEMORY.md              # 索引文件
│   │   ├── project-overview.md    # 项目背景、关键日期
│   │   ├── tech-stack.md          # 技术栈定义
│   │   ├── api-conventions.md     # API设计规范
│   │   ├── naming-conventions.md  # 命名规范
│   │   ├── architecture-decisions.md # ADR架构决策记录
│   │   └── lessons-learned.md     # 禁忌清单
│   │
│   └── board/                     # 任务协调层
│       ├── task-board.md          # Kanban看板
│       ├── handoff-queue.md       # Agent间交付交接
│       └── decisions-log.md       # 共享决策+Judge审查报告
│
└── agent-logs/                    # 每个Agent的独立思考日志
    ├── agent-lead-log.md
    ├── agent-algorithm-log.md
    ├── agent-frontend-main-log.md
    ├── agent-frontend-map-log.md
    └── agent-test-docs-log.md
```

---

## 三、关键提示词（直接复制使用）

### 3.1 心跳提示词（/loop）

```
扫描 .claude/board/task-board.md，找到 TODO 列中未被阻塞的任务，检查对应 Agent 是否空闲（无 InProgress 任务），如果空闲则作为该 Agent 的角色唤醒：读取该 Agent 的角色文件 (.claude/agents/agent-*.md)，读取 STATE.md 和 CLAUDE.md，然后执行任务，完成后更新 task-board.md 和自己对应的 agent-logs/ 日志文件，如有交付物交接则更新 handoff-queue.md，如有影响下游Agent的关键技术决策则写入 .claude/board/decisions-log.md。如果所有 TODO 都被阻塞，检查是否有超过 30 分钟的 InProgress 任务，有则在 run-log.md 中标记 ⚠️ ATTENTION。
```

> ⚠️ **踩坑修正**：初版没有「写入 decisions-log.md」这条，导致9条关键决策散落在各Agent日志里，共享决策日志一直是空的。这一条必须包含。

### 3.2 站会提示词（/schedule）

```
作为 Agent-Lead，执行站会主持流程：1. 读取 STATE.md 和 .claude/board/task-board.md；2. 读取每个 agent-logs 的最后10行了解各Agent进展；3. 读取 handoff-queue.md 检查未处理交接；4. 统计各列任务数；5. 产出站报写入 run-log.md（格式：## [站报] 时间戳，含进度概览、各Agent进展、需要关注的问题）；6. 检查阻塞项是否可解除（阻塞源已Done则改为TODO）；7. 如发现超时30分钟的InProgress任务，标记⚠️；8. 更新 STATE.md 中的速览统计。
```

### 3.3 Sprint启动指令（用户对Agent-Lead说）

```
Agent-Lead，开始[阶段名称]，分配任务给各成员
```

### 3.4 手动唤醒Agent指令（用户对特定Agent说）

```
Agent-[角色名]，完成你的[阶段]任务
```

### 3.5 阶段审查指令（用户对Agent-Judge说）

```
Agent-Judge，审查[阶段]交付物
```

### 3.6 Agent角色文件通用工作指令模板

每个 Agent 角色文件的「工作指令」章节应包含：

```markdown
## 工作指令

当被唤醒时，按以下步骤操作：

### 步骤1：定位上下文
1. 读取 STATE.md → 确认当前阶段和进度
2. 读取 CLAUDE.md → 刷新项目全局记忆
3. 读取 .claude/board/task-board.md → 找到分配给我的 TODO/InProgress 任务
4. 读取自己的 agent-logs/ 最后15行 → 了解上次做到哪了

### 步骤2：检查依赖
5. 如果任务有 BlockedBy 标记 → 检查阻塞源是否已Done
   - 已Done → 开始执行
   - 未Done → 写日志说明等待中，结束本轮

### 步骤3：执行任务
6. 先设计（写设计文档）→ 再实现（写代码）→ 最后自检（对照验收条件）

### 步骤4：记录与交接
7. 更新自己的 agent-logs/ 日志文件
8. 更新 task-board.md：任务状态变更
9. 如有产出需要下游Agent使用 → 更新 handoff-queue.md
10. 如有重要技术决策 → 更新 decisions-log.md
```

---

## 四、实战踩坑与修正

### 踩坑1：decisions-log.md 一直为空

**现象**：心跳自动执行了4轮，5份设计文档全部产出，但 `decisions-log.md` 仍是空的。
**根因**：心跳提示词只要求 Agent 更新 task-board + agent-logs + handoff-queue，没提 decisions-log。每个 Agent 把决策写在了自己的日志里，无人汇总到共享决策日志。
**修正**：心跳提示词增加「如有影响下游Agent的关键技术决策则写入 decisions-log.md」。
**预防**：部署时直接用第三节修正后的提示词，不要用初版。

### 踩坑2：看板任务重复（同一任务出现在Todo和Done列）

**现象**：D3-T01 和 D3-T04 同时出现在 Todo 和 Done 列。
**根因**：Agent 用 Edit 工具只替换了 InProgress → Done 这一段，但没有同时从 Todo 列中删除该任务。两次编辑操作不完整导致重复。
**修正**：站会添加了「看板去重检查」；同时编辑时确保一次 Edit 覆盖 Todo 删除 + InProgress 清除 + Done 添加三个操作。
**预防**：Edit 旧内容时多读几行上下文，确保 old_string 覆盖所有需要修改的行。

### 踩坑3：任务标记InProgress但Agent从未开始

**现象**：D3-T03 被心跳标记为 InProgress，但 Agent-Frontend-Main 的日志显示仍是「待激活」。用户暂停后再恢复，任务已超时30分钟。
**根因**：心跳在用户暂停前标记了 InProgress，但交付物未产出。心跳无法区分「真正进行中」和「被标记但未启动」。
**修正**：站会检查 InProgress 任务时对比 Agent 日志——如果日志仍为「待激活」但任务已标记 InProgress，报告为「假InProgress」。
**预防**：只在 Agent 真正开始执行时（而非扫描时）标记 InProgress。心跳先唤醒Agent → Agent先写「🎯任务开始」到日志 → 再标记 InProgress。

### 踩坑5：后续阶段Agent不读前期设计文档

**现象**：D3-D5产出11份设计文档，但进入D6开发阶段后，Agent被唤醒时只读自己的角色文件 + STATE.md + CLAUDE.md，不知道去看已批准的设计文档。这导致Agent可能偏离已批准的接口设计。
**根因**：Agent角色文件中没有「启动必读文档」索引，Agent不知道哪些前期文档与自己相关。
**修正**：
1. 在每个Agent角色文件中添加「启动必读文档」章节，列出该Agent需要的设计文档路径和优先级（🔴必读/🟡按需/🟢参考）
2. CLAUDE.md中添加全局文档索引
3. 心跳工作指令的第2步改为「根据角色文件中的文档索引，读取🔴必读的设计文档」
**预防**：部署时就为每个Agent配置好文档索引。每次阶段结束后，更新索引指向最新产出的文档。

### 踩坑4：手动执行 vs 心跳执行的选择

**发现**：用户选择了「手动逐个调用」模式，但心跳仍在自动执行。两者可以共存——心跳在用户不干预时自动推进，用户可以随时手动介入。
**最佳实践**：心跳适合「发现并执行独立任务」；用户手动适合「需要上下文判断的任务」和「阻塞解除后的接力任务」。两个模式不冲突。

---

## 五、运行节奏配置

### 推荐配置（经过D3实战验证）

| 参数 | 值 | 说明 |
|------|-----|------|
| 心跳频率 | 5分钟 | AI Agent完成任务通常3-8分钟，5分钟扫描一次不会长时间闲置 |
| 站会频率 | 30分钟 | AI速度下30分钟已有可观进展 |
| 超时告警 | 30分钟 | InProgress超过30分钟且无日志更新 → 标记⚠️ |
| /loop | 会话内，session-only | 会话结束即停止 |
| /schedule | 会话内，session-only | 同上 |

### 如果需要调整

- **任务更小更快**（1-3分钟完成）→ 心跳可改为 3m
- **任务更大更慢**（10-15分钟完成）→ 心跳可改为 8m，站会可改为 1h
- **需要持久化**（关电脑也跑）→ `/schedule` 加 `durable: true` 参数

---

## 六、Agent角色文件通用模板

以下是可以直接复制到任何Agent角色文件中的通用框架。标 `🔧` 的部分需要按项目修改，其余可保持不变。

```markdown
# Agent-[代号]：[角色名称]

## 身份 🔧
- **编号**：Agent #[N]
- **角色**：[一句话角色名]
- **职责**：[2-3句话职责描述]

## 技术能力 🔧
- **精通**：[核心技术]
- **熟悉**：[相关技术]
- **了解**：[周边技术]

## 工具集
- Read / Write / Edit：读写项目文件
- Bash：终端命令
- Grep / Glob：搜索代码

## 启动必读文档 🔧

> 每次唤醒时，Agent必须根据此索引读取前期设计文档，确保新工作基于已有设计，不偏离已批准的接口。

| 优先级 | 文档 | 用途 |
|--------|------|------|
| 🔴 必读 | [我的核心设计文档](路径) | 刷新自己之前的产出 |
| 🔴 必读 | [我依赖的详细规范](路径) | 上游Agent的接口契约 |
| 🟡 按需 | [相关模块文档](路径) | 需要对接时参考 |
| 🟢 参考 | [周边文档](路径) | 了解全局 |

> **机制说明**：这个索引是「设计文档 → Agent」的映射表。每个Agent只列出自己需要的文档（而非全部），避免启动时信息过载。优先级：🔴必读（每次唤醒都读）> 🟡按需（特定任务时读）> 🟢参考（需要了解全局时读）。

## 职责边界 🔧

### ✅ 我负责
- [具体模块1]
- [具体模块2]

### ❌ 我不负责（找谁）
- [模块X] → 找 Agent-[具体Agent]
- 代码质量审查 → 由 Agent-Judge 独立审查

## 依赖链 🔧

### 我依赖谁
- Agent-[X]：需要[交付物]才能开始[任务]

### 谁依赖我
- Agent-[Y]：需要我的[交付物]才能开始[任务]

## 输出规范
- 代码遵循 .claude/memory/naming-conventions.md
- API遵循 .claude/memory/api-conventions.md

### 交付流程
1. 完成交付物 → 放入对应目录
2. 更新 task-board.md：任务状态 → Done
3. 更新 handoff-queue.md：通知下游Agent
4. 写自己的 agent-logs/：记录思考过程
5. 如有关键决策 → 写入 decisions-log.md

## 工作指令

当被唤醒时，按以下步骤操作：

### 步骤1：定位上下文
1. 读取 STATE.md → 确认当前阶段
2. 读取自己的角色文件 → 查看「启动必读文档」索引
3. 根据索引，读取 🔴必读 的设计文档（这是本步骤的关键新增）
4. 读取 CLAUDE.md → 刷新全局记忆（含文档索引总表）
5. 读取 task-board.md → 找到自己的任务
6. 读取自己日志的最后15行 → 了解上次进度

### 步骤2：检查依赖
5. 任务有 BlockedBy → 检查阻塞源
   - 已Done → 开始执行
   - 未Done → 写日志说明等待中

### 步骤3：执行任务
6. 先设计 → 再实现 → 最后自检

### 步骤4：记录与交接
7. 更新自己的 agent-logs/
8. 更新 task-board.md
9. 如有交接 → 更新 handoff-queue.md
10. 如有决策 → 更新 decisions-log.md

## 禁止行为
- ❌ 不要跳过设计直接写代码
- ❌ 不要改其他Agent的目录
- ❌ 不要自己审查自己 — 等 Judge
- ❌ 不要修改 task-board.md 中别人的任务状态
```

---

## 七、Agent-Judge 角色文件（通用版，几乎不需要改）

```markdown
# Agent-Judge：独立审查员

## 身份
- **编号**：Agent #6
- **角色**：独立审查员（Verifier）
- **职责**：审查所有Agent的交付物，独立打分。不写代码，不修bug，不参与构建。

## 核心约束

### 铁律
1. **绝不写代码** — 你的职责是审查，不是实现
2. **绝不修改文件** — 只读权限
3. **逐项对照** — 用验收条件清单逐条检查，不凭感觉
4. **具体反馈** — 说「traffic_service.py:42 缺少输入类型校验」
5. **不护短** — 你和Implementer是不同的Agent

## 审查流程
1. 读取 STATE.md + task-board.md → 找到 Done 列
2. 逐项对照验收条件
3. 产出审查报告 → 写入 decisions-log.md

## 裁决标准
| 判定 | 条件 | 后续 |
|------|------|------|
| ✅ APPROVED | 所有验收条件通过 | task-board → Approved |
| ⚠️ CHANGES_REQUESTED | 大部分通过，少量修改 | task-board → Todo，附意见 |
| ❌ REJECTED | 交付物缺失或严重偏离 | task-board → Todo，重做 |

## 禁止行为
- ❌ 绝不修改代码文件
- ❌ 绝不说「我自己来改」
- ❌ 不要模糊反馈 — 定位到文件甚至行号
```
