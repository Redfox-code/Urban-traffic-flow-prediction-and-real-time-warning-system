# 决策日志

> **作用**：记录关键技术决策的讨论过程和审查结果。
> 分为两个分区：**决策记录**（设计决策）和 **审查记录**（Agent-Judge的审查报告）。

---

## 决策记录

### [决策] D3-T01 总体架构采用MVC三层 + 前后端分离 — Agent-Lead

**时间**：2026-07-01
**背景**：系统需要确定总体架构模式，影响所有下游Agent的设计。
**选项**：
- A：前后端一体化（Flask模板渲染）— 简单但扩展性差
- B：前后端分离 + MVC三层 — 分离关注点，可并行开发
**决议**：选择方案B
**理由**：
- 前后端并行开发（Leader写API时FE-Main可以同时写Vue组件）
- MVC三层（路由→服务→数据）职责清晰，测试可分层进行
- API版本化（/api/v1/）为后续升级留空间
**影响**：需要处理CORS；需要维护API文档；Agent-Frontend-Main需要Axios封装

---

### [决策] D3-T02 KNN K值范围选择[3,5,7,10,15] — Agent-Algorithm

**时间**：2026-07-01
**背景**：KNN回归的K值直接影响预测效果，需要确定GridSearchCV搜索范围。
**选项**：
- A：[1,3,5] — 小K值，更快但可能过拟合
- B：[3,5,7,10,15] — 适中范围，覆盖典型值
- C：[5,10,20,30,50] — 大范围，但15以上意义不大（样本有限）
**决议**：选择方案B
**理由**：
- K=1容易过拟合噪声
- 样本量不大（40检测器×约96个15min窗口/天），K>15时邻居距离太远失去参考价值
- 奇数K值避免平票
**影响**：Agent-Lead的PredictionService期望best_params中n_neighbors在此范围内

---

### [决策] D3-T02 策略模式抽象预测模型 — Agent-Algorithm

**时间**：2026-07-01
**背景**：系统使用KNN+RF双模型（ADR-002），后续可能增加GBDT等其他模型。需要确定代码组织方式。
**选项**：
- A：独立脚本，每个模型一个train.py
- B：策略模式 — BaseTrafficPredictor抽象基类 + 各模型实现
**决议**：选择方案B
**理由**：
- 统一接口（train/predict/get_params/save/load），Leader的PredictionService不关心底层是哪个模型
- 新增模型只需实现接口，不修改现有代码（开闭原则）
- 模型评估脚本（evaluator.py）可对任何BaseTrafficPredictor子类工作
**影响**：Agent-Lead在backend/app/services/prediction_service.py中使用load()静态方法加载具体模型

---

### [决策] D3-T03 Pinia Store拆分为3个独立Store — Agent-Frontend-Main

**时间**：2026-07-01
**背景**：前端状态管理需要确定Store数量。所有状态放一个Store会变得臃肿。
**选项**：
- A：单一useAppStore（所有状态在一起）
- B：按功能拆分为user/traffic/warning三个Store
**决议**：选择方案B
**理由**：
- userStore管理认证（Token、角色），逻辑独立
- trafficStore管理实时数据（大数据量、高频更新）
- warningStore管理预警（由FE-Map的WebSocket客户端调用addWarning）
- 拆分后每个Store的actions和getters清晰，不会互相干扰
**影响**：FE-Map的WebSocket客户端需要引用useWarningStore（通过store实例而非组件内）

---

### [决策] D3-T03 ECharts按需引入（非全量）— Agent-Frontend-Main

**时间**：2026-07-01
**背景**：全量echarts包约1MB，影响首屏加载速度。
**选项**：
- A：全量引入 `import * as echarts from 'echarts'`
- B：按需引入，只注册LineChart/BarChart/HeatmapChart + 必要组件
**决议**：选择方案B
**理由**：
- 全量1MB vs 按需~300KB，首屏差距约700KB
- 系统只用这三种图表类型，不需要其他80%的echarts功能
- 后续如果需要新图表类型（如Scatter），再注册即可
**影响**：所有图表通过BaseChart.vue组件渲染，组件内不直接init echarts实例

---

### [决策] D3-T04 WebSocket客户端采用单例模式 — Agent-Frontend-Map

**时间**：2026-07-01
**背景**：多个页面（TrafficMonitor、WarningManager、Dashboard）都需要WebSocket连接。如果每个页面各自连接，会出现重复建连和资源浪费。
**选项**：
- A：每个页面各自维护Socket.IO连接
- B：单例SocketClient，全局一个连接，Store消费事件
**决议**：选择方案B
**理由**：
- 避免多连接：10个页面各自连接 = 10个WebSocket，服务器压力大
- 生命周期清晰：connect在App.vue onMounted，disconnect在onUnmounted
- 事件通过Pinia Store分发，页面只watch Store不关心连接细节
- 自动重连逻辑统一管理（退避延迟1s→2s→4s→...→30s上限）
**影响**：FE-Main的useWarningStore需要暴露addWarning action供SocketClient调用

---

### [决策] D3-T04 CSS变量体系替代硬编码颜色 — Agent-Frontend-Map

**时间**：2026-07-01
**背景**：监控大屏需要统一的暗色主题，多个组件需要一致的交通路况颜色。
**选项**：
- A：各组件各自写颜色值
- B：集中CSS变量体系，所有组件引用变量
**决议**：选择方案B
**理由**：
- 路况颜色（smooth/slow/congested/jammed）在多个组件中复用
- 换主题只需改variables.css，不用逐个组件改
- 配合暗色大屏风格（深蓝底#0a1628 + cyan强调#00d4ff）
- 变量名语义化（--traffic-smooth而非--color-green-1）
**影响**：FE-Main在main.js中全局import variables.css；所有组件使用var(--traffic-smooth)而非#00e676

---

### [决策] D3-T05 traffic_records使用BIGINT主键 — Agent-Test-Docs

**时间**：2026-07-01
**背景**：traffic_records是数据量最大的表，需要预估ID是否会溢出。
**选项**：
- A：INT主键（上限21亿）— 标准做法
- B：BIGINT主键 — 预留更多空间
**决议**：选择方案B
**理由**：
- 40检测器 × 4次/小时 × 24小时 = 3840条/天（15min采样）
- 如果改为5min采样：40 × 12 × 24 = 11520条/天
- 按日增10000条算，INT(21亿)可用575年—但SUMO仿真批量输出可能是这个量的10倍
- BIGINT只多4字节，成本极低，换来永不过期的安心
**影响**：Agent-Lead在SQLAlchemy模型中需使用BigInteger类型

---

### [决策] D3-T05 路段坐标使用JSON字段 — Agent-Test-Docs

**时间**：2026-07-01
**背景**：路段坐标序列（起点+中间点+终点）是非定长数据，需要选择存储方式。
**选项**：
- A：单独coordinate_points表（point_id, section_id, lng, lat, seq）
- B：JSON字段
**决议**：选择方案B
**理由**：
- 坐标序列长度不一（直线路段2个点，弯曲路段可能有10+个点）
- JSON查询：MySQL 8.x支持JSON_CONTAINS、JSON_EXTRACT等函数
- 高德地图Polyline直接接受[{lng, lat}, ...]数组
- 避免了1:N关联查询的JOIN开销
**影响**：Agent-Lead在SQLAlchemy中使用JSON列类型；前端FE-Map直接JSON.parse后传给AMap.Polyline

---

## 审查记录

（Agent-Judge的审查报告将追加在此。当前尚未触发Judge审查。）
