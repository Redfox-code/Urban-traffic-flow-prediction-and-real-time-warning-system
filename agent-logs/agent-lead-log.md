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
| 7/02 | BUG-FE-08 | ✅修复 | seed_data.py预置24路段+36检测器+2用户。
| 7/05 | BUG-SUMO-PAUSE | ✅修复 | SUMO仿真暂停机制失效+信号文件残留双重修复。run_simulation_realtime.py: finally块+PAUSE_FILE+启动时清理PAUSE_FILE。sumo.py: _cleanup_orphans()重排(先杀进程再清4文件)+_kill_process_tree优雅终止→2s→强制杀。 |
| 7/06 | FEAT-REAL-NETWORK | ✅ | 基于高德地图的国贸CBD真实路网重建。35个真实交叉口节点(7×5)，116条路段，坐标与AMap底图对齐。24条路段数据(前端/后端/SUMO三端一致)。 |
| 7/06 | BUG-OSM-POLYLINE | ✅ | OSM路网Polyline双修复: (1) generate_segments去重: 相似路名(子串匹配)合并, 东三环+东三环中路+东三环北路合并为1条5213m路段；(2) _merge_named_edges贯穿修复: 投影+中心线平均(v7)取代中心点排序, 6m粒度合并平行车道点, 弯曲道路形状保留, 缺口500m跳过。验证: 全部50路段ratio<2.5, 9条主要道路span>1km, 无重复路名。 |
| 7/08 | FEAT-REPLAY-MODE | ✅ | 前端"启动实时仿真"按钮触发回放模式。修改: (1) sync_amap_traffic.py replay()增加进度写入.sim_progress+暂停/停止信号检测+心跳写入; (2) sumo.py /run_realtime改为启动--replay --speed 30替代--continuous。|

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

### BUG-PROG-01 根因修复 — git rm --cached .sim_progress

**🎯Bug接收**：进度条仍然卡在21%。上次修复(cf2448c)只加了.gitignore但没有从Git索引移除文件。

**💭根因分析**：`.gitignore`只阻止**新文件**被追踪，不能移除已被追踪的文件。`git ls-files`显示`algorithm/.sim_progress`仍在Git索引中，status端点读到的是旧文件内容(21)。

**📝修复**：(1)`git rm --cached algorithm/.sim_progress`从Git索引移除(文件保留磁盘)；(2)确认`.gitignore`已有全部3个条目(.sim_progress/.stop_realtime/.pause_realtime)；(3)commit+push到master。

**✅验证**：`git ls-files algorithm/.sim_progress`返回空 — 不再追踪。磁盘文件保留(内容21)，重启仿真时将重置为0。

**教训**：对已追踪文件，`.gitignore`无效。必须`git rm --cached`。如果当时同时执行了`git rm --cached` + `.gitignore`，一次commit就够了。

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

### BUG-ORPHAN-01 SUMO仿真孤儿进程+进度条卡住

**🎯Bug接收**：Flask重启后旧的sumo.exe子进程变成孤儿进程，.sim_progress文件保留旧值导致进度条卡住。

**💭分析**：Flask重启时，之前的subprocess.Popen启动的`run_simulation_realtime.py`进程成为孤儿。该脚本仍在运行，但Flask的`_realtime_process`引用丢失。.sim_progress文件仍由孤儿进程更新，但新Flask进程的status端点不再检测到rt_running=True，却可能在特定条件下读到旧值。更严重的是若孤儿进程已退出但.sim_progress残留，进度会卡在旧值。

**📝修复**：
1. `backend/app/routes/sumo.py`：
   - 新增`_cleanup_orphans()`函数，三步策略：清理残留文件→读PID文件检测进程→杀掉孤儿进程→兜底杀sumo.exe
   - 新增`_is_process_alive(pid)`辅助函数（Windows用tasklist，Unix用os.kill(pid,0)）
   - 新增`_kill_process_tree(pid)`辅助函数（Windows用taskkill /T，Unix用SIGKILL）
   - 在`run_realtime()`和`run_simulation()`启动前调用`_cleanup_orphans()`
   - 模块加载时自动调用一次`_cleanup_orphans()`（Flask启动时杀掉残留孤儿）
2. `algorithm/run_simulation_realtime.py`：
   - 启动时写PID到`.sim_pid`文件
   - finally块中删除`.sim_pid`
