# Agent-Frontend-Main 执行日志

> ⚠️ 只追加不删除。2026-07-02 恢复：合并git历史版本+最新修复。

## 操作记录

| 时间 | 任务ID | 类型 | 内容 |
|------|--------|------|------|
| 系统初始化 | — | 📝 | Agent #3 日志创建。角色：前端开发(主)。 |
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
