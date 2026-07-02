<template>
  <Teleport to="body">
    <Transition name="alert-slide">
      <div v-if="visible" class="alert-popup" :class="levelClass">
        <span class="alert-icon">{{ levelIcon }}</span>
        <span>{{ alert.message }}</span>
        <button @click="dismiss">×</button>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useWarningStore } from '@/store/warning'

const props = defineProps({ alert: { type: Object, default: () => ({}) } })
const visible = ref(false)
const warningStore = useWarningStore()

// TODO D8: 监听 store.activeWarnings变化 → 弹窗
const levelClass = computed(() => props.alert.level === 'CRITICAL' ? 'alert-critical' : 'alert-warning')
const levelIcon = computed(() => props.alert.level === 'CRITICAL' ? '🔴' : '🟡')
const dismiss = () => visible.value = false
</script>

<style scoped>
.alert-popup {
  position: fixed; top: 20px; right: 20px; z-index: 9999;
  padding: 16px 20px; border-radius: 8px; color: #fff; max-width: 400px;
}
.alert-warning { background: #ff9800; }
.alert-critical { background: #f44336; animation: pulse 0.5s infinite alternate; }
@keyframes pulse { from { opacity: 1; } to { opacity: 0.8; } }
</style>
