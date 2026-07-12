<template>
  <div class="route-comparison">
    <div class="rc-header">
      <span class="rc-title">路线对比</span>
      <el-tag v-if="recommendedIndex >= 0" size="small" type="success" effect="dark">推荐路线 {{ recommendedIndex + 1 }}</el-tag>
    </div>

    <!-- 路线列表 -->
    <div class="rc-list">
      <div v-for="(route, i) in routes" :key="i"
           class="rc-route"
           :class="{ recommended: i === recommendedIndex }"
           @click="$emit('select-route', i)">
        <div class="rc-route-color" :style="{ background: routeColors[i % routeColors.length] }"></div>
        <div class="rc-route-info">
          <div class="rc-route-name">
            {{ route.name || `路线 ${i + 1}` }}
            <el-tag v-if="i === recommendedIndex" size="small" type="success">推荐</el-tag>
          </div>
          <div class="rc-route-meta">
            <span>{{ route.distance || '--' }} km</span>
            <span class="rc-dot">·</span>
            <span>{{ route.duration || '--' }} min</span>
            <span class="rc-dot">·</span>
            <span :style="{ color: congestionColors[route.congestionLevel] }">
              {{ route.congestionText || '--' }}
            </span>
          </div>
        </div>
        <div class="rc-route-detail" @click.stop="$emit('view-detail', i)">
          <el-icon><ArrowRight /></el-icon>
        </div>
      </div>
    </div>

    <!-- 图例 -->
    <div class="rc-legend">
      <div v-for="(color, i) in routeColors.slice(0, routes.length)" :key="i"
           class="rc-legend-item">
        <span class="rc-legend-line" :style="{
          background: color,
          borderStyle: i === 0 ? 'solid' : (i === 1 ? 'dashed' : 'dotted')
        }"></span>
        <span class="rc-legend-label">{{ routes[i]?.name || `路线 ${i+1}` }}</span>
      </div>
      <div class="rc-legend-item">
        <span class="rc-legend-label" style="color:var(--text-secondary)">
          <span style="display:inline-block;width:10px;height:10px;border-radius:2px;background:#52c41a;margin-right:4px"></span> 畅通
          <span style="display:inline-block;width:10px;height:10px;border-radius:2px;background:#fa8c16;margin-left:8px;margin-right:4px"></span> 拥堵
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ArrowRight } from '@element-plus/icons-vue'

defineProps({
  routes: { type: Array, default: () => [] },
  // routes: [{name, distance, duration, congestionLevel, congestionText, path:[[lng,lat]]}]
  recommendedIndex: { type: Number, default: 0 },
})

defineEmits(['select-route', 'view-detail'])

const routeColors = ['#52c41a', '#1890ff', '#888']
const congestionColors = { low: '#52c41a', medium: '#fa8c16', high: '#f5222d' }
</script>

<style scoped>
.route-comparison {
  background: var(--bg-panel);
  border: 1px solid rgba(255,255,255,.08);
  border-radius: 12px;
  overflow: hidden;
}
.rc-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 14px;
  border-bottom: 1px solid rgba(255,255,255,.06);
}
.rc-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}
.rc-list {
  padding: 8px 0;
}
.rc-route {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  cursor: pointer;
  transition: background .2s;
  border-left: 3px solid transparent;
}
.rc-route:hover, .rc-route.recommended {
  background: rgba(0,212,255,.06);
}
.rc-route.recommended {
  border-left-color: var(--accent-blue);
}
.rc-route-color {
  width: 4px;
  height: 36px;
  border-radius: 2px;
  flex-shrink: 0;
}
.rc-route-info {
  flex: 1;
  min-width: 0;
}
.rc-route-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 6px;
}
.rc-route-meta {
  font-size: 11px;
  color: var(--text-secondary);
  margin-top: 2px;
  display: flex;
  align-items: center;
  gap: 4px;
}
.rc-dot { opacity: .4; }
.rc-route-detail {
  color: var(--text-secondary);
  cursor: pointer;
  padding: 4px;
}
.rc-route-detail:hover { color: var(--accent-blue); }
.rc-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  padding: 8px 14px;
  border-top: 1px solid rgba(255,255,255,.06);
}
.rc-legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
}
.rc-legend-line {
  width: 20px;
  height: 3px;
  border-radius: 1px;
}
.rc-legend-label {
  font-size: 11px;
  color: var(--text-primary);
}
</style>
