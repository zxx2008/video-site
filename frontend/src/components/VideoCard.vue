<template>
  <router-link :to="`/video/${video.id}`" class="group block bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden hover:shadow-md transition-shadow">
    <!-- Thumbnail -->
    <div class="relative aspect-video bg-gray-100">
      <img
        :src="thumbnailUrl"
        :alt="video.title"
        class="w-full h-full object-cover"
        loading="lazy"
        @error="onImgError"
      />
      <!-- Duration badge -->
      <span v-if="video.duration" class="absolute bottom-1.5 right-1.5 px-1.5 py-0.5 bg-black/75 text-white text-xs rounded">
        {{ formatDuration(video.duration) }}
      </span>
    </div>
    <!-- Info -->
    <div class="p-3">
      <h3 class="text-sm font-medium text-gray-900 line-clamp-2 group-hover:text-blue-600 transition-colors">
        {{ video.title }}
      </h3>
      <div class="mt-1.5 flex items-center text-xs text-gray-500 space-x-2">
        <span>{{ formatSize(video.file_size) }}</span>
        <span>&middot;</span>
        <span>{{ formatDate(video.created_at) }}</span>
      </div>
    </div>
  </router-link>
</template>

<script setup>
import { computed } from 'vue'
import videosApi from '../api/videos'

const props = defineProps({
  video: { type: Object, required: true },
})

const thumbnailUrl = computed(() => videosApi.getThumbnailUrl(props.video.id))

function onImgError(e) {
  e.target.style.display = 'none'
}

function formatDuration(seconds) {
  const s = Math.round(seconds)
  const h = Math.floor(s / 3600)
  const m = Math.floor((s % 3600) / 60)
  const sec = s % 60
  if (h > 0) return `${h}:${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')}`
  return `${m}:${String(sec).padStart(2, '0')}`
}

function formatSize(bytes) {
  if (!bytes) return '0 B'
  if (bytes >= 1073741824) return (bytes / 1073741824).toFixed(1) + ' GB'
  if (bytes >= 1048576) return (bytes / 1048576).toFixed(1) + ' MB'
  return (bytes / 1024).toFixed(1) + ' KB'
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}
</script>
