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

---

### [审查] D3-T01 总体架构设计与模块划分 — 2026-07-01

**审查结果**：✅ APPROVED

**审查概要**：文档结构完整（12章节），覆盖了架构图、6大模块划分、API路由表、数据库实体、接口契约、数据流。是所有下游文档的基准，被其余4份文档正确引用。

**逐项检查**：

| # | 验收条件 | 结果 | 说明 |
|---|---------|------|------|
| 1 | 架构图清晰展示三层分离 | ✅ 通过 | ASCII架构图清晰展示了前端展示层→后端服务层→数据层 |
| 2 | 模块描述完整 | ✅ 通过 | 6大模块（M1-M6），每个有技术栈+负责Agent+优先级 |
| 3 | 技术选型确认 | ✅ 通过 | 第3节三张表（后端/前端/算法），含版本+状态标记 |
| 4 | API路由表完整 | ✅ 通过 | 第4.2节7个路由模块，含方法+端点+认证要求 |
| 5 | 数据库实体概览 | ✅ 通过 | 第5节8个实体+关键字段+负责Agent，为D3-T05提供基准 |
| 6 | 模块间接口契约 | ✅ 通过 | 第2.2节M1→M2→M4数据流，第7节PredictionService/WebSocket接口 |
| 7 | 后端目录结构 | ✅ 通过 | 第4.1节完整MVC三层目录树 |
| 8 | 前端架构约定 | ✅ 通过 | 第8节路由表+Store+目录，FE-Main和FE-Map均据此设计 |
| 9 | 依赖标注正确 | ✅ 通过 | D3-T05标记为依赖D3-T01的BlockedBy，已正确解除 |

**亮点**：
- 第2.2节模块间接口契约清晰，下游Agent不需要猜接口格式
- API版本化(/api/v1/)为后续升级留空间
- 第11节明确列出下游Agent可开始的工作+对应章节

---

### [审查] D3-T02 算法模块设计（含数据管道）— 2026-07-01

**审查结果**：✅ APPROVED

**审查概要**：文档覆盖SUMO仿真配置、5步骤数据管道、策略模式双模型、评估方案、API对接。代码示例具体到函数级，可作为D6-D10开发的直接参考。

**逐项检查**：

| # | 验收条件 | 结果 | 说明 |
|---|---------|------|------|
| 1 | SUMO配置方案完整 | ✅ 通过 | 第2节：24路段/12路口/3时段/40检测器，参数明确 |
| 2 | 数据管道设计完整 | ✅ 通过 | 第3节5步骤每步有函数签名+代码示例 |
| 3 | KNN模型架构设计 | ✅ 通过 | 第4.2节GridSearchCV参数范围+代码框架 |
| 4 | 随机森林模型架构设计 | ✅ 通过 | 第4.3节参数范围+特征重要性输出 |
| 5 | 模型评估方案 | ✅ 通过 | 第5节TimeSeriesSplit+4指标+合格阈值表 |
| 6 | API对接设计 | ✅ 通过 | 第6.2节predict_flow()接口签名，与D3-T01第7.1节一致 |
| 7 | Celery重训练设计 | ✅ 通过 | 第6.3节retrain_models()设计草案 |

**亮点**：
- 策略模式（BaseTrafficPredictor）设计优雅，新增模型只需实现接口
- 评估方法选择TimeSeriesSplit而非KFold——时间序列数据的正确选择
- 第3.2节每步代码可直接转为实际实现

**与D3-T01一致性验证**：
- ✅ predict_flow接口签名与Leader的PredictionService接口一致
- ✅ 数据流M1→M2与Leader第2.2节对齐

---

### [审查] D3-T03 前端架构与路由设计 — 2026-07-01

**审查结果**：✅ APPROVED

**审查概要**：文档完整覆盖组件树、路由懒加载、3个Pinia Store、Axios JWT封装、ECharts集成方案。与FE-Map的协作约定已明确确认。

**逐项检查**：

