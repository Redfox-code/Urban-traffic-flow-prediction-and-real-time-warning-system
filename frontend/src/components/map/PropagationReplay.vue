<template>
  <div class="propagation-replay">
    <!-- 播放控件 -->
    <div class="pr-controls">
      <el-button size="small" circle @click="togglePlay" :title="isPlaying ? '暂停' : '播放'">
        {{ isPlaying ? '⏸' : '▶' }}
      </el-button>
      <el-button size="small" circle @click="stepBack" title="后退一帧">⏮</el-button>
      <el-button size="small" circle @click="stepForward" title="前进一帧">⏭</el-button>
      <el-button size="small" circle @click="speedUp" title="快进">{{ speedLabel }}</el-button>

      <!-- 进度条 -->
      <div class="pr-slider" ref="sliderRef" @mousedown="onSliderDown">
        <div class="pr-slider-track">
          <div class="pr-slider-fill" :style="{ width: progressPct + '%' }"></div>
          <div class="pr-slider-thumb" :style="{ left: progressPct + '%' }"></div>
        </div>
      </div>

      <span class="pr-time">{{ currentFrame }}/{{ totalFrames }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  frames: { type: Array, default: () => [] },
  // frames: [{timestamp, ripples:[...], arrows:[...], sections:{...}}]
  speed: { type: Number, default: 1 },
})

const emit = defineEmits(['frame-change', 'play-end'])

const isPlaying = ref(false)
const currentFrame = ref(0)
const speedMultiplier = ref(1)
const sliderRef = ref(null)

let playTimer = null

const totalFrames = computed(() => props.frames.length)
const progressPct = computed(() => {
  if (totalFrames.value <= 1) return 0
  return (currentFrame.value / (totalFrames.value - 1)) * 100
})

const speedLabel = computed(() => {
  return speedMultiplier.value === 1 ? '1×' : speedMultiplier.value + '×'
})

const togglePlay = () => {
  if (totalFrames.value === 0) return
  isPlaying.value = !isPlaying.value
  if (isPlaying.value) startPlay()
  else stopPlay()
}

const startPlay = () => {
  stopPlay()
  playTimer = setInterval(() => {
    if (currentFrame.value >= totalFrames.value - 1) {
      stopPlay()
      isPlaying.value = false
      emit('play-end')
      return
    }
    currentFrame.value++
    emit('frame-change', currentFrame.value)
  }, 1000 / speedMultiplier.value)
}

const stopPlay = () => {
  clearInterval(playTimer)
  playTimer = null
}

const stepForward = () => {
  if (currentFrame.value < totalFrames.value - 1) {
    currentFrame.value++
    emit('frame-change', currentFrame.value)
  }
}

const stepBack = () => {
  if (currentFrame.value > 0) {
    currentFrame.value--
    emit('frame-change', currentFrame.value)
  }
}

const speedUp = () => {
  const speeds = [1, 2, 4, 8]
  const idx = speeds.indexOf(speedMultiplier.value)
  speedMultiplier.value = speeds[(idx + 1) % speeds.length]
  if (isPlaying.value) {
    startPlay()
  }
}

const onSliderDown = (e) => {
  const rect = sliderRef.value.getBoundingClientRect()
  const pct = (e.clientX - rect.left) / rect.width
  const frame = Math.round(pct * (totalFrames.value - 1))
  currentFrame.value = Math.max(0, Math.min(frame, totalFrames.value - 1))
  emit('frame-change', currentFrame.value)

  const onMove = (ev) => {
    const p = (ev.clientX - rect.left) / rect.width
    const f = Math.round(p * (totalFrames.value - 1))
    currentFrame.value = Math.max(0, Math.min(f, totalFrames.value - 1))
    emit('frame-change', currentFrame.value)
  }
  const onUp = () => {
    document.removeEventListener('mousemove', onMove)
    document.removeEventListener('mouseup', onUp)
  }
  document.addEventListener('mousemove', onMove)
  document.addEventListener('mouseup', onUp)
}

watch(() => props.frames, (val) => {
  currentFrame.value = 0
  isPlaying.value = false
  stopPlay()
})

onUnmounted(stopPlay)

defineExpose({ togglePlay, currentFrame, goToFrame: (n) => { currentFrame.value = n; emit('frame-change', n) } })
</script>

<style scoped>
.propagation-replay {
  background: var(--bg-panel);
  border: 1px solid rgba(255,255,255,.08);
  border-radius: 12px;
  padding: 12px 16px;
}
.pr-controls {
  display: flex;
  align-items: center;
  gap: 8px;
}
.pr-slider {
  flex: 1;
  height: 24px;
  display: flex;
  align-items: center;
  cursor: pointer;
  position: relative;
}
.pr-slider-track {
  width: 100%;
  height: 6px;
  background: rgba(255,255,255,.1);
  border-radius: 3px;
  position: relative;
}
.pr-slider-fill {
  height: 100%;
  background: var(--accent-blue);
  border-radius: 3px;
  transition: width .1s;
}
.pr-slider-thumb {
  position: absolute;
  top: 50%;
  transform: translate(-50%, -50%);
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: var(--accent-blue);
  box-shadow: 0 0 0 3px rgba(0,212,255,.2);
  transition: left .1s;
}
.pr-time {
  font-size: 12px;
  color: var(--text-secondary);
  min-width: 60px;
  text-align: right;
}
</style>