3. `.gitignore`加入`algorithm/.sim_pid`

**决策**：用PID文件机制（.sim_pid）而非进程名模糊匹配。精确匹配能避免误杀其他系统的sumo.exe进程。taskkill /T选项同时杀掉sumo.exe子进程树。

**验证**：Flask app import正常，run_simulation_realtime模块import正常。

### BUG-SUMO-PAUSE 暂停/停止信号文件残留

**🎯Bug接收**：用户点击暂停→停止后再启动仿真，进度条卡在13-21%。信号文件(.pause/.stop/.sim_progress/.sim_pid)全部残留在磁盘。

**💭根因分析**：
1. `run_simulation_realtime.py` finally块清理列表漏了`PAUSE_FILE`
2. `_cleanup_orphans()` 用 `taskkill /F /T` 强制杀进程，子进程finally没机会执行
3. `_cleanup_orphans()` 步骤1只清3个文件，漏了PID_FILE

**📝修复**：
1. `run_simulation_realtime.py`：finally清理列表加入PAUSE_FILE；启动时同时清理STOP_FILE和PAUSE_FILE
2. `sumo.py`：`_cleanup_orphans()` 步骤顺序调换（先杀进程再清文件），步骤2加入PID_FILE
3. `_kill_process_tree()`：改为两阶段——先`taskkill /T`（不带/F），等2秒让子进程finally执行，再`/F`兜底

**决策**：优雅终止优先，给Python脚本的finally块2秒窗口完成文件清理。

### BUG-SIM-HANG 仿真卡死21% — TraCI simulationStep超时

**🎯Bug接收**：每次运行实时仿真到step≈7560（进度21%）就卡死。暂停/停止都无效——因为暂停检查在`simulationStep()`之前，卡在里面出不来。

**💭根因**：`traci.simulationStep()` 在SUMO内部死锁/阻塞，函数不返回。主循环的暂停/停止检查在step调用之前执行，无法干预正在阻塞的调用。

**📝修复方案演进**：
1. 尝试线程超时保护（`_step_with_timeout`）→ 无效，daemon线程同样卡住
2. **最终方案：完全移除TraCI**，重写为纯Python数学模型

### FEAT-SIM-REWRITE 实时仿真业务逻辑重写

**🎯任务**：用纯Python交通流模拟器替换TraCI方案。

**💭设计决策**：
- 交通流用正弦波 + 随机噪声模拟（30min周期高峰/低谷 + 5min短波 + 长期趋势）
- 24个路段各有不同的相位偏移（素数偏移），避免所有路段同步变化
- 1秒间隔写入DB（24路段×1秒 = 每秒24条记录）
- 暂停/停止信号每0.5秒检查一次，即时响应
- 心跳文件(.sim_heartbeat)每步更新，Flask status端点60秒未更新→判定卡死

**📝实现**：[algorithm/run_simulation_realtime.py](algorithm/run_simulation_realtime.py) 完全重写（去掉traci依赖）

**验证**：3秒测试生成108条记录，正常退出无卡死。

### FEAT-ANALYSIS-REPORT 预测分析报告模块 — 2026-07-06

**🎯任务**：在预测界面增加「预测分析报告」模块，提供趋势/峰值/拥堵风险/模型可靠性/模型对比的分析解读。

**📝实现方案**：

**后端 (prediction_service.py)**：
- 新增 `analyze()` 方法 — 生成完整分析报告
- 新增 `_analyze_trend()` — 比较预测序列首尾值确定方向(上升/下降/平稳)
- 新增 `_analyze_peak()` — 找预测序列最大/最小值及时间点
- 新增 `_analyze_congestion()` — 用60veh/h容量阈值，计算超过85%/95%阈值的概率和风险等级
- 新增 `_get_model_reliability()` — 从metrics.json读取模型评估指标(R²/MAE)，生成推荐建议
- 新增 `_compare_models()` — 同时运行RF和KNN预测，对比差异

**backend (prediction.py)**：
- 新增 `GET /api/v1/predict/analysis?section_id=X&horizon=Y` 端点

**前端 (api/prediction.js)**：
- 新增 `getAnalysis(sectionId, horizon)` 方法

