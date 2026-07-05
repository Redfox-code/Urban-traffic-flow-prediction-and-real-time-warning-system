# Agent-Lead 执行日志

> ⚠️ 只追加不删除。2026-07-02 恢复：曾因Write覆盖丢失详细内容，已从git恢复。

## 操作记录

| 时间 | 任务ID | 类型 | 内容 |
|------|--------|------|------|
| 系统初始化 | — | 📝 | Agent #1 日志创建。角色：组长/后端架构师。 |
| 7/01 | 站会1 | 📋 | 首次站会。D3待启动。 |
| 7/01 | D3-T01 | ✅ | 总体架构设计(12章)。D3-T05阻塞解除。 |
| 7/01 | 站会2 | 📋 | D3进度80%。D3-T03超时标记。 |
| 7/01 | D4启动 | 🎯 | Sprint启动。D4拆分6任务。 |
| 7/01 | D4-T01 | ✅ | API详细接口规范(10章,30+端点)。 |
| 7/02 | D6启动 | 🎯 | D6 Sprint启动。5任务分配。 |
| 7/02 | D6-T01 | ✅ | Flask脚手架(28文件)。7 Blueprint+8 Model。 |
| 7/02 | D7启动 | 🎯 | D7 Sprint启动。 |
| 7/02 | D7-T01 | ✅ | JWT认证实现(auth_service+auth.py)。 |
| 7/02 | D8-T03 | ✅ | 预警引擎+sections CRUD+stats实现。 |
| 7/02 | D9启动 | 🎯 | D9 Sprint启动。 |
| 7/02 | D9-T02 | ✅ | Dijkstra路径规划(route_service+route_plan)。 |
| 7/02 | D10 | ✅ | 联调+admin页面+集成测试。D3-D10正式完成。 |
| 7/02 | D11-T01 | ✅ | Bug修复: warning分页+Dijkstra haversine坐标。 |
| 7/02 | BUG-BE-02 | ✅修复 | sections/stats全部5端点加@jwt_required()。 |
| 7/02 | BUG-BE-04 | ✅修复 | JWT_SECRET_KEY 21→32字节，消除InsecureKeyLengthWarning。 |
| 7/02 | BUG-BE-05 | ✅修复 | warning/route_plan加@jwt_required()。 |
| 7/02 | BUG-FE-08 | ✅修复 | seed_data.py预置24路段+36检测器+2用户。 |

## 思考轨迹

### D6-T01 Flask脚手架
**决策**：一次注册全部7个Blueprint，Algorithm的prediction.py/traffic.py留骨架。这样Algorithm只需填充实现，不用关心注册逻辑。
**风险**：如果Algorithm修改了Blueprint注册方式，需要我配合调整。

### D7-T01 JWT认证
**决策**：auth_service分离认证逻辑（register_user/authenticate），auth.py只处理HTTP请求。符合MVC三层分离。
**关键**：werkzeug密码哈希不存明文，符合禁忌#5。

### D8-T03 预警+sections CRUD
**决策**：sections CRUD用Flask-SQLAlchemy的paginate，避免手写分页SQL。warning_service用简单阈值规则（85%/95%），后续可扩展。
**风险**：Dijkstra的build_graph基于ID相邻简化，真实路网需要基于coordinates拓扑——D11可优化。

### D9-T02 Dijkstra
**决策**：用heapq实现标准Dijkstra，不引入networkx依赖。build_graph基于路段ID相邻关系简化——适合24路段的SUMO网格。
**已知局限**：图构建假设ID相邻=物理相邻，大型路网需改为坐标拓扑。

### D10 联调总结
**完成**：admin页面(UserManager/SystemLogs)+ 4条集成测试(认证流程/CRUD/路径规划/权限)。
**待做**：D11 Bug修复 + D12演示视频 + D13报告整合。

### D11-T01 Bug修复+代码完善
**步骤1**：修复warning.py——warning/list端点从空数组改为从DB分页查询warning_events表。
**步骤2**：完善route_service.py的build_graph——从基于ID相邻改为haversine坐标距离，1km阈值。
**步骤3**：补齐前端缺失的API模块(traffic.js) + SectionHeatmap组件骨架。

### BUG-BE-02/04/05 JWT保护修复
**🎯Bug接收**：系统测试发现sections/预测端点未认证返回200而非401。
**💭根因分析**：D6搭建Blueprint骨架时只写了端点函数签名，忘记加@jwt_required()装饰器。D7-D8实现业务逻辑时也漏掉了安全检查。
**📝修复**：全部Leader负责的Blueprint（sections 5端点/stats 2端点/warning 4端点/route_plan 2端点）统一加@jwt_required()。auth的login/register保持公开。
**✅验证**：pytest 17 passed，curl测试未认证返回401。
**教训**：速度优先跳过了安全检查。今后每个端点写完curl测试未认证场景。

