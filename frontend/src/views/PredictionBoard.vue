<template>
  <div style="color:var(--text-primary)">
    <h2>流量预测看板</h2>
    <el-row :gutter="20" style="margin-bottom:16px">
      <el-col :span="6"><el-select v-model="sectionId" placeholder="选择路段" style="width:100%" @change="fetchPrediction"><el-option v-for="s in sections" :key="s.id" :label="s.name" :value="s.id" /></el-select></el-col>
      <el-col :span="4"><el-select v-model="model" style="width:100%"><el-option label="随机森林(RF)" value="RF" /><el-option label="KNN回归" value="KNN" /></el-select></el-col>
      <el-col :span="4"><el-select v-model="horizon" style="width:100%"><el-option label="15分钟" :value="15" /><el-option label="30分钟" :value="30" /><el-option label="5分钟" :value="5" /></el-select></el-col>
      <el-col :span="4"><el-button type="primary" @click="fetchPrediction" :loading="loading" style="width:100%">开始预测</el-button></el-col>
    </el-row>

    <el-alert v-if="errorMsg" :title="errorMsg" type="warning" show-icon closable @close="errorMsg=''" style="margin-bottom:16px" />

    <el-card v-if="result" style="background:var(--bg-panel);margin-bottom:16px">
      <div style="display:flex;gap:24px;flex-wrap:wrap">
        <div style="flex:1;min-width:180px">
          <div style="font-size:13px;color:var(--text-secondary)">预测流量</div>
          <div style="font-size:36px;font-weight:bold;color:var(--accent-blue)">{{ result.predicted_flow }} <span style="font-size:14px">veh/h</span></div>
        </div>
        <div style="flex:1;min-width:180px">
          <div style="font-size:13px;color:var(--text-secondary)">置信区间</div>
          <div style="font-size:20px;color:var(--text-primary)">{{ result.confidence_interval?.lower }} ~ {{ result.confidence_interval?.upper }}</div>
        </div>
        <div style="flex:1;min-width:120px">
          <div style="font-size:13px;color:var(--text-secondary)">模型</div>
          <div style="font-size:20px;color:var(--text-primary)">{{ result.model }} <el-tag v-if="!result.using_trained_model" size="small" type="warning">模拟</el-tag></div>
        </div>
      </div>
    </el-card>

    <el-card v-if="result?.predictions" style="background:var(--bg-panel);margin-bottom:16px">
      <template #header><span style="font-weight:bold">&#x1F4C8; 预测序列 ({{ result.horizon }}分钟)</span></template>
      <div style="display:flex;gap:12px;flex-wrap:wrap">
        <div v-for="p in result.predictions" :key="p.timestamp" class="pred-point">
          <div style="font-size:12px;color:var(--text-secondary)">{{ p.timestamp.slice(11,16) }}</div>
          <div style="font-size:20px;font-weight:bold;color:var(--accent-blue)">{{ p.predicted_flow }}</div>
          <div style="font-size:11px;color:var(--text-secondary)">veh/h</div>
        </div>
      </div>
    </el-card>

    <!-- 预测分析报告 -->
    <el-card v-if="analysis" style="background:var(--bg-panel)" class="analysis-card">
      <template #header><span style="font-weight:bold">&#x1F4CA; 预测分析报告</span></template>

      <el-row :gutter="20">
        <!-- 左列：趋势 + 峰值 -->
        <el-col :span="12">
          <!-- 趋势分析 -->
          <div class="analysis-section">
            <div class="section-title">趋势分析</div>
            <div class="trend-row">
              <span class="trend-icon" :class="analysis.trend.direction">
                {{ trendIcon(analysis.trend.direction) }}
              </span>
              <span class="trend-label" :style="{ color: trendColor(analysis.trend.direction) }">
                {{ analysis.trend.direction }}
              </span>
              <span class="trend-value" :style="{ color: trendColor(analysis.trend.direction) }">
                {{ analysis.trend.change_percent > 0 ? '+' : '' }}{{ analysis.trend.change_percent }}%
              </span>
            </div>
            <div class="trend-detail">
              起始流量 {{ analysis.trend.start_flow }} veh/h → 终止流量 {{ analysis.trend.end_flow }} veh/h
            </div>
          </div>

          <!-- 峰值分析 -->
          <div class="analysis-section">
            <div class="section-title">峰值分析</div>
            <div class="peak-grid">
              <div class="peak-item">
                <div class="peak-label">最高</div>
                <div class="peak-val peak-high">{{ analysis.peak.max_flow }}</div>
                <div class="peak-time">{{ analysis.peak.max_time.slice(11,16) }}</div>
              </div>
              <div class="peak-item">
                <div class="peak-label">最低</div>
                <div class="peak-val peak-low">{{ analysis.peak.min_flow }}</div>
                <div class="peak-time">{{ analysis.peak.min_time.slice(11,16) }}</div>
              </div>
            </div>
          </div>
        </el-col>

        <!-- 右列：拥堵风险 + 模型对比 -->
        <el-col :span="12">
          <!-- 拥堵风险评估 -->
          <div class="analysis-section">
            <div class="section-title">拥堵风险评估</div>
            <div class="congestion-level" :class="'level-' + analysis.congestion_risk.level">
              {{ riskLabel(analysis.congestion_risk.level) }}
            </div>
            <el-progress
              :percentage="Math.round(analysis.congestion_risk.probability * 100)"
              :color="riskProgressColor"
              :stroke-width="12"
              :text-inside="false"
              style="margin:8px 0"
            />
            <div style="font-size:12px;color:var(--text-secondary)">
              超过85%容量阈值概率: {{ Math.round(analysis.congestion_risk.probability * 100) }}%
            </div>
            <div style="font-size:12px;color:var(--text-secondary);margin-top:4px">
              {{ analysis.congestion_risk.description }}
            </div>
          </div>

          <!-- 模型对比 -->
          <div class="analysis-section">
            <div class="section-title">模型对比 (RF vs KNN)</div>
            <div class="model-compare-grid">
              <div class="model-bar-group">
                <div class="model-bar-label">RF</div>
                <div class="model-bar-track">
                  <div class="model-bar-fill rf-bar" :style="{ width: modelBarWidth(analysis.comparison.rf_predicted) + '%' }"></div>
                </div>
                <div class="model-bar-val">{{ analysis.comparison.rf_predicted }} veh/h</div>
              </div>
              <div class="model-bar-group">
                <div class="model-bar-label">KNN</div>
                <div class="model-bar-track">
                  <div class="model-bar-fill knn-bar" :style="{ width: modelBarWidth(analysis.comparison.knn_predicted) + '%' }"></div>
                </div>
                <div class="model-bar-val">{{ analysis.comparison.knn_predicted }} veh/h</div>
              </div>
            </div>
            <div style="font-size:12px;color:var(--text-secondary);margin-top:6px">
              差异: {{ analysis.comparison.difference }} veh/h &mdash; {{ analysis.comparison.note }}
            </div>
          </div>
        </el-col>
      </el-row>

      <!-- 模型可靠性 -->
      <el-divider style="border-color:rgba(255,255,255,.08);margin:12px 0" />
      <div class="reliability-row">
        <span class="reliability-badge">模型可靠性</span>
        <span class="reliability-text">最佳模型: {{ analysis.model_reliability.best_model }}</span>
        <span class="reliability-text">RF: MAE={{ analysis.model_reliability.rf_mae }} R&sup2;={{ analysis.model_reliability.rf_r2 }}</span>
        <span class="reliability-text">KNN: MAE={{ analysis.model_reliability.knn_mae }} R&sup2;={{ analysis.model_reliability.knn_r2 }}</span>
      </div>
      <div style="font-size:12px;color:var(--text-secondary);margin-top:4px;padding:0 4px">
        {{ analysis.model_reliability.recommendation }}
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { predictionApi } from '@/api/prediction'
import { sectionsApi } from '@/api/sections'
const sections = ref([]); const sectionId = ref(null); const model = ref('RF')
const horizon = ref(15); const loading = ref(false); const result = ref(null); const analysis = ref(null)
const errorMsg = ref('')