| # | 验收条件 | 结果 | 说明 |
|---|---------|------|------|
| 1 | 路由表完整 | ✅ 通过 | 第2.1节10条路由+动态import懒加载+chunk预估 |
| 2 | 导航守卫设计 | ✅ 通过 | 第2.2节：401→跳转登录、403→Dashboard、已登录访问login→重定向 |
| 3 | 组件树完整 | ✅ 通过 | 第1节9页面+15+组件，父子关系清晰，FE-Map组件标注了挂载位 |
| 4 | 状态管理方案 | ✅ 通过 | 第3节3个Store(user/traffic/warning)，与Leader第8.2节一致 |
| 5 | Axios封装方案 | ✅ 通过 | 第4节JWT注入+401自动登出+超时处理 |
| 6 | ECharts集成方案 | ✅ 通过 | 第5节按需引入(Line+Bar+Heatmap)+BaseChart可复用组件 |
| 7 | FE-Map协作确认 | ✅ 通过 | 第6节逐条确认D3-T04第8节的5个约定 |

**亮点**：
- ECharts按需引入（~300KB vs 全量~1MB）——有实际性能考量
- Axios响应拦截器401自动跳转登录——用户体验设计到位
- 路由chunk分割预估具体大小——不是随便说说的

**与D3-T01/D3-T04一致性验证**：
- ✅ 路由表与Leader第8.1节一致
- ✅ Store划分与Leader第8.2节一致
- ✅ 第6节FE-Map协作约定与D3-T04第8节逐条匹配

---

### [审查] D3-T04 地图集成方案设计 — 2026-07-01

**审查结果**：✅ APPROVED

**审查概要**：文档覆盖高德2.0初始化、5个核心组件、WebSocket客户端架构、地图-ECharts联动、CSS变量体系、4断点响应式。组件设计具体到Props/Events/代码示例。

**逐项检查**：

| # | 验收条件 | 结果 | 说明 |
|---|---------|------|------|
| 1 | 高德API接入方案 | ✅ 通过 | 第2节：异步加载+暗色主题+Key安全方案(.env+.gitignore) |
| 2 | 地图组件设计 | ✅ 通过 | 第3.1节5个组件(TrafficMap/Heatmap/Trajectory/Marker/AlertPopup) |
| 3 | WebSocket事件设计 | ✅ 通过 | 第4节单例SocketClient+事件协议(warning:new/update/resolve, traffic:update) |
| 4 | 地图-ECharts联动 | ✅ 通过 | 第5节通过Pinia Store解耦——地图emit→Store→ECharts watch |
| 5 | 颜色映射体系 | ✅ 通过 | 第6节4级路况颜色+预警颜色+暗色主题CSS变量 |
| 6 | 响应式设计 | ✅ 通过 | 第7节4断点(1920/1366/768/<768)策略 |

**亮点**：
- WebSocket单例设计避免多连接——是D3-T01禁忌#2（不要轮询）的正确延伸
- 地图-ECharts联动通过Store解耦，两个组件可独立开发测试
- CSS变量体系（--traffic-smooth/slow/congested/jammed）语义化命名

**与D3-T01一致性验证**：
- ✅ WebSocket事件名与Leader第7.3节一致(warning:new, traffic:update)
- ✅ 地图页面路由/traffic与Leader第8.1节一致

**建议（非阻塞）**：
- ⚠️ AlertPopup弹窗建议增加「不再提示同类预警」功能（D6实现时考虑）

---

### [审查] D3-T05 数据库设计与E-R图 — 2026-07-01

**审查结果**：✅ APPROVED

**审查概要**：文档包含ASCII格式E-R图、8表完整数据字典（字段/类型/约束/索引/默认值）、完整DDL脚本（含CREATE DATABASE+字符集utf8mb4）、Seed数据、8条测试草案。DDL可执行性待MySQL实际验证（D6阶段）。

**逐项检查**：

