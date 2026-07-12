---
name: lessons-learned
description: 项目执行中的踩坑记录、已知问题、禁止重复的错误
metadata:
  type: feedback
---

# 踩坑记录

## 禁忌清单

### 1. 不要在预测接口中直接加载模型文件
- **正确做法**：Flask启动时用单例模式预加载模型到内存
- **相关**：[[architecture-decisions]]

### 2. 不要在前端轮询 `/api/traffic/current`
- **正确做法**：用WebSocket推送（Flask-SocketIO → Socket.IO Client）

### 3. 不要硬编码路径
- **正确做法**：在 `config.py` 中定义环境变量，用 `pathlib.Path`

### 4. Windows路径用正斜杠或pathlib，不用反斜杠

### 5. 不提交密码和API Key到Git — 用 `.env` + `.gitignore`

### 6. 不跳过设计直接写代码 — 先设计文档 → Judge审查 → 编码

### 7. 不一个Agent改多个Agent的目录 — 严格限定负责范围

### 8. 🆕 不跳过Agent直接修改代码（D12新增）
- **原因**：协调者(Claude)直接改代码导致Agent日志断裂、task-board无人更新、协作流程形同虚设
- **正确做法**：即使一行改动也走Agent流程：Agent-Lead分析→创建任务→分配Agent→开发→日志

### 9. 🆕 Agent角色文件不能太长（D12新增）
- **原因**：Agent启动时上下文不够用，无法读完200行角色文件+设计文档
- **正确做法**：Agent角色文件压缩到40行以内，设计文档改为按需读取

### 10. 🆕 每个Agent必须在独立Git分支上工作（D12新增）
- **原因**：多人同时改master导致冲突，且无法追踪每个Agent的贡献
- **正确做法**：feature/{agent-name}/{task-id} 分支 → commit → push → PR合并