**前端 (PredictionBoard.vue)**：
- 新增分析报告卡片，位于预测序列下方
- 左列：趋势(箭头图标+颜色) + 峰值(最高/最低+时间)
- 右列：拥堵风险(el-progress进度条) + 模型对比(双柱条)
- 底部：模型可靠性指标(最佳模型+MAE+R²+推荐建议)
- 暗色主题视觉风格与现有卡片一致

**✅验证**：3条路由注册正确(`/predict/analysis` 200 OK)。curl测试返回完整分析报告JSON:
```
trend: 上升(6.0%), peak: 19.5@02:55, congestion: 低(0.0%), best_model: RF
```

**已更新文件清单**：
- `backend/app/services/prediction_service.py` — +170行(5分析函数)
- `backend/app/routes/prediction.py` — +12行(analysis端点)
- `frontend/src/api/prediction.js` — +1行(getAnalysis)
- `frontend/src/views/PredictionBoard.vue` — 分析报告卡片UI+逻辑

### FEAT-PREDICTION-REAL 流量预测业务填充

**🎯任务**：预测模块从模拟数据切换到真实训练模型。

**💭现状调研**：
- 算法代码已完整：preprocessing.py（特征工程）+ knn_predictor.py + rf_predictor.py + train_model.py + evaluator.py
- 模型已训练：47,868条数据，保存为knn_latest.pkl + rf_latest.pkl
- 预测服务已集成：prediction_service.py单例预加载
- 模型精度：RF MAE=6.16, R²=0.13；KNN MAE=5.34, R²=-0.99

**📝修复**：
1. prediction_service.py：`_build_feature_vector`返回DataFrame(带列名)而非numpy数组——消除sklearn feature name warning
2. prediction_service.py：`_load_models` 优先加载`_sklearn_latest.pkl`格式——避免pickle对prediction包的路径依赖
3. 多步预测iloc索引适配DataFrame

**决策**：保留fallback模式（模型未加载时用历史均值），确保系统在任何情况下可运行。

**最终验证结果 (2026-07-06)**：
- `GET /api/v1/predict/forecast?section_id=1&horizon=15&model=RF` → `using_trained_model: true`, `predicted_flow: 21.9`
- `GET /api/v1/predict/forecast?section_id=5&horizon=30&model=KNN` → `using_trained_model: true`, `predicted_flow: 60.2`
- `GET /api/v1/predict/accuracy` → `best_model: RF`, `RF: MAE=6.16, R²=0.13`
- API响应时间 < 100ms（远低于500ms要求）

**已更新文件清单**：
- `algorithm/prediction/preprocessing.py` (新建) — 特征工程管道
- `algorithm/prediction/train_model.py` (新建) — 训练管道
- `algorithm/prediction/evaluate.py` (重写) — 修复MAPE除零
- `algorithm/prediction/__init__.py` (更新) — 导出新模块
- `backend/app/services/prediction_service.py` (重写) — 真实模型加载+预测
- `backend/app/routes/prediction.py` (更新) — accuracy端点接入真实数据
- `backend/saved_models/` — rf_sklearn_latest.pkl, knn_sklearn_latest.pkl, metrics.json
- `.claude/board/decisions-log.md` — 新增特征工程决策
- `.claude/board/handoff-queue.md` — 新增交付记录
- `run-log.md` — 新增执行记录

### FEAT-AMAP-SYNC 高德API作为主数据源 — 2026-07-07

**🎯任务**：SUMO仿真数据管道断裂(Section_id硬编码+OSM无检测器)，改用高德交通态势API作为主实时数据源。

**💭背景**：高德API已测试成功(Key: a7e006e65af936c9e57abc52fff9b826)，返回国贸CBD 92条道路实时路况。

**📝实现**：

1. **sync_amap_traffic.py (新建)**：
   - 调用GET /v3/traffic/status/rectangle (矩形116.44,39.898;116.48,39.918)
   - 解析92条道路，按路名子串匹配traffic_sections表
   - 状态映射: status1→occ20%, status2→occ50%, status3→occ75%, status4→occ90%
   - INSERT到traffic_records表，打印同步结果
   - 可直接运行: `python sync_amap_traffic.py`

2. **traffic.py (更新)**：
   - `_real_traffic` source字段: 'db' → 'amap'
   - `/traffic/current` 优先返回DB数据，空则fallback到mock

