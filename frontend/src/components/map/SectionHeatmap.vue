<template>
  <div ref="heatmapContainer" style="display:none"></div>
</template>
<script setup>
import { ref, watch, onMounted } from 'vue'
const props = defineProps({ map: Object, trafficData: { type: Array, default: () => [] } })
// D11: 基于occupancy渲染热力图覆盖层
// heatmap.setDataSet({ data: heatmapData, max: 100 })
</script>