### BUG-FE-08 Seed数据
**🎯Bug接收**：前端所有页面数据显示0——数据库是空的。
**💭根因**：D6建表但从未插入数据。SQLite dev.db在gitignore中，每次clone都是空库。
**📝修复**：seed_data.py预置2用户(admin+analyst)+24路段(模拟6x4城市路网)+36检测器。
**决策**：用独立Python脚本而非Flask CLI自定义命令——简单直接，课程项目够用。

### BUG-DATA-02 traffic.py数据库集成

**🎯任务**：解决traffic.py只用mock数据、不读数据库的问题。
**💭设计**：/current端点改为双层策略——先查TrafficRecord表是否有数据，有则读最新记录(带`source:'db'`标记)，无则fallback到mock(带`source:'mock'`标记)。前端可通过source字段知道数据来源。
**📝修复**：`_real_traffic(section)`函数从DB查询每个路段最新traffic_record。`_mock_traffic`作为fallback保留。`has_db_data`检查全局是否有记录。
**决策**：保留mock fallback——课程项目阶段SUMIO数据可能不完整，fallback确保系统始终可展示。

### BUG-SUMO-API 一键仿真端点

**🎯任务**：用户不想在终端手动执行3个命令（generate→run→import），希望前端一键完成。
**💭设计**：创建`POST /api/v1/sumo/run`端点，后端用subprocess依次执行3步：生成路网(30s超时)→运行仿真(120s超时)→导入数据库(30s超时)。任一步失败返回具体错误+stderr。
**决策**：同步执行而非Celery异步——课程项目并发量低，1-2分钟等待可接受，前端显示加载状态即可。
**关键**：必须用`sys.executable`而非`python`，确保使用当前虚拟环境的Python。

### FEAT-RT-02/03 实时仿真端点+前端刷新

**🎯任务**：配合Agent-Algorithm的TraCI脚本，实现后端实时仿真控制+前端自动刷新。
**📝修复**：(1)sumo.py新增/run_realtime端点(Popen后台启动)和/status端点；(2)TrafficMonitor每5秒setInterval调用loadAllTraffic()；(3)Dashboard加「启动实时仿真」按钮。
**决策**：复用traffic/current端点+DB——TraCI写入→traffic_records→traffic/current读取→前端5秒刷新→完整闭环。

### BUG-PROG-01 进度条卡21%

**🎯Bug接收**：进度条一直显示21%，即使仿真未运行。
**💭分析**：`.sim_progress`文件在上次测试时被git提交(值21)，拉取后文件一直存在。status端点不检查仿真是否运行就读取进度。
**📝修复**：(1).gitignore加*.sim_progress等临时文件+从git删除旧文件；(2)启动仿真时重置进度为0；(3)status端点只在rt_running时返回进度。
**✅验证**：未启动仿真时进度=0，启动后从0%开始增长。

### FEAT-PAUSE-01 暂停/继续端点

**🎯任务**：用户需要暂停和恢复实时仿真。
**📝修复**：sumo.py新增/sumo/pause(写.pause文件)+/sumo/resume(删.pause文件)+启动时清理旧文件(解决进度条卡21%)。status端点返回realtime_running+batch_running+progress。
**决策**：用文件信号(.pause_realtime)而非进程信号——TraCI脚本每步循环检测文件，简单可靠。

### BUG-SUMO-SYNTAX sumo.py global声明顺序

**🎯Bug接收**：用户报告后端启动报错 `SyntaxError: name '_batch_process' is used prior to global declaration`。
**💭分析**：sumo.py第89行 `except` 块中的 `global _batch_process` 在函数体内使用 `_batch_process.communicate()` 之后——Python要求 `global` 声明必须在任何使用之前。
**📝修复**：(1)`global _batch_process`移到函数顶部并初始化为None；(2)删除except块中的冗余`global`声明。
**✅验证**：`python -c "from app import create_app; create_app()"` 返回 OK。

### BUG-SUMO-02 sumo端点错误信息增强

**🎯分析**：前端报500但无具体错误信息，无法定位根因。
**📝修复**：sumo.py错误返回增加cwd/stdout/stderr详细输出，500响应message包含stderr最后200字符。
**同时修复**：ALGORITHM_DIR加os.path.abspath确保路径正确。
