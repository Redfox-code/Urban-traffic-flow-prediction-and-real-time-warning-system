---
name: api-conventions
description: RESTful API设计规范、统一返回格式、分页标准、错误码定义
metadata:
  type: reference
---

# API 设计规范

## 统一返回格式

```json
{
  "code": 200,
  "data": { ... },
  "message": "ok"
}
```

## 业务状态码
| code | 含义 |
|------|------|
| 200 | 请求成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 401 | 未认证（Token缺失或过期） |
| 403 | 无权限（角色不匹配） |
| 404 | 资源不存在 |
| 409 | 资源冲突（重复创建等） |
| 500 | 服务器内部错误 |

## 分页标准
**请求**：`?page=1&page_size=20`

| 参数 | 默认值 | 最大值 | 说明 |
|------|--------|--------|------|
| page | 1 | — | 页码从1开始 |
| page_size | 20 | 100 | 每页条数 |

**返回**：
```json
{
  "code": 200,
  "data": {
    "items": [...],
    "total": 100,
    "page": 1,
    "page_size": 20,
    "total_pages": 5
  },
  "message": "ok"
}
```

## API 路由前缀

所有API统一前缀：`/api/v1/`

## URL命名规范

- 使用名词复数：`/sections`、`/predictions`、`/warnings`
- 层级表达归属关系：`/sections/{id}/traffic`
- 动作用HTTP方法表达，不在URL中：
  - `GET /api/v1/sections` — 列表
  - `POST /api/v1/sections` — 创建
  - `PUT /api/v1/sections/{id}` — 更新
  - `DELETE /api/v1/sections/{id}` — 删除

## 路由模块划分

| 前缀 | 文件 | 负责Agent |
|------|------|----------|
| `/api/v1/auth/*` | `backend/app/routes/auth.py` | Agent-Lead |
| `/api/v1/sections/*` | `backend/app/routes/sections.py` | Agent-Lead |
| `/api/v1/traffic/*` | `backend/app/routes/traffic.py` | Agent-Lead |
| `/api/v1/predict/*` | `backend/app/routes/prediction.py` | Agent-Lead |
| `/api/v1/warning/*` | `backend/app/routes/warning.py` | Agent-Lead |
| `/api/v1/route/*` | `backend/app/routes/route_plan.py` | Agent-Lead |
| `/api/v1/stats/*` | `backend/app/routes/stats.py` | Agent-Lead |

## 认证

- 方案：JWT Bearer Token
- Header：`Authorization: Bearer <token>`
- Token过期：24小时
- 刷新：`POST /api/v1/auth/refresh`

**Why:** 前后端分离开发，接口规范不一致会导致大量返工。
**How to apply:** Agent-Lead设计API时必须遵循；Agent-Frontend-Main封装Axios时以此为基准。
