<template>
  <div class="history-view">
    <div class="htv-header">
      <h2>📋 历史记录</h2>
      <div class="htv-header-actions">
        <el-button v-if="history.length > 0" text size="small" @click="refreshHistory" :loading="loading">
          🔄
        </el-button>
        <el-button v-if="history.length > 0" text size="small" type="danger" @click="confirmClearAll">
          🗑️ 清空全部
        </el-button>
      </div>
    </div>

    <!-- 加载体 -->
    <div v-if="loading && history.length === 0" class="htv-loading">
      <el-skeleton :rows="4" animated />
    </div>

    <!-- 空状态 -->
    <el-empty v-else-if="history.length === 0 && !loading"
      description="暂无历史记录">
      <template #image>
        <div class="htv-empty-icon">📋</div>
      </template>
      <p style="color:var(--text-secondary);font-size:13px">
        规划路线后，历史记录会保存在这里
      </p>
      <el-button type="primary" @click="goRoutePlan">🚘 去规划路线</el-button>
    </el-empty>

    <!-- 历史列表 -->
    <template v-else>
      <div class="htv-list">
        <div v-for="(item, i) in history" :key="item.id" class="htv-item">
          <!-- 序号 -->
          <div class="htv-index">{{ i + 1 }}</div>

          <!-- 内容 -->
          <div class="htv-item-body" @click="reloadRoute(item)">
            <div class="htv-route">
              <span class="htv-origin-dot"></span>
              <span class="htv-place">{{ getSectionName(item.origin_section_id) }}</span>
              <span class="htv-arrow">→</span>
              <span class="htv-dest-dot"></span>
              <span class="htv-place">{{ getSectionName(item.dest_section_id) }}</span>
            </div>
            <div class="htv-meta">
              <span v-if="item.distance" class="htv-meta-item">📏 {{ item.distance }} km</span>
              <span v-if="item.estimated_time" class="htv-meta-item">⏱️ {{ item.estimated_time }} min</span>
              <span class="htv-meta-item">📅 {{ formatTime(item.created_at) }}</span>
              <span class="htv-meta-item htv-congestion" :style="{ color: congestionColor(item) }">
                {{ congestionLabel(item) }}
              </span>
            </div>
          </div>

          <!-- 操作 -->
          <div class="htv-actions">
            <el-button circle size="small" @click.stop="reloadRoute(item)" title="重新加载">
              🔄
            </el-button>
            <el-button circle size="small" @click.stop="confirmDelete(item)" title="删除">
              ❌
            </el-button>
          </div>
        </div>
      </div>

      <!-- 分页/底部 -->
      <div class="htv-footer">
        <span class="htv-total">共 {{ total }} 条记录</span>
        <el-button v-if="hasMore" text size="small" @click="loadMore" :loading="loadingMore">
          加载更多
        </el-button>
        <span v-else-if="history.length > 0" class="htv-all-loaded">已显示全部</span>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { travelerApi } from '@/api/traveler'
import { sectionsApi } from '@/api/sections'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()

const history = ref([])
const sections = ref([])
const loading = ref(true)
const loadingMore = ref(false)
const total = ref(0)
const page = ref(1)
const pageSize = 20
const hasMore = ref(false)

// ===== 加载路段列表（用于显示名称） =====
onMounted(async () => {
  try {
    const res = await sectionsApi.getList()
    sections.value = res.data?.items || res?.items || []
  } catch { /* silent */ }
  await refreshHistory()
})

// ===== 加载历史 =====
async function refreshHistory() {
  page.value = 1
  loading.value = true
  try {
    const res = await travelerApi.getHistory({ page: 1, page_size: pageSize })
    const data = res.data || res
    history.value = data?.items || []
    total.value = data?.total || 0
    hasMore.value = history.value.length >= pageSize
  } catch (e) {
    console.warn('加载历史失败', e)
    history.value = []
  } finally {
    loading.value = false
  }
}

async function loadMore() {
  loadingMore.value = true
  page.value++
  try {
    const res = await travelerApi.getHistory({ page: page.value, page_size: pageSize })
    const data = res.data || res
    const items = data?.items || []
    history.value = [...history.value, ...items]
    hasMore.value = items.length >= pageSize
  } catch {
    page.value--
  } finally {
    loadingMore.value = false
  }
}

