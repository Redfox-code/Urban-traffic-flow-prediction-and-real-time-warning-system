---
name: naming-conventions
description: Python/Vue/SQL/文件命名规范
metadata:
  type: reference
---

# 命名规范

## Python
| 元素 | 规范 | 示例 |
|------|------|------|
| 文件名 | `snake_case` | `traffic_service.py` |
| 类名 | `PascalCase` | `TrafficRecord` |
| 函数/方法 | `snake_case` | `get_traffic_flow()` |
| 变量 | `snake_case` | `traffic_data` |
| 常量 | `UPPER_SNAKE_CASE` | `MAX_PAGE_SIZE` |
| 私有方法 | `_leading_underscore` | `_validate_input()` |
| 包名 | `snake_case` 简短 | `routes`, `services`, `models` |

## Vue 3
| 元素 | 规范 | 示例 |
|------|------|------|
| 组件文件 | `PascalCase.vue` | `TrafficMonitor.vue` |
| 页面文件 | `PascalCase.vue`，放在views/ | `TrafficDashboard.vue` |
| 组合式函数 | `useCamelCase.js` | `useTrafficData.js` |
| Props | `camelCase` | `sectionId` |
| Events | `kebab-case` | `@section-change` |
| Store文件 | `camelCase.js` | `traffic.js` |
| API模块 | `camelCase.js` | `trafficApi.js` |

## SQL / 数据库
| 元素 | 规范 | 示例 |
|------|------|------|
| 表名 | `snake_case` 复数 | `traffic_records` |
| 字段名 | `snake_case` | `created_at` |
| 主键 | `id` | `id` |
| 外键 | `{table}_id` | `section_id` |
| 时间戳 | `created_at`, `updated_at` | — |
| 索引名 | `ix_{table}_{column}` | `ix_traffic_records_timestamp` |

## 文件路径
- 统一使用**正斜杠** `/`，不用反斜杠 `\`
- Python中用 `pathlib.Path` 而非字符串拼接
- 目录名用小写+连字符（如 `route-plan`）或中文

## 注释规范
- Python：docstring用三引号，关键逻辑加行内注释
- Vue：组件顶部加 `<!-- 组件说明 -->`
- 复杂算法：注释解释「为什么这样做」，而非「做了什么」

**Why:** 多人（Agent）协作，没有统一命名规范会导致代码库混乱。
**How to apply:** 所有Agent写代码前读本文件；Agent-Judge审查时以此为标准。
