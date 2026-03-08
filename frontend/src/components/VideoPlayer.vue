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

// Progress memory
const STORAGE_KEY = 'videohub_progress'

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

function initPlayer() {
  if (!videoEl.value) return

  const aspectRatio = normalizeAspectRatio(props.displayAspectRatio)
  const playerOptions = {
    controls: true,
    preload: 'auto',
    responsive: true,
    fluid: true,
    playbackRates: [0.5, 1, 1.5, 2],
    sources: [{ src: props.src, type: props.type }],
  }

  if (aspectRatio) {
    playerOptions.aspectRatio = aspectRatio
  }

  player = videojs(videoEl.value, playerOptions)

  // Restore progress
  player.on('loadedmetadata', () => {
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

  // Clear on ended
  player.on('ended', () => {
    clearProgress(props.videoId)
  })
}

onMounted(() => {
  initPlayer()
})

onBeforeUnmount(() => {
  // Save current position before destroy
  if (player) {
    const time = player.currentTime()
    if (time > 0) saveProgress(props.videoId, time)
    player.dispose()
    player = null
  }
})

// Watch src changes
watch(() => [props.src, props.type], ([newSrc, newType]) => {
  if (player) {
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
