<template>
  <div class="alerts-view">
    <h2 class="alerts-title">🔔 出行提醒</h2>

    <!-- ===== 提醒设置 ===== -->
    <el-card shadow="never" class="alerts-settings-card">
      <template #header>
        <span style="font-weight:bold;color:var(--text-primary)">⚙️ 提醒设置</span>
      </template>
      <div class="alerts-settings">
        <!-- 通勤提醒 -->
        <div class="alerts-setting-row">
          <div class="alerts-setting-info">
            <div class="alerts-setting-label">通勤提醒</div>
            <div class="alerts-setting-desc">出发前推送路况预警</div>
          </div>
          <el-switch v-model="settings.commuteAlert" @change="onSettingsChange" />
        </div>
        <div v-if="settings.commuteAlert" class="alerts-setting-extras">
          <div class="alerts-setting-row">
            <div class="alerts-setting-info">
              <div class="alerts-setting-label">提前提醒时间</div>
              <div class="alerts-setting-desc">出发前多久推送</div>
            </div>
            <el-select v-model="settings.alertBeforeMin" size="small" style="width:100px" @change="onSettingsChange">
              <el-option :value="10" label="10分钟" />
              <el-option :value="15" label="15分钟" />
              <el-option :value="30" label="30分钟" />
              <el-option :value="60" label="60分钟" />
            </el-select>
          </div>
        </div>

        <!-- 晚间提醒 -->
        <div class="alerts-setting-row">
          <div class="alerts-setting-info">
            <div class="alerts-setting-label">晚间路况提醒</div>
            <div class="alerts-setting-desc">17:00-20:00 晚高峰推送</div>
          </div>
          <el-switch v-model="settings.eveningAlert" @change="onSettingsChange" />
        </div>
      </div>
    </el-card>

    <!-- ===== 提醒历史 ===== -->
    <div class="alerts-list-header">
      <h3>📋 提醒历史</h3>
      <el-button v-if="alerts.length > 0" text size="small" @click="markAllRead" :loading="markingAll">
        全部标为已读
      </el-button>
    </div>

    <!-- 加载体 -->
    <div v-if="loading && alerts.length === 0" class="alerts-loading">
      <el-skeleton :rows="4" animated />
    </div>

    <!-- 空状态 -->
    <el-empty v-else-if="alerts.length === 0 && !loading"
      description="暂无出行提醒">
      <template #image>
        <div class="alerts-empty-icon">🔔</div>
      </template>
      <p style="color:var(--text-secondary);font-size:13px">
        开启通勤提醒后，出发前会自动推送路况预警
      </p>
    </el-empty>

    <!-- 提醒列表 -->
    <div v-else ref="listRef" class="alerts-list" @scroll="onScroll">
      <div
        v-for="a in alerts"
        :key="a.id"
        class="alerts-item"
        :class="{ 'alerts-item-unread': !a.is_read }"
        @click="onAlertClick(a)"
      >
        <!-- 未读竖线 -->
        <div v-if="!a.is_read" class="alerts-unread-bar"></div>

        <!-- 内容 -->
        <div class="alerts-item-body">
          <div class="alerts-item-top">
            <el-tag size="small" :type="alertType(a.alert_type)" effect="dark" class="alerts-type-tag">
              {{ alertTypeLabel(a.alert_type) }}
            </el-tag>
            <span class="alerts-time">{{ formatTime(a.created_at) }}</span>
          </div>
          <div class="alerts-title" :class="{ 'alerts-title-unread': !a.is_read }">
            {{ a.title }}
          </div>
          <div v-if="a.message" class="alerts-message">{{ a.message }}</div>
          <div class="alerts-item-bottom">
            <span v-if="a.suggested_action" class="alerts-action">{{ a.suggested_action }}</span>
            <el-button
              v-if="a.alert_type === 'congestion'"
              text size="small" type="primary"
              @click.stop="viewAlternative(a)">
              查看备选路线 →
            </el-button>
          </div>
        </div>
      </div>

      <!-- 加载更多 -->
      <div v-if="loadingMore" class="alerts-loading-more">
        <el-icon class="is-loading" :size="16"><Loading /></el-icon> 加载中...
      </div>
      <div v-if="!hasMore && alerts.length > 0" class="alerts-no-more">
        — 已显示全部提醒 —
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { travelerApi } from '@/api/traveler'
import { ElMessage } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'

const router = useRouter()

// ===== 设置 =====
const settings = reactive({
  commuteAlert: false,
  alertBeforeMin: 15,
  eveningAlert: false,
})

// ===== 提醒列表 =====
const alerts = ref([])
const loading = ref(true)
const loadingMore = ref(false)
const markingAll = ref(false)
const hasMore = ref(true)
const page = ref(1)
const pageSize = 20

