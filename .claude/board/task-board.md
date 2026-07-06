# 任务看板

## ✅ Done (2026-07-06)

| ID | 任务 | Agent |
|----|------|-------|
| BUG-PROG-01 | 进度条卡21%：.gitignore不生效(git rm --cached) | agent-lead |
| BUG-ORPHAN-01 | SUMO孤儿进程防护(PID文件+启动清理) | agent-lead |
| BUG-SUMO-PAUSE | 暂停信号文件残留修复(finally+优雅终止) | agent-lead |
| BUG-SIM-HANG | 仿真卡死根因修复(TraCI移除→纯Python模拟) | agent-lead |
| FEAT-SIM-REWRITE | 实时仿真业务逻辑重写(去掉TraCI) | agent-lead |
| FEAT-PREDICTION-REAL | 流量预测业务填充(真实模型+API) | agent-lead |

## 📋 Backlog

| ID | 任务 | 优先级 | Agent |
|----|------|--------|-------|
| D12-T01 | 演示视频录制 | P1 | agent-test-docs |

## 🔄 InProgress

（空）

## 📥 待验收

| ID | 任务 | 验收标准 | Agent |
|----|------|---------|-------|
| FEAT-SIM-REWRITE | 实时仿真重写 | 启动→运行→暂停→继续→停止 全流程无卡死 | agent-lead |
| FEAT-PREDICTION-REAL | 预测真实模型 | ✅ 已完成: using_trained_model:true + RF: MAE=6.16, R²=0.13 | agent-lead |
| FEAT-ANALYSIS-REPORT | 预测分析报告模块 | API /predict/analysis返回完整分析报告(5区块) + 前端分析卡片展示趋势/峰值/拥堵/对比/可靠性 | agent-lead |
