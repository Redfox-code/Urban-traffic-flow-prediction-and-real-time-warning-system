<template>
  <div class="propagation-arrows" style="display:none"></div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  map: { type: Object, required: true },
  arrows: { type: Array, default: () => [] },
  // arrows: [{from:{lng,lat}, to:{lng,lat}, probability:0.7, hop:1, level:'congested'}]
  visible: { type: Boolean, default: true },
})

let arrowPolylines = []
let arrowLabelMarkers = []

const clearArrows = () => {
  arrowPolylines.forEach(p => props.map?.remove(p))
  arrowLabelMarkers.forEach(m => props.map?.remove(m))
  arrowPolylines = []
  arrowLabelMarkers = []
}

const drawArrows = () => {
  if (!props.map || !props.visible) return
  clearArrows()

  props.arrows.forEach((arrow, idx) => {
    if (!arrow.from || !arrow.to) return

    // 根据跳数选择线型
    const dashStyle = arrow.hop === 1 ? []        // 第1跳: 实线
                    : arrow.hop === 2 ? [8, 6]     // 第2跳: 虚线
                    : [4, 6, 4, 6]                 // 第3跳+: 点线

    // 颜色深浅 = 传播概率
    const baseColor = arrow.level === 'jammed' ? '#f5222d'
                    : arrow.level === 'congested' ? '#fa8c16'
                    : '#fadb14'
    const alpha = Math.min(1, (arrow.probability || 0.5) + 0.3)

    const polyline = new AMap.Polyline({
      path: [arrow.from, arrow.to],
      strokeColor: baseColor,
      strokeWeight: 4,
      strokeOpacity: alpha,
      lineJoin: 'round',
      strokeStyle: dashStyle.length > 0 ? 'dashed' : 'solid',
      dashArray: dashStyle,
      zIndex: 30 + (arrow.hop || 1),
      showDir: true,
      extData: { hop: arrow.hop, probability: arrow.probability },
    })
    props.map.add(polyline)
    arrowPolylines.push(polyline)

    // 概率标签（中点位置）
    const midLng = (arrow.from.lng + arrow.to.lng) / 2
    const midLat = (arrow.from.lat + arrow.to.lat) / 2
    const label = Math.round((arrow.probability || 0) * 100) + '%'
    if (window.AMap?.Marker) {
      const marker = new AMap.Marker({
        position: [midLng, midLat],
        content: `<div class="pa-label" style="background:${baseColor};">${label}</div>`,
        offset: new AMap.Pixel(-14, -8),
        zIndex: 35,
      })
      props.map.add(marker)
      arrowLabelMarkers.push(marker)
    }
  })
}

watch(() => props.arrows, () => { drawArrows() }, { deep: true })
watch(() => props.visible, (val) => { if (!val) clearArrows(); else drawArrows() })

onMounted(() => { if (props.arrows.length > 0) drawArrows() })
onUnmounted(clearArrows)

defineExpose({ drawArrows, clearArrows })
</script>

<style>
.pa-label {
  color: #fff; font-size: 10px; font-weight: bold;
  padding: 2px 6px; border-radius: 4px;
  white-space: nowrap;
  box-shadow: 0 1px 4px rgba(0,0,0,.4);
}
</style>