onMounted(async () => {
  try { const res = await sectionsApi.getList(); sections.value = res.data?.items || res?.items || [] } catch {}
})

const fetchPrediction = async () => {
  if (!sectionId.value) { errorMsg.value = '请先选择路段'; return }
  errorMsg.value = ''; loading.value = true; result.value = null; analysis.value = null
  try {
    const res = await predictionApi.getForecast(sectionId.value, horizon.value, model.value)
    result.value = res.data || res
    // 同时获取分析报告
    try {
      const anaRes = await predictionApi.getAnalysis(sectionId.value, horizon.value)
      analysis.value = anaRes.data || anaRes
    } catch { /* 分析报告可选：失败不阻塞主预测 */ }
  } catch (e) { errorMsg.value = e?.message || '预测请求失败，请确认后端已启动' }
  finally { loading.value = false }
}

/** 趋势箭头图标 */
const trendIcon = (direction) => {
  const map = { '上升': '↑', '下降': '↓', '平稳': '→' }
  return map[direction] || '→'
}

/** 趋势颜色 */
const trendColor = (direction) => {
  const map = { '上升': '#f56c6c', '下降': '#67c23a', '平稳': '#909399' }
  return map[direction] || '#909399'
}

/** 拥堵风险标签 */
const riskLabel = (level) => {
  const map = { '低': 'Low ✅', '中': 'Medium ⚠️', '高': 'High 🚨', '严重': 'Critical 🔴' }
  return map[level] || level
}

