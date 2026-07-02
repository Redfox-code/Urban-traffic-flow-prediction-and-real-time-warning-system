# 任务看板 — 系统测试

## 🐛 Bugs（待修复）

| ID | 描述 | 严重 | 分配给 | 错误 |
|----|------|------|--------|------|
| BUG-BE-02 | sections端点缺少JWT保护(200≠401) | 🔴 | agent-lead | test_public_endpoints_blocked FAILED |
| BUG-BE-03 | predict端点缺JWT+未训练模型返回500 | 🔴 | agent-algorithm | test_forecast_no_auth FAILED |
| BUG-BE-04 | JWT key过短(<32字节)安全警告 | 🟡 | agent-lead | InsecureKeyLengthWarning |
| BUG-FE-02 | Vite @/ alias未配置→import全部失败 | 🔴 | agent-frontend-main | npm run dev报错 |

## 🔄 InProgress

| ID | Agent | 开始 |
|----|-------|------|
| BUG-BE-02 | agent-lead | 修复中 |

## ✅ Done

D3-D13: 38任务完成

## ✔️ 测试通过

Phase 1: Auth✅ Sections✅ | Phase 2: SUMO✅ | Phase 4: 14/17 passed