// ===== 获取路段名称 =====
const sectionMap = ref({})
function getSectionName(id) {
  if (Object.keys(sectionMap.value).length === 0) {
    sections.value.forEach(s => { sectionMap.value[s.id] = s.name })
  }
  return sectionMap.value[id] || `路段#${id}`
}

// ===== 重新加载路线 =====
function reloadRoute(item) {
  const oName = getSectionName(item.origin_section_id)
  const dName = getSectionName(item.dest_section_id)
  router.push({
    name: 'TravelerRoutePlan',
    query: {
      origin_name: oName,
      dest_name: dName,
    }
  })
}

// ===== 删除 =====
function confirmDelete(item) {
  ElMessageBox.confirm(`删除此历史记录？`, '确认', {
    confirmButtonText: '删除',
    cancelButtonText: '取消',
    type: 'warning',
  }).then(async () => {
    try {
      await travelerApi.deleteHistory(item.id)
      history.value = history.value.filter(h => h.id !== item.id)
      total.value--
      ElMessage.success('已删除')
    } catch {
      ElMessage.error('删除失败')
    }
  }).catch(() => {})
}

function confirmClearAll() {
  ElMessageBox.confirm(`确定清空全部 ${total.value} 条历史记录？此操作不可撤销。`, '确认', {
    confirmButtonText: '清空全部',
    cancelButtonText: '取消',
    type: 'warning',
  }).then(async () => {
    try {
      await travelerApi.clearHistory()
      history.value = []
      total.value = 0
      ElMessage.success('已清空全部记录')
    } catch {
      ElMessage.error('清空失败')
    }
  }).catch(() => {})
}

// ===== 辅助 =====
function formatTime(iso) {
  if (!iso) return ''
  try {
    const d = new Date(iso)
    return `${d.getFullYear()}/${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
  } catch { return iso?.slice(0, 16) || '' }
}

function congestionColor(item) {
  // history records may not have traffic data, use generic
  return 'var(--text-secondary)'
}

function congestionLabel(item) {
  // 历史记录可能无路况数据，显示一般信息
  return '📊 历史路线'
}

function goRoutePlan() {
  router.push({ name: 'TravelerRoutePlan' })
}
</script>

<style scoped>
.history-view {
  max-width: 800px;
  margin: 0 auto;
}
.htv-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.htv-header h2 {
  color: var(--text-primary);
  font-size: 20px;
  margin: 0;
}
.htv-header-actions {
  display: flex;
  gap: 8px;
}
.htv-loading {
  padding: 40px 20px;
}
.htv-empty-icon {
  font-size: 60px;
  text-align: center;
  line-height: 1;
}
/* 列表 */
.htv-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.htv-item {
  display: flex;
  align-items: center;
  gap: 12px;
  background: var(--bg-panel);
  border: 1px solid rgba(255,255,255,.06);
  border-radius: 10px;
  padding: 14px 16px;
  transition: border-color .2s;
}
.htv-item:hover {
  border-color: rgba(255,255,255,.12);
}
.htv-index {
  width: 28px;
  height: 28px;
  background: rgba(0,212,255,.1);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: bold;
  color: var(--accent-blue);
  flex-shrink: 0;
}
.htv-item-body {
  flex: 1;
  min-width: 0;
  cursor: pointer;
}
.htv-route {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  margin-bottom: 4px;
}
.htv-origin-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #00e676;
  flex-shrink: 0;
}
.htv-dest-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #f44336;
  flex-shrink: 0;
}
.htv-place {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 150px;
}
.htv-arrow {
  color: var(--text-secondary);
  font-size: 14px;
}
.htv-meta {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}
.htv-meta-item {
  font-size: 12px;
  color: var(--text-secondary);
}
.htv-congestion {
  font-style: italic;
}
.htv-actions {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}
.htv-footer {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 20px 0;
  font-size: 13px;
  color: var(--text-secondary);
}
.htv-total {
  font-size: 12px;
}
.htv-all-loaded {
  font-size: 12px;
  opacity: .6;
}
</style>
