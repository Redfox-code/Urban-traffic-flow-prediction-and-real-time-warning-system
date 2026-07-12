# Agent-Frontend-Main 执行日志

> ⚠️ 只追加不删除。2026-07-02 恢复：合并git历史版本+最新修复。

## 操作记录

| 时间 | 任务ID | 类型 | 内容 |
|------|--------|------|------|
| 系统初始化 | — | 📝 | Agent #3 日志创建。角色：前端开发(主)。 |
| 2026-07-12 | FE-MAIN-01~04 | ✅ | 三角色路由重构+3套布局组件+15个占位视图+JWT解析工具 |
| 7/01 | D3-T03 | ✅ | 前端架构设计(8章)。组件树+路由+Store+Axios。 |
| 7/01 | D4-T03 | ✅ | 前端API对接+Mock数据(5章)。 |
| 7/02 | D6-T03 | ✅ | Vue 3初始化(17文件)。Router+Store+Layout+9视图。 |
| 7/02 | D7-T03 | ✅ | Login+Register+Dashboard(统计卡片)。 |
| 7/02 | D8-T04/T05 | ✅ | PredictionBoard+WarningManager。 |
| 7/02 | D9-T03 | ✅ | RoutePlanner(起终点选择+路径时间线)。 |
| 7/02 | BUG-FE-02 | ✅修复 | Vite @/ alias配置。 |
| 7/02 | BUG-FE-03 | ✅修复 | Dashboard接入statsApi.getDashboard()真数据。 |
| 7/02 | BUG-FE-05 | ✅修复 | PredictionBoard接入sectionsApi+predictionApi。 |
| 7/02 | BUG-FE-06 | ✅修复 | WarningManager接入warningApi筛选+解除。 |
| 7/02 | BUG-FE-07 | ✅修复 | RoutePlanner接入sectionsApi+routeApi。 |
| 7/02 | UI-02 | ✅美化 | Dashboard卡片：图标+渐变色+悬浮动画。 |
| 7/02 | UI-03 | ✅美化 | 全局样式：卡片圆角+表格暗色+输入框+标签+按钮统一暗色主题。 |
| 7/02 | UI-04 | ✅重写 | TrafficMonitor: 左地图+右数据面板+TrafficBadge组件。 |

### FE-ANALYST-01~05 分析员5页面填充真实内容 (2026-07-12)

**🎯 任务接收**：分析员5个页面填充真实内容，对接后端API+ECharts图表

