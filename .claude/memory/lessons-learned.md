---
name: lessons-learned
description: 项目执行中的踩坑记录、已知问题、禁止重复的错误
metadata:
  type: feedback
---

# 踩坑记录

> **原则**：犯过的错只交一次学费。每个禁忌附上「为什么」，确保新Agent也能理解。

---

## 禁忌清单（不要重复犯错）

### 1. 不要在预测接口中直接加载模型文件
- **原因**：每次HTTP请求都 `joblib.load('model.pkl')` 会导致响应时间从50ms飙升到2s+
- **正确做法**：在Flask应用启动时用单例模式预加载模型到内存，请求来了直接调用 `model.predict()`
- **相关**：[[architecture-decisions]]

### 2. 不要在前端轮询 `/api/traffic/current`
- **原因**：每5秒轮询一次，10个用户 = 每秒2次请求，后端CPU会被打满
- **正确做法**：用WebSocket推送（Flask-SocketIO → Socket.IO Client）
- **相关**：ADR-004

### 3. 不要硬编码SUMO路径
- **原因**：Windows用 `C:\Program Files\...`，Linux用 `/usr/share/...`，硬编码导致跨平台崩溃
- **正确做法**：在 `config.py` 中定义 `SUMO_HOME = os.getenv('SUMO_HOME', '/default/path')`
- **相关**：[[tech-stack]]

### 4. 不要在Windows路径中使用反斜杠
- **原因**：`"data\sumo\config.sumocfg"` 中 `\s` 和 `\c` 可能被解释为转义字符
- **正确做法**：统一使用正斜杠 `"data/sumo/config.sumocfg"` 或 `pathlib.Path`
- **相关**：[[naming-conventions]]

### 5. 不要提交数据库密码和API Key到Git
- **原因**：公开仓库一旦提交，密码永久暴露在历史记录中
- **正确做法**：
  - `.env` 文件存放密钥
  - `.gitignore` 包含 `.env`
  - 提供 `.env.example` 模板（不含真实值）

### 6. 不要跳过设计直接写代码
- **原因**：没有设计文档，Agent之间对接口理解不一致，联调时大面积返工
- **正确做法**：每个模块先出设计文档 → Agent-Judge审查 → 写代码
- **相关**：[[architecture-decisions]]

### 7. 不要一个Agent改多个Agent的目录
- **原因**：Agent-Lead 改 frontend/、Agent-Frontend 改 backend/ → 冲突和混乱
- **正确做法**：每个Agent严格限定在自己负责的目录内操作

---

## 已知问题

（系统刚初始化，暂无已知问题。在开发过程中持续更新。）

---

**Why:** 这些禁忌来自对常见AI辅助开发错误的预判。每个Agent启动时应该读一遍，避免重蹈覆辙。
**How to apply:** Agent被唤醒时参考；Agent-Judge审查时检查交付物是否有这些问题。