| # | 验收条件 | 结果 | 说明 |
|---|---------|------|------|
| 1 | E-R图完整 | ✅ 通过 | 第1节ASCII格式，8实体+1:N关系+多外键标注，兼容所有Markdown渲染器 |
| 2 | 数据字典完整（8表） | ✅ 通过 | 第2节每表字段/类型/约束/默认值/索引/说明六列 |
| 3 | DDL脚本草案 | ✅ 通过 | 第3节完整SQL，含外键CASCADE+DEFAULT+COMMENT |
| 4 | 实体关系正确 | ✅ 通过 | 与D3-T01第5-6节8实体+关系描述一致 |
| 5 | 索引设计合理 | ✅ 通过 | 复合索引idx_record_section_time覆盖最常用查询 |
| 6 | Seed数据 | ✅ 通过 | 第4节预置admin+analyst用户+示例路段+检测器 |

**亮点**：
- traffic_records使用BIGINT+分区策略（日增估算3840条→月增17万）——有数据量考量
- 外键全部CASCADE——路段删除自动清理4张关联表
- DDL含utf8mb4字符集——emoji等特殊字符支持
- 8条测试用例草案前置到设计阶段——质量意识

**与D3-T01一致性验证**：
- ✅ 8实体与Leader第5节一致（users→route_records/system_logs全量覆盖）
- ✅ 实体关系与Leader第6节一致

**建议（非阻塞）**：
- DDL在MySQL 8.x上实际执行验证（D6由Leader负责）
- JSON字段（coordinates, route_path, details）的查询性能需EXPLAIN验证

---

## 审查总结

| 任务 | Agent | 审查结果 | 问题数 |
|------|-------|---------|--------|
| D3-T01 总体架构设计 | Agent-Lead | ✅ APPROVED | 0 |
| D3-T02 算法模块设计 | Agent-Algorithm | ✅ APPROVED | 0 |
| D3-T03 前端架构设计 | Agent-Frontend-Main | ✅ APPROVED | 0 |
| D3-T04 地图集成方案 | Agent-Frontend-Map | ✅ APPROVED | 0 |
| D3-T05 数据库设计 | Agent-Test-Docs | ✅ APPROVED | 0 |

**通过率：5/5（100%）**

### 交叉一致性验证

| 检查项 | 结果 |
|--------|------|
| D3-T01实体清单 ↔ D3-T05数据字典 | ✅ 8实体全量覆盖 |
| D3-T01 API路由表 ↔ D3-T03路由设计 | ✅ 7模块+10路由一致 |
| D3-T01 WebSocket事件 ↔ D3-T04 WS协议 | ✅ 事件名+数据格式一致 |
| D3-T01前端约定 ↔ D3-T03前端架构 | ✅ Store/路由/目录一致 |
| D3-T02预测接口 ↔ D3-T01 PredictionService | ✅ predict_flow签名一致 |
| D3-T03协作约定 ↔ D3-T04协作约定 | ✅ 5条逐项匹配 |

---

### [审查] D4-T01 API详细接口规范 — 2026-07-02

**审查结果**：✅ APPROVED — 7模块30+端点完整，与D4-T03/T04一致

### [审查] D4-T02 模型接口详细规范 — 2026-07-02

**审查结果**：✅ APPROVED — Schema完整，与D4-T01 §5对齐

### [审查] D4-T03 前端API对接+Mock — 2026-07-02

**审查结果**：✅ APPROVED — 7模块封装+Mock三场景+与D4-T01端点一致

### [审查] D4-T04 WebSocket消息格式规范 — 2026-07-02

**审查结果**：✅ APPROVED — 6事件TS Schema，与D4-T01 §9一致

### [审查] D4-T05 API测试用例设计 — 2026-07-02

**审查结果**：✅ APPROVED — 36条用例(正常17+异常15+边界4)，覆盖全部端点

### [审查] D5-T01 概要设计报告整合 — 2026-07-02

**审查结果**：✅ APPROVED — 10章节+附录完整索引

---

## 审查总结（D4+D5）