/** 拥堵风险进度条颜色 */
const riskProgressColor = (percentage) => {
  if (percentage >= 50) return '#f56c6c'
  if (percentage >= 20) return '#e6a23c'
  return '#67c23a'
}

/** 模型对比柱条宽度（最大流量基准） */
const modelBarWidth = (val) => {
  const base = Math.max(analysis.value?.comparison?.rf_predicted || 60, analysis.value?.comparison?.knn_predicted || 60, 60)
  return Math.round((val / base) * 80)
}
</script>

<style scoped>
.analysis-card {
  margin-top: 0;
}
.analysis-section {
  margin-bottom: 16px;
  padding: 8px 12px;
  background: rgba(255,255,255,.02);
  border-radius: 8px;
}
.analysis-section:last-child {
  margin-bottom: 0;
}
.section-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
  padding-bottom: 4px;
  border-bottom: 1px solid rgba(255,255,255,.06);
}
.trend-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.trend-icon {
  font-size: 24px;
  line-height: 1;
}
.trend-label {
  font-size: 18px;
  font-weight: bold;
}
.trend-value {
  font-size: 16px;
  font-weight: bold;
}
.trend-detail {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 4px;
}
.peak-grid {
  display: flex;
  gap: 16px;
}
.peak-item {
  flex: 1;
  text-align: center;
  padding: 8px;
  background: rgba(0,0,0,.15);
  border-radius: 6px;
}
.peak-label {
  font-size: 11px;
  color: var(--text-secondary);
  margin-bottom: 4px;
}
.peak-val {
  font-size: 24px;
  font-weight: bold;
}
.peak-high {
  color: #f56c6c;
}
.peak-low {
  color: #67c23a;
}
.peak-time {
  font-size: 11px;
  color: var(--text-secondary);
  margin-top: 2px;
}
.congestion-level {
  font-size: 16px;
  font-weight: bold;
  margin-bottom: 4px;
}
.level-低 { color: #67c23a; }
.level-中 { color: #e6a23c; }
.level-高 { color: #f56c6c; }
.level-严重 { color: #f56c6c; }
.model-compare-grid {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.model-bar-group {
  display: flex;
  align-items: center;
  gap: 8px;
}
.model-bar-label {
  width: 36px;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-primary);
  text-align: right;
}
.model-bar-track {
  flex: 1;
  height: 16px;
  background: rgba(255,255,255,.06);
  border-radius: 8px;
  overflow: hidden;
}
.model-bar-fill {
  height: 100%;
  border-radius: 8px;
  transition: width .5s ease;
}
.rf-bar {
  background: linear-gradient(90deg, #00d4ff, #409eff);
}
.knn-bar {
  background: linear-gradient(90deg, #a855f7, #6366f1);
}
.model-bar-val {
  width: 70px;
  font-size: 12px;
  color: var(--text-secondary);
  text-align: left;
}
.reliability-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  padding: 0 4px;
}
.reliability-badge {
  font-size: 12px;
  font-weight: 600;
  color: var(--accent-blue);
  padding: 2px 8px;
  border: 1px solid rgba(0,212,255,.3);
  border-radius: 4px;
}
.reliability-text {
  font-size: 12px;
  color: var(--text-secondary);
}
</style>

<style scoped>
.pred-point {
  background: rgba(0,212,255,.06); border-radius: 10px; padding: 12px 16px;
  text-align: center; min-width: 80px;
  border: 1px solid rgba(0,212,255,.12);
}
</style>
