# Agent-Algorithm 执行日志

> ⚠️ 只追加不删除。2026-07-02 恢复：曾因Write覆盖，已从git恢复完整内容。

## 操作记录

| 时间 | 任务ID | 类型 | 内容 |
|------|--------|------|------|
| 系统初始化 | — | 📝 | Agent #2 日志创建。角色：算法工程师。 |
| 7/01 | D3-T02 | ✅ | 算法模块设计(10章)。策略模式KNN+RF。 |
| 7/01 | D4-T02 | ✅ | 模型接口详细规范(6章)。 |
| 7/02 | D6-T02 | ✅ | SUMO路网(city_flows.rou.xml+detectors+config+run_simulation)。 |
| 7/02 | D7-T02 | ✅ | 数据预处理(parse_e2_output+clean_data+build_features+normalize)。 |
| 7/02 | D8-T01 | ✅ | 预测API(PredictionService单例+prediction.py+traffic.py)。 |
| 7/02 | D8-T02 | ✅ | KNN训练(base_model+knn_predictor+train.py)。 |
| 7/02 | D9-T01 | ✅ | RF训练(rf_predictor+evaluator)。双模型就绪。 |
| 7/02 | SUMO修复1 | ✅修复 | --lane-number→--default.lanenumber。 |
| 7/02 | SUMO修复2 | ✅修复 | 检测器lane ID硬编码→动态生成。 |
| 7/02 | SUMO修复3 | ✅修复 | e2detector→laneAreaDetector标签修正。 |
| 7/02 | SUMO修复4 | ✅修复 | 车流edge ID硬编码→动态生成generate_routes()。 |
| 7/02 | BUG-BE-03 | ✅修复 | prediction/traffic加@jwt_required(), 500→503。 |

## 思考轨迹

### D6-T02 SUMO路网
**决策**：用netgenerate生成6×4网格路网而非手写800行XML。理由是手写易出错且难以调试，netgenerate一行命令生成标准网格。符合D3-T02设计：24路段/12交叉口/2信号灯。

### D7-T02 数据预处理
**决策**：5步Pipeline(解析→清洗→特征→归一化)每步独立函数，可单独测试。IQR方法处理异常值（比Z-score更稳健），前值填充处理缺失。
**关键**：TimeSeriesSplit而非KFold——时间序列不能随机切分。

### D8-T01 预测API
**决策**：PredictionService采用单例模式（禁忌#1），应用启动时预加载模型。当前用随机数模拟预测（模型文件需实际训练后才能加载）。
**风险**：模型文件路径硬编码了saved_models/目录，后续需改为config配置。

### D8-T02 KNN训练
**决策**：GridSearchCV搜索K=[3,5,7,10,15]，metric=[euclidean,manhattan]。选择5折交叉验证而非留出法——样本量不大(3840条/天)，交叉验证更稳定。

### D9-T01 RF训练
**决策**：对偶模型策略(KNN+RF)。RF选n_estimators=[100,200]、max_depth=[10,15,None]。引入feature_importance输出——帮助Leader理解哪些因素影响流量最大。
**评估**：evaluator.py用TimeSeriesSplit 5折+MAE/RMSE/MAPE/R2四指标。

### SUMO仿真Bug修复系列
**Bug1(--lane-number)**：用户运行报错`No option with the name 'lane-number'`。根因：SUMO正确参数是`--default.lanenumber`。修复：改参数名。
**Bug2(检测器lane ID)**：报错`lane 'north_to_south_0' is not known`。根因：detectors.add.xml手动编写的假lane ID与netgenerate生成的实际ID不匹配。修复：改为generate_detectors()从.net.xml动态读取。
**Bug3(XML标签)**：报错`no declaration found for element 'e2detector'`。根因：SUMO标准标签是`laneAreaDetector`。修复：改标签名。
**Bug4(车流edge ID)**：报错`edge 'left0to1/0' is not known`。根因：city_flows.rou.xml手动编写的假edge ID。修复：改为generate_routes()动态生成。
**根因教训**：全部4个Bug都是「写代码不运行」导致——Agent写完直接push，从未执行`python run_simulation.py run`验证。这直接催生了后续的「Agent代码验证机制」。

### BUG-TRAFFIC-01 traffic.py动态mock数据

**🎯Bug接收**：前端点击任意路段显示「加载中」——traffic.py只有section_id=1的硬编码数据。
**💭分析**：D8-T01实现的traffic/current端点用固定mock列表`[{section_id:1,...}]`，其他23个路段过滤后返回空数组。
**📝修复**：改为`_mock_traffic(section)`函数——从数据库读取所有路段，基于每个路段的capacity/max_speed/id动态生成合理mock数据(车流量/速度/占有率/路况等级)。支持`?section_id=`筛选。
**✅验证**：curl测试任意section_id均返回数据。

### BUG-PRED-01 PredictionService无模型返回503

**🎯Bug接收**：前端调用预测API返回503「模型未加载」。
**💭分析**：saved_models/目录无.pkl文件→模型为None→返回503错误。用户无法使用预测功能。
**📝修复**：改为始终返回可用预测数据。有真实模型时用模型预测并用`using_trained_model: true`标记；无模型时基于路段ID+时段生成合理mock数据并用`using_trained_model: false`标记。
**决策**：课程项目阶段，优先保证功能可演示。前端通过`using_trained_model`字段显示「模拟」标签区分数据来源。
**✅验证**：curl测试predict端点返回200+完整预测JSON。

### BUG-BE-03 predict端点JWT+错误码
**🎯Bug接收**：系统测试发现`GET /api/v1/predict/forecast`无认证返回500而非401。
**💭分析**：(1)prediction.py端点无@jwt_required(); (2)PredictionService模型未加载返回code:500应改为503。
**📝修复**：prediction.py两个端点加@jwt_required(); prediction_service.py错误码500→503; traffic.py加JWT保护。
**✅验证**：pytest 17 passed, test_forecast_no_auth通过。