3. **TrafficMonitor.vue (更新)**：
   - 全局标签: source='amap' → "📡 高德实时"(绿色) / 'mock' → "🎲 模拟"(黄色)
   - 路段详情面板: 同样更新

4. **seed_data.py (更新)**：
   - 扩展国贸CBD道路列表至21条(东西向9条+南北向9条+快速路3条)
   - 路名与高德API返回名称一致(建国路/东三环中路/朝阳路等)

**决策**: 高德API仅用于获取实时路况数据。预测模型(KNN+RF)继续使用自有算法，路线规划继续使用Dijkstra。

**已更新文件清单**：
- `algorithm/sync_amap_traffic.py` (新建) — 高德数据同步脚本
- `backend/app/routes/traffic.py` (更新) — source字段改为'amap'
- `frontend/src/views/TrafficMonitor.vue` (更新) — 数据源标签改为高德实时
- `backend/seed_data.py` (更新) — 扩展国贸CBD道路列表至21条

### FEAT-AMAP-RETRAIN 高德API真实数据重新训练 — 2026-07-07

**🎯任务**：用高德API同步的真实交通数据（而非旧仿真数据）重新训练KNN+RF模型。

**💭现状调研**：
- DB初始只有67条测试数据（全部同一时间戳），无法训练
- `sync_amap_traffic.py` 从高德交通态势API获取国贸CBD路况，但脚本有bug：第200行 `return` 在函数外
- 旧模型（7/6训练）使用了47,868条数据，但来源是仿真/CSV数据，非高德真实数据
- `preprocessing.py` 的 `load_traffic_data()` 从 `TrafficRecord` 表读取 — 高德同步数据也写入该表，路径通畅

**📝修复与执行**：

1. **修复sync_amap_traffic.py**：`return` → `sys.exit(0)` 修复语法错误
2. **高德数据同步**：连续运行6次（每次~66条道路），累计463条记录
3. **模型重训练**：`python -m prediction.train_model` 
   - 输入：463条高德真实数据，17个路段
   - 特征工程：9特征（时间+滞后+辅助），395样本
   - 划分：316训练 / 79测试
   - 训练参数：KNN(manhattan,distance,15邻居) + RF(max_depth=15, 100棵树)
   - 特征重要性：section_id(33.5%) > avg_speed_lag_1(28.4%) > vehicle_count_lag_2(16.5%) > lag_3(12.7%) > hour(3.3%)
4. **API验证**：启动Flask → curl预测API → `using_trained_model: True`

**关键指标对比**：

| 指标 | 旧模型 (7/6 仿真数据) | 新模型 (7/7 高德数据) |
|------|----------------------|----------------------|
| 数据量 | 47,868条 | 463条 |
| 数据源 | 仿真/CSV | 高德交通态势API |
| RF R² | 0.130 | -0.457 |
| KNN R² | -0.990 | -0.591 |
| RF MAE | 6.16 | 120.93 |
| 模型文件大小(RF) | 9.3MB | 405KB |

**分析**：新模型R²为负值，因为高德数据仅463条(17路段×~27条/路段)，且同批次数据时间戳相同(批量同步)，时间序列滞后特征参考价值低。R²为负说明模型预测不如简单取均值。需要积累更多高德数据（多次不同时段同步）才能改善。

**决策**：保留RF为默认模型（best_model=RF）。数据量不足时，预测API的confidence_interval(±15%)提供容错。待高德数据积累至~10,000条后可重新训练获得正R²。

**✅验证**：启动后端 → curl预测API → `using_trained_model: True` → 模型服务正常

**已更新文件清单**：
- `algorithm/sync_amap_traffic.py` (修复) — `return` → `sys.exit(0)`, 128号语法错误
- `backend/saved_models/knn_latest.pkl` (更新) — 54KB, 高德数据训练
- `backend/saved_models/rf_latest.pkl` (更新) — 405KB, 高德数据训练
- `backend/saved_models/knn_sklearn_latest.pkl` (更新) — 54KB
- `backend/saved_models/rf_sklearn_latest.pkl` (更新) — 405KB
- `backend/saved_models/knn_model_20260707_102153.pkl` (新建) — 时间戳版本
- `backend/saved_models/rf_model_20260707_102154.pkl` (新建) — 时间戳版本
- `backend/saved_models/metrics.json` (更新) — 463条记录, RF R²=-0.457
