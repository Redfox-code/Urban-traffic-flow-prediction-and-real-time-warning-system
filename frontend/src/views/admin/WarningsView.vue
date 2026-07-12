<template>
  <div class="warnings-view">
    <!-- 顶部统计 -->
    <div class="warn-stats">
      <div class="warn-stat-item">
        <span class="warn-stat-num" style="color:#f44336">{{ stats.total || 0 }}</span>
        <span class="warn-stat-label">总预警</span>
      </div>
      <div class="warn-stat-item">
        <span class="warn-stat-num" style="color:#ff9800">{{ stats.active || 0 }}</span>
        <span class="warn-stat-label">未解决</span>
      </div>
      <div class="warn-stat-item">
        <span class="warn-stat-num" style="color:#4caf50">{{ stats.resolved || 0 }}</span>
        <span class="warn-stat-label">已解决</span>
      </div>
    </div>

    <!-- 筛选栏 -->
    <el-card shadow="never" class="warn-filter-card">
      <div class="warn-filter-row">
        <el-select v-model="filters.level" placeholder="预警等级" clearable size="default" style="width:130px" @change="fetchList">
          <el-option label="全部等级" value="" />
          <el-option label="提示" value="info" />
          <el-option label="警告" value="warning" />
          <el-option label="严重" value="critical" />
        </el-select>
        <el-select v-model="filters.is_resolved" placeholder="处理状态" clearable size="default" style="width:130px" @change="fetchList">
          <el-option label="全部" value="" />
          <el-option label="未解决" value="false" />
          <el-option label="已解决" value="true" />
        </el-select>
        <el-input v-model="filters.section_id" placeholder="路段ID" clearable size="default" style="width:120px" @clear="fetchList" @keyup.enter="fetchList" />
        <el-button type="primary" size="default" @click="fetchList" :loading="loading">🔍 查询</el-button>
        <div style="flex:1" />
        <el-button size="default" @click="showRules = true">⚙️ 预警规则</el-button>
        <el-button size="default" type="success" @click="batchResolve" :disabled="selectedIds.length === 0">
          ✅ 批量解除 ({{ selectedIds.length }})
        </el-button>
      </div>
    </el-card>

    <!-- 预警表格 -->
    <el-card shadow="never" class="warn-table-card">
      <el-table :data="items" v-loading="loading" size="default" @selection-change="onSelectChange" style="width:100%">
        <el-table-column type="selection" width="40" />
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="section_id" label="路段" width="70" />
        <el-table-column prop="level" label="等级" width="85">
          <template #default="{row}">
            <el-tag size="small" :type="levelTagType(row.level)" effect="dark">{{ levelLabel(row.level) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="message" label="预警消息" min-width="180" show-overflow-tooltip />
        <el-table-column prop="trigger_flow" label="触发流量" width="90">
          <template #default="{row}">{{ row.trigger_flow }} veh/h</template>
        </el-table-column>
        <el-table-column prop="threshold" label="阈值" width="70">
          <template #default="{row}">{{ row.threshold }}%</template>
        </el-table-column>
        <el-table-column prop="is_resolved" label="状态" width="80">
          <template #default="{row}">
            <el-tag size="small" :type="row.is_resolved ? 'success' : 'danger'" effect="plain">
              {{ row.is_resolved ? '已解决' : '未解决' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="时间" width="160">
          <template #default="{row}">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{row}">
            <el-button v-if="!row.is_resolved" type="primary" link size="small" @click="resolveOne(row.id)">解除</el-button>
            <span v-else style="color:var(--text-secondary);font-size:12px">—</span>
          </template>
        </el-table-column>
      </el-table>
      <div class="warn-pagination" v-if="total > 0">
        <el-pagination v-model:current-page="pagination.page" :page-size="pagination.page_size" :total="total"
          layout="total, prev, pager, next" @current-change="fetchList" />
      </div>
    </el-card>

    <!-- 预警规则弹窗 -->
    <el-dialog v-model="showRules" title="⚙️ 预警规则配置" width="480px" destroy-on-close>
      <el-form label-width="130px" size="default">
        <el-form-item label="预警触发阈值">
          <el-input-number v-model="rules.warning_threshold" :min="0.1" :max="0.99" :step="0.01" :precision="2" />
          <span style="color:var(--text-secondary);font-size:12px;margin-left:8px">占有率超过此值触发 warning</span>
        </el-form-item>
        <el-form-item label="严重预警阈值">
          <el-input-number v-model="rules.critical_threshold" :min="0.1" :max="0.99" :step="0.01" :precision="2" />
        </el-form-item>
        <el-form-item label="最小数据点数">
          <el-input-number v-model="rules.min_data_points" :min="1" :max="20" :step="1" />
        </el-form-item>
        <el-form-item label="冷却时间(分)">
          <el-input-number v-model="rules.cooldown_minutes" :min="1" :max="120" :step="5" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showRules = false">取消</el-button>
        <el-button type="primary" @click="saveRules" :loading="savingRules">保存规则</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { warningApi } from '@/api/warning'
import { ElMessage, ElMessageBox } from 'element-plus'

const items = ref([])
const loading = ref(false)
const total = ref(0)
const selectedIds = ref([])
const showRules = ref(false)
const savingRules = ref(false)

const filters = reactive({ level: '', is_resolved: 'false', section_id: '' })
const pagination = reactive({ page: 1, page_size: 20 })
const stats = reactive({ total: 0, active: 0, resolved: 0 })
const rules = reactive({ warning_threshold: 0.85, critical_threshold: 0.95, min_data_points: 4, cooldown_minutes: 30 })

async function fetchList() {
  loading.value = true
  try {
    const params = { page: pagination.page, page_size: pagination.page_size }
    if (filters.level) params.level = filters.level
    if (filters.is_resolved !== '') params.is_resolved = filters.is_resolved
    if (filters.section_id) params.section_id = filters.section_id
    const res = await warningApi.getList(params)
    const data = res.data?.data || res.data || {}
    items.value = data.items || []
    total.value = data.total || 0
  } catch (e) { console.warn('获取预警列表失败', e) }
  finally { loading.value = false }
}

async function fetchStats() {
  try {
    const [allRes, activeRes, resolvedRes] = await Promise.all([
      warningApi.getList({ page: 1, page_size: 1 }).catch(() => ({ data: { data: { total: 0 } } })),
      warningApi.getList({ page: 1, page_size: 1, is_resolved: 'false' }).catch(() => ({ data: { data: { total: 0 } } })),
      warningApi.getList({ page: 1, page_size: 1, is_resolved: 'true' }).catch(() => ({ data: { data: { total: 0 } } })),
    ])
    stats.total = (allRes.data?.data || allRes.data || {}).total || 0
    stats.active = (activeRes.data?.data || activeRes.data || {}).total || 0
    stats.resolved = (resolvedRes.data?.data || resolvedRes.data || {}).total || 0
  } catch { /* silence */ }
}

async function resolveOne(id) {
  try { await ElMessageBox.confirm('确认解除此预警？', '解除预警', { confirmButtonText: '确认', cancelButtonText: '取消', type: 'warning' }) }
  catch { return }
  try { await warningApi.resolve(id); ElMessage.success('预警已解除'); fetchList(); fetchStats() }
  catch { ElMessage.error('解除失败') }
}

async function batchResolve() {
  try { await ElMessageBox.confirm(`确认批量解除 ${selectedIds.value.length} 条预警？`, '批量解除', { confirmButtonText: '确认', type: 'warning' }) }
  catch { return }
  let count = 0
  for (const id of selectedIds.value) { try { await warningApi.resolve(id); count++ } catch { /* skip */ } }
  ElMessage.success(`已解除 ${count} 条`)
  selectedIds.value = []; fetchList(); fetchStats()
}

function onSelectChange(selection) { selectedIds.value = selection.map(s => s.id) }

async function loadRules() {
  try { const res = await warningApi.getRules(); Object.assign(rules, res.data?.data || res.data || {}) } catch { /* use defaults */ }
}
async function saveRules() {
  savingRules.value = true
  try { await warningApi.updateRules({ ...rules }); ElMessage.success('规则已保存'); showRules.value = false }
  catch { ElMessage.error('保存失败') }
  finally { savingRules.value = false }
}

function levelTagType(level) { return level === 'critical' ? 'danger' : level === 'warning' ? 'warning' : 'info' }
function levelLabel(level) { return level === 'critical' ? '🔴 严重' : level === 'warning' ? '🟡 警告' : '🟢 提示' }
function formatTime(iso) { if (!iso) return ''; try { return iso.replace('T', ' ').slice(0, 19) } catch { return iso } }

onMounted(async () => { await Promise.all([fetchList(), fetchStats(), loadRules()]) })
</script>

<style scoped>
.warnings-view { max-width: 1400px; }
.warn-stats { display: flex; gap: 24px; margin-bottom: 12px; }
.warn-stat-item { text-align: center; }
.warn-stat-num { font-size: 28px; font-weight: 700; }
.warn-stat-label { font-size: 12px; color: var(--text-secondary); margin-top: 2px; display: block; }
.warn-filter-card { background: var(--bg-panel); margin-bottom: 12px; }
.warn-filter-row { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
.warn-table-card { background: var(--bg-panel); }
.warn-pagination { display: flex; justify-content: flex-end; margin-top: 12px; }
</style>
