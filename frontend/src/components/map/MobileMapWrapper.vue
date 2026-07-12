<template>
  <div class="mobile-map-wrapper" :class="{ 'is-mobile': isMobile }">
    <div ref="mapContainer" class="mmw-map" :style="mapStyle"></div>

    <!-- 触摸操作提示 -->
    <div class="mmw-touch-hint" v-if="showTouchHint">
      <div class="mmw-hint-content">
        <div class="mmw-hint-icon">👆</div>
        <div class="mmw-hint-text">
          <div>单指拖动地图</div>
          <div>双指缩放</div>
          <div>长按选点</div>
        </div>
        <el-button size="small" text @click="dismissHint">知道了</el-button>
      </div>
    </div>

    <!-- 移动端底部信息栏 -->
    <Transition name="mmw-slide">
      <div v-if="showBottomPanel && isMobile" class="mmw-bottom-panel">
        <div class="mmw-bottom-handle" @click="toggleBottomPanel"></div>
        <div class="mmw-bottom-content">
          <slot name="bottom-panel">
            <div style="text-align:center;color:var(--text-secondary);padding:20px">
              点击路段查看详情
            </div>
          </slot>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  mapInstance: { type: Object, default: null },
  height: { type: String, default: undefined },
  touchHint: { type: Boolean, default: true },
})

const mapContainer = ref(null)
const isMobile = ref(false)
const showTouchHint = ref(props.touchHint)
const showBottomPanel = ref(false)
const windowWidth = ref(window.innerWidth)

const mapStyle = computed(() => {
  if (props.height) return { height: props.height }
  return {
    height: isMobile.value ? '55vh' : '80vh',
  }
})

const checkMobile = () => {
  isMobile.value = window.innerWidth < 768
  windowWidth.value = window.innerWidth
}

const dismissHint = () => {
  showTouchHint.value = false
  try { localStorage.setItem('mmw-hint-dismissed', 'true') } catch {}
}

const toggleBottomPanel = () => {
  showBottomPanel.value = !showBottomPanel.value
}

// 初始化触摸事件
const initTouchEvents = () => {
  const el = mapContainer.value
  if (!el || !window.AMap) return
  // 长按选点
  let longPressTimers = null
  el.addEventListener('touchstart', (e) => {
    if (e.touches.length === 1) {
      longPressTimers = setTimeout(() => {
        // 触发的长按选点
        if (props.mapInstance) {
          const touch = e.touches[0]
          const pixel = new AMap.Pixel(touch.clientX, touch.clientY)
          const lnglat = props.mapInstance.containerToLngLat(pixel)
          if (lnglat) {
            props.mapInstance.emit('longpress', { lnglat })
          }
        }
      }, 600)
    }
  })
  el.addEventListener('touchend', () => clearTimeout(longPressTimers))
  el.addEventListener('touchmove', () => clearTimeout(longPressTimers))
}

const onResize = () => {
  checkMobile()
  props.mapInstance?.resize()
}

onMounted(() => {
  checkMobile()
  window.addEventListener('resize', onResize)
  const dismissed = localStorage.getItem('mmw-hint-dismissed')
  if (dismissed) showTouchHint.value = false

  // 等地图就绪后绑定触摸事件
  if (props.mapInstance) {
    initTouchEvents()
  } else {
    // 等待地图加载
    const checkMap = setInterval(() => {
      if (props.mapInstance || window.AMap) {
        clearInterval(checkMap)
        initTouchEvents()
      }
    }, 500)
    setTimeout(() => clearInterval(checkMap), 10000)
  }
})

onUnmounted(() => {
  window.removeEventListener('resize', onResize)
})

defineExpose({ showBottomPanel, toggleBottomPanel })
</script>

<style scoped>
.mobile-map-wrapper {
  position: relative;
  width: 100%;
  overflow: hidden;
}
.mmw-map {
  width: 100%;
  border-radius: 12px;
  overflow: hidden;
}
.mmw-touch-hint {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
  backdrop-filter: blur(4px);
}
.mmw-hint-content {
  background: var(--bg-panel);
  border: 1px solid rgba(255,255,255,.1);
  border-radius: 16px;
  padding: 24px 32px;
  text-align: center;
}
.mmw-hint-icon { font-size: 40px; margin-bottom: 12px; }
.mmw-hint-text {
  font-size: 14px;
  color: var(--text-primary);
  line-height: 1.8;
  margin-bottom: 16px;
}
.mmw-bottom-panel {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: var(--bg-panel);
  border-radius: 16px 16px 0 0;
  border-top: 1px solid rgba(255,255,255,.08);
  z-index: 150;
  max-height: 40vh;
  overflow-y: auto;
}
.mmw-bottom-handle {
  width: 36px;
  height: 4px;
  border-radius: 2px;
  background: rgba(255,255,255,.2);
  margin: 8px auto;
  cursor: pointer;
}
.mmw-bottom-content {
  padding: 0 16px 16px;
}

/* 底部面板过渡 */
.mmw-slide-enter-active, .mmw-slide-leave-active {
  transition: transform .3s ease;
}
.mmw-slide-enter-from, .mmw-slide-leave-to {
  transform: translateY(100%);
}
</style>