| 任务 | Agent | 结果 |
|------|-------|------|
| D4-T01~T05 | 全5Agent | ✅ 5/5 APPROVED |
| D5-T01 | Test-Docs | ✅ APPROVED |
| **通过率** | | **6/6 (100%)** |

### 🎉 概要设计阶段(D3-D5)全部审查通过

| 阶段 | 任务数 | 审查 |
|------|--------|------|
| D3 | 5 | ✅ 5/5 Approved |
| D4 | 5 | ✅ 5/5 Approved |
| D5 | 1 | ✅ 1/1 Approved |
| **合计** | **11** | ✅ **11/11 (100%)** |

> 零驳回，零修改要求。可正式进入D6详细设计+开发阶段。

### 建议（D4阶段关注）

1. 5份设计文档均高质量，无阻塞性问题
2. D4 API详细设计时建议Leader产出OpenAPI/Swagger格式文档
3. D6开发前建议所有Agent重新阅读decisions-log.md中的9条决策
4. DDL脚本需在D6由Leader在MySQL上实际执行验证

---

## D6-D13 开发阶段决策记录

### [决策] D6-T02 netgenerate vs 手写XML — Agent-Algorithm (2026-07-02)

**背景**：需创建24路段/12交叉口的SUMO路网
**选项**：A-手写.net.xml(~800行) / B-netgenerate --grid一行命令
**决议**：B。理由：14天工期手写易出错；网格路网足够验证算法；run_simulation.py封装了generate命令
**影响**：网格路网非真实城市路网，迁移需重新建模

### [决策] D6-T03 直接写package.json vs Vite CLI — Agent-Frontend-Main (2026-07-02)

**背景**：需初始化Vue 3项目，CLI是交互式的不适合Agent
**决议**：直接写package.json+vite.config.js+源文件。D3-T03已设计好所有文件结构

### [决策] D8-T01 PredictionService单例模式 — Agent-Algorithm (2026-07-02)

**背景**：禁忌#1禁止每次请求加载模型
**选项**：A-每次joblib.load / B-Flask全局变量 / C-Python单例(__new__)
**决议**：C。理由：全局唯一实例；首次实例化自动加载；与Flask工厂函数兼容
**影响**：模型路径硬编码saved_models/，后续需config化

### [决策] D8-T03 预警阈值85%/95% — Agent-Lead (2026-07-02)

**背景**：预警规则需要occupancy阈值区分WARNING/CRITICAL
**选项**：A-70%/90%(敏感) / B-85%/95%(平衡) / C-自适应(需历史数据)
**决议**：B。理由：交通领域常用阈值；自适应需历史数据(暂缺)；阈值可通过API动态修改

### [决策] D9-T02 Dijkstra用heapq vs networkx — Agent-Lead (2026-07-02)

**背景**：路径规划需最短路径算法
**选项**：A-networkx(功能完整+依赖) / B-手写heapq Dijkstra(零依赖~50行)
**决议**：B。理由：24路段不需要networkx完整图论；零依赖适合课程项目

### [决策] D11 ID相邻→haversine坐标距离 — Agent-Lead (2026-07-02)

**背景**：D9的build_graph用ID相邻简化，真实路网不准确
**选项**：A-保持ID相邻 / B-haversine公式+1km阈值
**决议**：B。理由：地理距离标准公式；使路径规划适配任意路网

### [决策] D6-T04 高德Key用.env vs 硬编码 — Agent-Frontend-Map (2026-07-02)

**背景**：禁忌#5禁止硬编码密钥
**决议**：import.meta.env.VITE_AMAP_KEY + .env + .gitignore。提供.env.example模板

### [决策] D10 测试用SQLite内存库 vs MySQL — Agent-Test-Docs (2026-07-02)

**背景**：测试需快速创建/销毁，不应依赖外部MySQL
**选项**：A-MySQL(真实环境) / B-SQLite内存库(零外部依赖)
**决议**：B。理由：CI可直接跑；pytest fixture自动管理；14天工期够用
