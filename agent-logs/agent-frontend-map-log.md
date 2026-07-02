# Agent-Frontend-Map 执行日志

> ⚠️ 只追加不删除。2026-07-02 恢复：曾因Write覆盖丢失详细内容，已从git恢复。

## 操作记录

| 时间 | 任务ID | 类型 | 内容 |
|------|--------|------|------|
| 系统初始化 | — | 📝 | Agent #4 日志创建。角色：前端开发(辅)/地图。 |
| 7/01 | D3-T04 | ✅ | 地图集成方案设计(11章)。5组件+CSS变量+4断点。 |
| 7/01 | D4-T04 | ✅ | WebSocket消息格式规范(5章)。6事件TS Schema。 |
| 7/02 | D6-T04 | ✅ | TrafficMap+SocketClient+AlertPopup(3文件)。 |
| 7/02 | D7-T04 | ✅ | 地图路段标注+点击联动+NotFound页。 |
| 7/02 | UI-01 | ✅修复 | 地图无Key: 显示引导提示+加载失败降级。 |
| 7/02 | 地图修复 | ✅修复 | .env引号导致Key无效 + API URL修正 + marker watch。 |

## 思考轨迹

### D6-T04 高德地图基础
**决策**：高德Key通过import.meta.env读取（不硬编码，符合禁忌#5）。地图异步动态加载（不阻塞首屏）。WebSocket客户端单例模式——多个页面共享一个连接。AlertPopup用Teleport挂载到body，独立于页面层级。

### D7-T04 路段标注
**决策**：TrafficMap从props.sections动态渲染AMap.Marker，点击emit('section-click')给父组件做ECharts联动。标注点用section.coordinates.start定位。
**待做**：热力图(SectionHeatmap)和轨迹动画(VehicleTrajectory)——D11实现。

### UI-01 地图Key缺失处理
**🎯Bug接收**：env中VITE_AMAP_KEY未配置时地图白屏无任何提示。
**💭分析**：TrafficMap的loadAMapScript失败时只console.warn，用户看不到。loadError状态未渲染UI。
**📝修复**：增加loadError UI——显示「地图未配置」引导信息+高德平台链接。加载中显示loading动画。
**✅验证**：无Key时页面不再白屏，显示友好引导。

### 地图.env引号Bug
**🎯Bug接收**：用户配置了Key但地图仍不加载。
**💭分析**：.env中VITE_AMAP_KEY='a7e...'带了单引号。Vite原样读取.env值不去引号，所以import.meta.env.VITE_AMAP_KEY返回的是带引号的字符串。
**📝修复**：去掉引号。同时修正高德JS API URL路径，marker改为watch动态渲染。
**教训**：.env值不要加引号——和Shell变量不同。