**💭 分析**：
- 后端API都已就绪（dev分支，91测试通过），需要调用：/carbon/*, /propagation/*, /scenario/*, /predict/accuracy, /traffic/history等
- 需要新建3个API模块：carbon.js, propagation.js, scenario.js
- 5个页面需覆盖：Loading状态、Empty状态、暗色主题

**📝 实现**：

| ID | 页面 | 关键功能 | API调用 |
|----|------|---------|---------|
| FE-ANALYST-01 | ModelsView.vue | KNN/RF状态卡片+MAE/RMSE/MAPE指标+趋势图+参数滑块+重训练 | GET /predict/accuracy |
| FE-ANALYST-02 | PropagationView.vue | 路段选择+步数/时间窗口/阈值+ECharts Tree图+链详情表 | POST /propagation/analyze |
| FE-ANALYST-03 | CarbonView.vue | 日/周/月切换+概览统计+趋势折线+额外排放堆叠+Top10水平柱状 | GET /carbon/trend, /carbon/current, /carbon/sections/top |
| FE-ANALYST-04 | ExploreView.vue | 日期/路段/小时/星期筛选+TrafficBadge+异常橙色高亮+CSV导出 | GET /traffic/history |
| FE-ANALYST-05 | ScenariosView.vue | 场景CRUD+运行+三列对比(基线/干预/改善)+报告导出+发送管理员 | POST /scenario/create, POST /scenario/{id}/run, etc. |

**新增文件**：
- `frontend/src/api/carbon.js` — 碳排放API模块
- `frontend/src/api/propagation.js` — 拥堵传播API模块
- `frontend/src/api/scenario.js` — 场景仿真API模块

**✅ 验证**：`npx vite build` → 2287 modules transformed, 0 errors, 0 warnings

### FE-MAIN-01~04 三角色路由+布局+占位视图 (2026-07-12)

**🎯任务接收**：实现三用户角色平台 Phase 1 — 路由重构 + 管理员/分析员/出行者布局 + 占位视图

**💭分析**：
- 需要从0创建3套布局组件、15个占位视图页、1个JWT解析工具
- 现有MainLayout.vue需保留做向后兼容
- 路由守卫需从JWT payload解析role字段做角色分流
- 出行者布局需移动端优先设计

**📝实现**：
1. `utils/jwt.js` — parseJWT()和getRoleFromToken()函数
2. `store/user.js` — 增强parseRoleFromToken action + isAnalyst/isTraveler getter
3. `router/index.js` — 新增/admin /analyst /traveler三条路由树+完整角色守卫
4. `layouts/AdminLayout.vue` — 280px侧边栏+5菜单项+预警角标+实时时钟+角色标签
5. `layouts/AnalystLayout.vue` — 280px侧边栏+5菜单项+模型状态指示灯+实时时钟
6. `layouts/TravelerLayout.vue` — 移动端底部Tab+≥768px侧边栏+登录引导
7. 15个占位视图: admin(5) + analyst(5) + traveler(5)

**关键决策**：
- 用emoji代替`<el-icon>`组件避免额外依赖
- 路由守卫直接从localStorage读token解析role，不依赖Store初始化时序
- TravelerLayout用`window.innerWidth`响应式检测+resize事件监听
- 模型状态通过`window.__updateModelStatus`暴露给子组件

**✅验证**：`npm run dev` → build成功，零红色错误。15个视图全部import按需加载正常。

### FE-MODEL-CHART 模型评估可视化图表 (2026-07-13)

**🎯 任务接收**：给 ModelsView 增加模型评估可视化图表

**💭 分析**：
- 需要在现有指标卡片下方增加2个ECharts图表
- API未就绪(GET /predict/evaluation不存在)，用硬编码默认数据
- 需要ScatterChart + MarkLineComponent组件
- 按需引入保持构建体积

**📝 实现**：

1. `frontend/src/api/prediction.js` — 新增 `getEvaluation()` 方法
2. `frontend/src/views/analyst/ModelsView.vue`：
   - **KNN vs RF 对比柱状图**：MAE / RMSE / R² 三组对比，KNN蓝色渐变、RF绿色渐变柱体，带tooltip
   - **预测值 vs 实际值散点图**：KNN红点、RF蓝点，对角线y=x参考线，实际值X轴、预测值Y轴
   - 默认数据：`{ metric: "MAE", knn: 158.29, rf: 162.52 }` 等
   - 散点图mock数据随机生成30个点模拟偏差分布
   - 暗色主题适配（splitLine/axisLabel/textStyle统一#8899aa）

**✅ 验证**：`npx vite build` → 2298 modules, 0 errors

**📦 交付**：
- 分支: `feature/agent-frontend-main/FE-MODEL-CHART`
- 文件: `frontend/src/api/prediction.js`, `frontend/src/views/analyst/ModelsView.vue`
- PR: 已推送等待Agent-Lead审查合并

## 思考轨迹

### D6-T03 Vue初始化
**决策**：不依赖Vite交互式CLI，直接写package.json+vite.config.js。所有路由用动态import()懒加载。D6-T04阻塞解除：TrafficMap挂载位已在TrafficMonitor.vue中预留。

### D7-T03 Login/Dashboard
**决策**：登录成功后自动跳转到redirect参数或/dashboard。JWT存在localStorage，请求拦截器自动注入。Dashboard用4个el-card做统计卡片——简洁但信息量够。

### D8-T04 PredictionBoard
**决策**：路段选择+模型切换(RF/KNN)+预测按钮，结果卡片展示predicted_flow+置信区间。ECharts挂载位预留(D11实现图表渲染)。
**依赖**：需要Agent-Algorithm的prediction API返回D4-T02定义的JSON格式。

### D9-T03 RoutePlanner
**决策**：起终点select + el-timeline展示路径序列。调用Leader的route/plan API。暂不集成地图可视化——地图路径展示由Agent-Frontend-Map在D11实现。

### BUG-FE-02 Vite @/ alias
**🎯Bug接收**：系统测试npm run dev报错`@/store/user could not be resolved`。
**💭分析**：D6-T03创建vite.config.js时忘记配置resolve.alias。
**📝修复**：加`resolve.alias: {'@': fileURLToPath(new URL('./src', import.meta.url))}`。
**✅验证**：npm run dev无import解析错误。

### BUG-FE-03~07 前端功能补齐
**问题**：D6-D10期间的页面只有UI壳子，数据显示全是0或空。
**根因**：写代码时未接入真实API——Mock环境下开发，API未就绪时用静态数据。
**修复方案**：
- Dashboard: `onMounted` 调 `statsApi.getDashboard()` → 4张卡片填真实数据
- PredictionBoard: `onMounted` 调 `sectionsApi.getList()` 加载路段 → 选路段+模型 → 调 `predictionApi.getForecast()`
- WarningManager: `onMounted` 调 `warningApi.getList()` → 筛选+解除调 `warningApi.resolve()`
- RoutePlanner: `onMounted` 调 `sectionsApi.getList()` → 起终点→ `routeApi.plan()`
- 新增 `stats.js` API模块（D6遗漏）
**关键决策**：用 `res.data?.items || res?.items` 兼容不同的响应解包方式。

### BUG-TRAFFIC-02 TrafficMonitor数据加载

**🎯Bug接收**：点击路段列表一直显示「加载中」，即使API返回了数据也消不掉。
**💭分析**：(1)onSectionClick调trafficApi.getCurrent(id)但只传单个section_id，其他23个路段trafficData为空→显示「加载中」；(2)空数据判断不准确。
**📝修复**：(1)onMounted时调`loadAllTraffic()`加载全部路段路况数据；(2)加`loadingAll`状态区分首次加载vs无数据；(3)空数据显示「暂无实时数据」而非「加载中」。
**✅验证**：页面加载后24路段全部显示路况badge，点击任一路段右侧面板显示详细数据。

### UI-05 PredictionBoard增强

**问题**：只有单一预测值+无错误提示+无预测序列展示。
**修复**：加预测窗口选择(5/15/30min)、el-alert错误提示、预测序列卡片(每个时间点独立展示)、模拟数据标签提醒。
**新增**：`using_trained_model` 字段展示——无真实模型时显示「模拟」标签。

### BUG-TIMEOUT-01 SUMO仿真超时

**🎯Bug接收**：Agent-Lead分配。用户点击「一键运行仿真」报timeout 15000ms exceeded。
**💭分析**：SUMO仿真需要1-2分钟，但Axios默认timeout=15000(15秒)。request.js全局超时对/sumo/run不适用。
**📝修复**：Dashboard.vue中sumo/run请求单独设置`{ timeout: 180000 }`(3分钟)，覆盖全局15秒超时。
**✅验证**：重启前端后再点按钮不再超时。

### FEAT-PAUSE-03 暂停/继续按钮

**🎯任务**：前端加暂停/继续控制。
**📝修复**：SimulationStore加realtimePaused状态+pauseRealtime()/resumeRealtime()。Dashboard和TrafficMonitor按钮根据运行/暂停状态显示不同组合：运行中→⏸暂停+⏹停止；暂停中→▶继续+⏹停止。

### FEAT-VIZ-01 TrafficMonitor动态渲染

**🎯任务**：实时路况界面静止无动态效果。
**📝修复**：(1)数据变化时路段行0.5秒蓝色闪烁(flash class)；(2)倒计时器「刷新Xs前」秒级更新；(3)数据值CSS transition平滑过渡。
**效果**：启动实时仿真后，路段列表数据波动→闪烁→路况badge实时变化，有真实的「监控大屏」感。

### UI-SIM-01~03 仿真双框布局+全局状态同步

**🎯任务**：Agent-Lead分析。实现首页双列布局(实时+离线并排)、拖拽上传、全局状态同步(切换页不断)。
**📝实现**：
1. simulation.js Store — `realtimeRunning`/`batchRunning`全局状态，`checkStatus()`/`startRealtime()`/`stopRealtime()`/`runBatch()` actions。Pinia ensure跨页面共享。
2. Dashboard — 双列el-row(各50%)。实时侧:启动/停止按钮+状态。离线侧:el-upload drag拖拽上传+提交历史+一键仿真。
3. TrafficMonitor — 读写同一simStore，按钮和状态与Dashboard完全同步。切换页面不断(Store存在Pinia中)。
**决策**：用Pinia Store而非组件间emit/props——仿真状态是全局的，两个页面独立渲染但共享同一个store实例。

### UI-06 Dashboard一键仿真按钮

**🎯任务**：前端添加一键运行SUMO仿真+导入的按钮。
**📝实现**：Dashboard底部增加「SUMO仿真控制」卡片。点击「▶ 一键运行仿真」→ POST /api/v1/sumo/run → 显示加载状态+进度提示(约1-2分钟)→ 成功后显示导入记录数。
**决策**：放在Dashboard而非Traffic页面——仿真属于系统管理操作。

### UI-04 TrafficMonitor重写
**问题**：页面仍是D6骨架「TODO D8: 地图组件 + 实时数据面板」。
**修复**：左地图+右数据面板双栏布局。24路段列表可滚动点击。TrafficBadge组件(畅通🟢/缓行🟡/拥堵🟠/严重🔴)。选中路段调trafficApi.getCurrent()显示实时数据。
### FE-MODEL-CHART 模型评估可视化图表 (2026-07-13)

**任务接收**：给 ModelsView 增加模型评估可视化图表

**分析**：
- 需要在现有指标卡片下方增加2个ECharts图表
- API未就绪(GET /predict/evaluation不存在)，用硬编码默认数据
- 需要ScatterChart + MarkLineComponent组件

**实现**：
1. frontend/src/api/prediction.js — 新增 getEvaluation() 方法
2. frontend/src/views/analyst/ModelsView.vue：
   - KNN vs RF 对比柱状图：MAE / RMSE / R2 三组对比
   - 预测值 vs 实际值散点图：KNN红点、RF蓝点，对角线y=x参考线
   - 硬编码默认数据回退

**验证**：npx vite build -> 2298 modules, 0 errors

**交付**：分支 feature/agent-frontend-main/FE-MODEL-CHART
