<template>
  <span class="traffic-badge" :style="{background:level.color}">{{ level.label }}</span>
</template>

<script setup>
import { computed } from 'vue'
const props = defineProps({ occupancy: { type: Number, default: 0 } })
const level = computed(() => {
  if (props.occupancy < 30) return { label:'畅通', color:'#00e676' }
  if (props.occupancy < 60) return { label:'缓行', color:'#ffeb3b' }
  if (props.occupancy < 85) return { label:'拥堵', color:'#ff9800' }
  return { label:'严重拥堵', color:'#f44336' }
})
</script>

<style scoped>
.traffic-badge { padding:2px 10px; border-radius:10px; font-size:12px; color:#000; font-weight:bold; }
</style>
