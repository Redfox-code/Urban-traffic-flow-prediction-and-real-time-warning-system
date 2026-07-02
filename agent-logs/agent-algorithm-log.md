# Agent-Algorithm 执行日志

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

### Bug修复: 检测器 lane ID 不匹配
**问题**：运行 `python run_simulation.py run` 报错 `lane 'north_to_south_0' is not known`。
**原因**：detectors.add.xml 手动编写的 lane ID 与实际 netgenerate 生成的路网不匹配（手工假名 vs sumo实际名）。
**修复**：改为动态生成检测器——generate_detectors() 从生成的 .net.xml 中读取真实 edge/lane ID 并自动写入 detectors.add.xml。
**改动**：run_simulation.py 重写，新增 `generate_detectors()` 函数。

### Bug修复: netgenerate参数错误
**问题**：用户运行 `python run_simulation.py generate` 报错 `No option with the name 'lane-number' exists`。
**原因**：SUMO netgenerate 的正确参数名是 `--default.lanenumber`，不是 `--lane-number`。
**修复**：`--lane-number=3` → `--default.lanenumber=3`。

### D9-T01 RF训练
**决策**：对偶模型策略(KNN+RF)。RF选n_estimators=[100,200]、max_depth=[10,15,None]。引入feature_importance输出——帮助Leader理解哪些因素影响流量最大。
**评估**：evaluator.py用TimeSeriesSplit 5折+MAE/RMSE/MAPE/R2四指标。
