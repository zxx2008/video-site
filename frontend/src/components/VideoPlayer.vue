<template>
  <div>
    <video ref="videoEl" class="video-js vjs-big-play-centered vjs-fluid" playsinline></video>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import videojs from 'video.js'
import 'video.js/dist/video-js.css'

const props = defineProps({
  src: { type: String, required: true },
  type: { type: String, default: 'video/mp4' },
  videoId: { type: [Number, String], required: true },
  displayAspectRatio: { type: String, default: '' },
})

const videoEl = ref(null)
let player = null
let loopEnabled = ref(false)

// Progress memory
const STORAGE_KEY = 'videohub_progress'
const LOOP_STATE_KEY = 'videohub_loop_enabled'

function loadProgress(id) {
  try {
    const data = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}')
    return data[id] || 0
  } catch {
    return 0
  }
}

function saveProgress(id, time) {
  try {
    const data = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}')
    data[id] = time
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
  } catch {
    // ignore
  }
}

function clearProgress(id) {
  try {
    const data = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}')
    delete data[id]
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
  } catch {
    // ignore
  }
}

// Loop state management
function loadLoopState() {
  try {
    return localStorage.getItem(LOOP_STATE_KEY) === 'true'
  } catch {
    return false
  }
}

function saveLoopState(enabled) {
  try {
    localStorage.setItem(LOOP_STATE_KEY, enabled ? 'true' : 'false')
  } catch {
    // ignore
  }
}

function normalizeAspectRatio(raw) {
  if (!raw || typeof raw !== 'string') return ''
  const parts = raw.split(':')
  if (parts.length !== 2) return ''

  const width = Number(parts[0])
  const height = Number(parts[1])
  if (!Number.isFinite(width) || !Number.isFinite(height) || width <= 0 || height <= 0) {
    return ''
  }

  return `${width}:${height}`
}

function applyIntrinsicAspectRatio() {
  if (!player) return false
  const width = Number(player.videoWidth?.())
  const height = Number(player.videoHeight?.())

  if (!Number.isFinite(width) || !Number.isFinite(height) || width <= 0 || height <= 0) {
    return false
  }

  player.aspectRatio(`${width}:${height}`)
  return true
}

function initPlayer() {
  if (!videoEl.value) return

  // Load saved loop state
  loopEnabled.value = loadLoopState()

  // Register custom loop button
  const Button = videojs.getComponent('Button')
  const loopButtonRef = { value: null }

  class LoopButton extends Button {
    constructor(player, options) {
      super(player, options)
      this.updateIcon()
      loopButtonRef.value = this
    }
    
    handleClick() {
      loopEnabled.value = !loopEnabled.value
      saveLoopState(loopEnabled.value)
      this.updateIcon()
    }
    
    updateIcon() {
      if (loopEnabled.value) {
        this.addClass('vjs-loop-active')
        this.controlText('关闭循环播放')
      } else {
        this.removeClass('vjs-loop-active')
        this.controlText('开启循环播放')
      }
    }
    
    buildCSSClass() {
      return 'vjs-loop-button vjs-control vjs-button ' + super.buildCSSClass()
    }
  }
  videojs.registerComponent('LoopButton', LoopButton)

  const aspectRatio = normalizeAspectRatio(props.displayAspectRatio)
  const playerOptions = {
    controls: true,
    preload: 'auto',
    responsive: true,
    fluid: true,
    playbackRates: [0.5, 1, 1.5, 2],
    sources: [{ src: props.src, type: props.type }],
    controlBar: {
      children: [
        'playToggle',
        'volumePanel',
        'currentTimeDisplay',
        'timeDivider',
        'durationDisplay',
        'progressControl',
        'playbackRateMenuButton',
        'LoopButton',
        'fullscreenToggle',
      ],
    },
  }

  if (aspectRatio) {
    playerOptions.aspectRatio = aspectRatio
  }

  player = videojs(videoEl.value, playerOptions)

  // Restore progress
  player.on('loadedmetadata', () => {
    applyIntrinsicAspectRatio()

    const saved = loadProgress(props.videoId)
    if (saved > 0) {
      player.currentTime(saved)
    }
  })

  // Throttled save every 5 seconds
  let lastSave = 0
  player.on('timeupdate', () => {
    const now = Date.now()
    if (now - lastSave >= 5000) {
      lastSave = now
      const time = player.currentTime()
      if (time > 0) saveProgress(props.videoId, time)
    }
  })

  // Loop or clear on ended
  player.on('ended', () => {
    if (loopEnabled.value) {
      player.currentTime(0)
      player.play().catch(() => {
        // Ignore autoplay errors
      })
    } else {
      clearProgress(props.videoId)
    }
  })
}

onMounted(() => {
  initPlayer()
})

onBeforeUnmount(() => {
  if (player) {
    const time = player.currentTime()
    if (time > 0) saveProgress(props.videoId, time)
    player.dispose()
    player = null
  }
})

watch(() => [props.src, props.type], ([newSrc, newType]) => {
  if (player) {
    const fallbackAspectRatio = normalizeAspectRatio(props.displayAspectRatio)
    if (fallbackAspectRatio) {
      player.aspectRatio(fallbackAspectRatio)
    }
    player.src({ src: newSrc, type: newType })
  }
})

watch(() => props.displayAspectRatio, (newRatio) => {
  if (!player) return
  const aspectRatio = normalizeAspectRatio(newRatio)
  if (aspectRatio) {
    player.aspectRatio(aspectRatio)
  }
})
</script>

<style scoped>
/* 循环按钮基础样式 - 白色、更大、更明显 */
:deep(.vjs-loop-button) {
  color: #ffffff !important;
  cursor: pointer;
  opacity: 1;
  width: 3em !important;
  height: 3em !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  transition: all 0.2s ease;
  position: relative;
}

:deep(.vjs-loop-button:hover) {
  transform: scale(1.15);
  filter: drop-shadow(0 0 6px rgba(255, 255, 255, 0.8));
}

/* 按钮图标 */
:deep(.vjs-loop-button .vjs-icon-placeholder) {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
}

:deep(.vjs-loop-button .vjs-icon-placeholder::before) {
  content: '';
  display: block;
  width: 100%;
  height: 100%;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23ffffff' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M17 2l4 4-4 4'/%3E%3Cpath d='M3 11v-1a4 4 0 0 1 4-4h14'/%3E%3Cpath d='M7 22l-4-4 4-4'/%3E%3Cpath d='M21 13v1a4 4 0 0 1-4 4H3'/%3E%3C/svg%3E");
  background-size: contain;
  background-repeat: no-repeat;
  background-position: center;
  transition: all 0.2s ease;
}

/* 开启状态 - 高亮蓝色 */
:deep(.vjs-loop-active) {
  color: #4dabf7 !important;
}

:deep(.vjs-loop-active:hover) {
  filter: drop-shadow(0 0 10px rgba(77, 171, 247, 0.9)) !important;
}

:deep(.vjs-loop-active .vjs-icon-placeholder::before) {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%234dabf7' stroke-width='3' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M17 2l4 4-4 4'/%3E%3Cpath d='M3 11v-1a4 4 0 0 1 4-4h14'/%3E%3Cpath d='M7 22l-4-4 4-4'/%3E%3Cpath d='M21 13v1a4 4 0 0 1-4 4H3'/%3E%3C/svg%3E");
  filter: drop-shadow(0 0 4px rgba(77, 171, 247, 0.8));
}
</style>