// ===== 加载 =====
async function loadAlerts() {
  if (page.value === 1) loading.value = true
  try {
    const res = await travelerApi.getAlerts({ page: page.value, page_size: pageSize })
    const data = res.data || res
    const items = data?.items || []
    if (page.value === 1) {
      alerts.value = items
    } else {
      alerts.value = [...alerts.value, ...items]
    }
    hasMore.value = items.length >= pageSize
  } catch (e) {
    console.warn('加载提醒失败', e)
    if (page.value === 1) alerts.value = []
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

onMounted(loadAlerts)

// ===== 无限滚动 =====
function onScroll(e) {
  if (!hasMore.value || loadingMore.value) return
  const el = e.target
  if (el.scrollHeight - el.scrollTop - el.clientHeight < 100) {
    loadingMore.value = true
    page.value++
    loadAlerts()
  }
}

// ===== 标记已读 =====
async function onAlertClick(a) {
  if (!a.is_read) {
    try {
      await travelerApi.markRead(a.id)
      a.is_read = true
    } catch { /* silent */ }
  }
}

async function markAllRead() {
  const ids = alerts.value.filter(a => !a.is_read).map(a => a.id)
  if (ids.length === 0) {
    ElMessage.info('没有未读提醒')
    return
  }
  markingAll.value = true
  try {
    await travelerApi.batchRead(ids)
    alerts.value.forEach(a => { a.is_read = true })
    ElMessage.success(`已标记 ${ids.length} 条已读`)
  } catch {
    ElMessage.error('操作失败')
  } finally {
    markingAll.value = false
  }
}

// ===== 设置更新 =====
async function onSettingsChange() {
  try {
    // 需要profile_id才能更新，此处只做本地保存；有profile时更新
    if (settings.profileId) {
      await travelerApi.updateAlertSettings({
        profile_id: settings.profileId,
        alert_enabled: settings.commuteAlert,
        alert_before_min: settings.alertBeforeMin,
      })
    }
  } catch { /* silent */ }
}

// ===== 查看备选路线 =====
function viewAlternative(a) {
  router.push({ name: 'TravelerRoutePlan' })
}

// ===== 类型映射 =====
const alertTypeMap = {
  congestion: { type: 'danger', label: '🚨 拥堵预警' },
  info: { type: 'info', label: 'ℹ️ 信息' },
  emergency: { type: 'danger', label: '⚠️ 紧急' },
  warning: { type: 'warning', label: '⚠️ 警告' },
  general: { type: 'info', label: '📢 通知' },
}

function alertType(type) {
  return alertTypeMap[type]?.type || 'info'
}

function alertTypeLabel(type) {
  return alertTypeMap[type]?.label || type || '通知'
}

function formatTime(iso) {
  if (!iso) return ''
  try {
    const d = new Date(iso)
    const now = new Date()
    const diff = now - d
    if (diff < 60000) return '刚刚'
    if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
    return `${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
  } catch { return iso?.slice(5, 16) || '' }
}
</script>

<style scoped>
.alerts-view {
  max-width: 800px;
  margin: 0 auto;
}
.alerts-title {
  color: var(--text-primary);
  font-size: 20px;
  margin: 0 0 16px 0;
}
/* 设置卡片 */
.alerts-settings-card {
  margin-bottom: 20px;
}
.alerts-settings {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.alerts-setting-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 0;
  border-bottom: 1px solid rgba(255,255,255,.04);
}
.alerts-setting-row:last-child {
  border-bottom: none;
}
.alerts-setting-info {
  flex: 1;
}
.alerts-setting-label {
  font-size: 14px;
  color: var(--text-primary);
  font-weight: 500;
}
.alerts-setting-desc {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 2px;
}
.alerts-setting-extras {
  padding-left: 16px;
  border-left: 2px solid var(--accent-blue);
  margin-left: 4px;
}
/* 列表头部 */
.alerts-list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.alerts-list-header h3 {
  font-size: 16px;
  color: var(--text-primary);
  margin: 0;
}
/* 列表 */
.alerts-list {
  max-height: 500px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.alerts-item {
  display: flex;
  gap: 0;
  background: var(--bg-panel);
  border: 1px solid rgba(255,255,255,.06);
  border-radius: 10px;
  overflow: hidden;
  cursor: pointer;
  transition: border-color .2s;
}
.alerts-item:hover {
  border-color: rgba(255,255,255,.12);
}
.alerts-item-unread {
  border-color: rgba(0,212,255,.2);
}
.alerts-unread-bar {
  width: 4px;
  background: var(--accent-blue);
  flex-shrink: 0;
}
.alerts-item-body {
  flex: 1;
  padding: 14px 16px;
}
.alerts-item-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}
.alerts-type-tag {
  flex-shrink: 0;
}
.alerts-time {
  font-size: 11px;
  color: var(--text-secondary);
  white-space: nowrap;
  margin-left: 8px;
}
.alerts-title {
  font-size: 14px;
  color: var(--text-primary);
  margin-bottom: 4px;
  line-height: 1.5;
}
.alerts-title-unread {
  font-weight: 700;
  color: var(--accent-blue);
}
.alerts-message {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 8px;
  line-height: 1.5;
}
.alerts-item-bottom {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px;
}
.alerts-action {
  font-size: 12px;
  color: var(--text-secondary);
  font-style: italic;
}
/* 加载状态 */
.alerts-loading {
  padding: 40px 20px;
}
.alerts-empty-icon {
  font-size: 60px;
  text-align: center;
  line-height: 1;
}
.alerts-loading-more {
  text-align: center;
  padding: 16px;
  color: var(--text-secondary);
  font-size: 13px;
}
.alerts-no-more {
  text-align: center;
  padding: 16px;
  color: var(--text-secondary);
  font-size: 12px;
  opacity: .6;
}
</style>
