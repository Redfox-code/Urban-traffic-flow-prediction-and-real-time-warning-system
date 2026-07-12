<template>
  <div class="area-selector">
    <!-- 模式切换 -->
    <div class="as-toolbar" v-if="!enabled">
      <el-button size="small" type="primary" @click="enableBoxSelect" :disabled="mode !== null">
        ▭ 框选区域
      </el-button>
      <el-button size="small" plain @click="enableMultiSelect" :disabled="mode !== null">
        👆 点击多选
      </el-button>
    </div>

    <!-- 激活状态提示 -->
    <div v-if="mode === 'box'" class="as-hint as-hint-box">
      <span>拖拽选择矩形区域</span>
      <el-button size="small" circle @click="cancelSelect">✕</el-button>
    </div>
    <div v-if="mode === 'multi'" class="as-hint as-hint-multi">
      <span>点击路段选择（已选 {{ selectedIds.length }} 条）</span>
      <el-button size="small" circle @click="cancelSelect">✕</el-button>
    </div>

    <!-- 选中结果 -->
    <div v-if="selectedIds.length > 0 && !mode" class="as-result">
      <div class="as-result-header">
        <span>已选中 {{ selectedIds.length }} 个路段</span>
      </div>
      <el-scrollbar max-height="120px">
        <div v-for="id in selectedIds" :key="id" class="as-result-item">
          {{ getSectionName(id) }}
          <el-tag size="small" type="info">{{ id }}</el-tag>
        </div>
      </el-scrollbar>
      <div class="as-result-actions">
        <el-button size="small" type="primary" @click="$emit('confirm', selectedSections)">确认</el-button>
        <el-button size="small" @click="clearSelection">取消</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ROAD_SEGMENTS } from '@/data/roadNetwork'

const props = defineProps({
  map: { type: Object, required: true },
  enabled: { type: Boolean, default: false },
})

const emit = defineEmits(['confirm', 'cancel'])

const mode = ref(null) // null | 'box' | 'multi'
const selectedIds = ref([])
const tempHighlight = ref([]) // 高亮Polyline
let mouseTool = null
let clickHandler = null

const selectedSections = computed(() => {
  return selectedIds.value.map(id => ROAD_SEGMENTS.find(s => s.id === id)).filter(Boolean)
})

const getSectionName = (id) => {
  const seg = ROAD_SEGMENTS.find(s => s.id === id)
  return seg?.name || `路段 #${id}`
}

const enableBoxSelect = () => {
  if (!props.map || !window.AMap) return
  mode.value = 'box'

  // 使用AMap.MouseTool绘制矩形
  if (!mouseTool) {
    mouseTool = new AMap.MouseTool(props.map)
  }

  mouseTool.rectangle({
    fillColor: 'rgba(0,212,255,.15)',
    strokeColor: '#00d4ff',
    strokeWeight: 2,
  })

  mouseTool.on('draw', (e) => {
    const bounds = e.obj.getBounds()
    // 查找矩形内的路段
    const inside = ROAD_SEGMENTS.filter(seg => {
      return seg.path.some(p => bounds.contains(p))
    })
    selectedIds.value = [...new Set([...selectedIds.value, ...inside.map(s => s.id)])]
    highlightSections(inside)
    mouseTool.close()
    mode.value = null
  })
}

const enableMultiSelect = () => {
  if (!props.map) return
  mode.value = 'multi'

  clickHandler = (e) => {
    const lnglat = e.lnglat
    if (!lnglat) return
    // 查找最近路段
    let minDist = Infinity
    let nearest = null
    ROAD_SEGMENTS.forEach(seg => {
      seg.path.forEach(p => {
        const d = Math.sqrt((p[0] - lnglat.lng) ** 2 + (p[1] - lnglat.lat) ** 2)
        if (d < minDist) { minDist = d; nearest = seg }
      })
    })
    if (nearest && minDist < 0.01) {
      const idx = selectedIds.value.indexOf(nearest.id)
      if (idx >= 0) {
        selectedIds.value.splice(idx, 1)
      } else {
        selectedIds.value.push(nearest.id)
      }
      selectedIds.value = [...selectedIds.value]
      highlightSectionsById(selectedIds.value)
    }
  }

  props.map.on('click', clickHandler)
}

const cancelSelect = () => {
  clearTemp()
  emit('cancel')
}

const clearSelection = () => {
  selectedIds.value = []
  clearTemp()
}

const clearTemp = () => {
  if (mouseTool) { mouseTool.close(); mouseTool = null }
  if (clickHandler && props.map) {
    props.map.off('click', clickHandler)
    clickHandler = null
  }
  tempHighlight.value.forEach(p => props.map?.remove(p))
  tempHighlight.value = []
  mode.value = null
}

const highlightSections = (sections) => {
  sections.forEach(seg => {
    const polyline = new AMap.Polyline({
      path: seg.path,
      strokeColor: '#00d4ff',
      strokeWeight: 8,
      strokeOpacity: 0.5,
      lineJoin: 'round',
      zIndex: 60,
    })
    props.map?.add(polyline)
    tempHighlight.value.push(polyline)
  })
}

const highlightSectionsById = (ids) => {
  tempHighlight.value.forEach(p => props.map?.remove(p))
  tempHighlight.value = []
  ids.forEach(id => {
    const seg = ROAD_SEGMENTS.find(s => s.id === id)
    if (seg) highlightSections([seg])
  })
}

defineExpose({ selectedIds, selectedSections, clearSelection })
</script>

<style scoped>
.area-selector {
  position: absolute;
  top: 12px;
  left: 12px;
  z-index: 100;
  display: flex;
  flex-direction: column;
  gap: 8px;
  pointer-events: none;
}
.area-selector > * { pointer-events: auto; }
.as-toolbar {
  display: flex;
  gap: 6px;
}
.as-hint {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 8px;
  font-size: 13px;
  color: #fff;
}
.as-hint-box { background: rgba(0,212,255,.2); border: 1px solid rgba(0,212,255,.4); }
.as-hint-multi { background: rgba(82,196,26,.2); border: 1px solid rgba(82,196,26,.4); }
.as-result {
  background: var(--bg-panel);
  border: 1px solid rgba(255,255,255,.08);
  border-radius: 8px;
  padding: 10px;
  min-width: 200px;
}
.as-result-header {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
}
.as-result-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 0;
  font-size: 12px;
  color: var(--text-primary);
  border-bottom: 1px solid rgba(255,255,255,.04);
}
.as-result-actions {
  display: flex;
  gap: 6px;
  margin-top: 8px;
  justify-content: flex-end;
}
</style>
