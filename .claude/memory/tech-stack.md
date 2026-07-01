---
name: tech-stack
description: 完整技术栈定义，包含版本号和选型理由
metadata:
  type: reference
---

# 技术栈

## 后端
| 技术 | 版本 | 用途 | 选型理由 |
|------|------|------|----------|
| Python | 3.10+ | 主语言 | 生态丰富，Scikit-learn/Flask支持好 |
| Flask | 3.x | Web框架 | 轻量灵活，适合中小项目，14天工期够用 |
| SQLAlchemy | 2.x | ORM | Python最成熟的ORM，支持MySQL |
| Flask-JWT-Extended | 4.x | JWT认证 | Flask官方推荐，双角色管理方便 |
| Celery | 5.x | 异步任务 | 模型定时重训练、批量仿真 |
| Redis | 7.x | 消息队列+缓存 | Celery默认broker，高性能 |
| Flask-SocketIO | 5.x | WebSocket | 实时预警推送，与Flask无缝集成 |
| Flask-CORS | 4.x | 跨域处理 | 前后端分离必需 |

## 算法
| 技术 | 版本 | 用途 |
|------|------|------|
| Scikit-learn | 1.x | KNN回归 + 随机森林模型 |
| NumPy | 2.x | 矩阵/数值运算 |
| Pandas | 2.x | 数据处理与清洗 |
| joblib | 1.x | 模型持久化到磁盘 |
| SUMO | 1.19+ | 微观交通仿真引擎 |
| TraCI | — | SUMO Python控制接口 |

## 前端
| 技术 | 版本 | 用途 |
|------|------|------|
| Vue 3 | 3.x | 前端框架（Composition API） |
| Vite | 5.x | 构建工具，开发热更新 |
| Element Plus | 2.x | UI组件库 |
| ECharts | 5.x | 图表可视化（流量曲线、柱状图） |
| 高德地图 JS API | 2.0 | 地图渲染、热力图、轨迹动画 |
| Pinia | 2.x | Vue 3官方状态管理 |
| Vue Router | 4.x | SPA路由 |
| Axios | 1.x | HTTP请求客户端 |
| Socket.IO Client | 4.x | WebSocket客户端 |

## 数据库
| 技术 | 版本 |
|------|------|
| MySQL | 8.x |

## 开发工具
| 工具 | 用途 |
|------|------|
| Git + GitHub | 版本控制 |
| pytest | 后端测试 |
| npm | 前端包管理 |
| pip | Python包管理 |

**Why:** 统一技术栈定义，所有Agent引用同一份清单，避免「你用的版本和我不一样」的问题。
**How to apply:** Agent在选择库或配置环境时，以本文件为准。
