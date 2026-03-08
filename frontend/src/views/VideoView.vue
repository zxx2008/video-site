<template>
  <div class="max-w-[960px] mx-auto px-4 sm:px-6 py-6">
    <!-- Loading -->
    <div v-if="loading" class="flex justify-center py-20">
      <svg class="animate-spin h-8 w-8 text-blue-600" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none" />
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
      </svg>
    </div>

    <!-- 404 -->
    <div v-else-if="notFound" class="text-center py-20">
      <p class="text-6xl font-bold text-gray-200">404</p>
      <p class="mt-4 text-gray-500">视频不存在</p>
      <router-link to="/" class="mt-4 inline-block text-blue-600 hover:underline">返回首页</router-link>
    </div>

    <!-- Video content -->
    <template v-else-if="video">
      <!-- Player -->
      <VideoPlayer
        :src="streamUrl"
        :type="streamType"
        :video-id="video.id"
        :display-aspect-ratio="displayAspectRatio"
      />

      <!-- Video info -->
      <div class="mt-6">
        <h1 class="text-xl sm:text-2xl font-bold text-gray-900">{{ video.title }}</h1>
        <div class="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-sm text-gray-500">
          <span v-if="video.duration">{{ formatDuration(video.duration) }}</span>
          <span v-if="video.resolution">{{ video.resolution }}</span>
          <span v-if="displayAspectRatio">显示比例 {{ displayAspectRatio }}</span>
          <span v-if="video.codec">{{ video.codec.toUpperCase() }}</span>
          <span>{{ formatSize(video.file_size) }}</span>
          <span>{{ formatDate(video.created_at) }}</span>
        </div>
      </div>

      <!-- Action buttons -->
      <div class="mt-6 flex flex-wrap gap-3">
        <a
          :href="downloadUrl"
          class="inline-flex items-center px-4 py-2 min-h-[44px] bg-gray-100 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-200 transition-colors"
        >
          <svg class="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          下载
        </a>
        <button
          @click="confirmDelete"
          class="inline-flex items-center px-4 py-2 min-h-[44px] bg-red-50 text-red-600 text-sm font-medium rounded-lg hover:bg-red-100 transition-colors"
        >
          <svg class="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
          删除
        </button>
      </div>

      <!-- Delete confirm dialog -->
      <div v-if="showDeleteConfirm" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50" @click.self="showDeleteConfirm = false">
        <div class="bg-white rounded-lg p-6 mx-4 max-w-sm w-full shadow-xl">
          <h3 class="text-lg font-medium text-gray-900">确认删除</h3>
          <p class="mt-2 text-sm text-gray-500">确定要删除「{{ video.title }}」吗？此操作不可撤销。</p>
          <div class="mt-4 flex justify-end space-x-3">
            <button @click="showDeleteConfirm = false" class="px-4 py-2.5 min-h-[44px] text-sm text-gray-700 hover:bg-gray-100 rounded-lg transition-colors">
              取消
            </button>
            <button @click="doDelete" :disabled="deleting" class="px-4 py-2.5 min-h-[44px] text-sm text-white bg-red-600 hover:bg-red-700 rounded-lg transition-colors disabled:opacity-50">
              {{ deleting ? '删除中...' : '确认删除' }}
            </button>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import videosApi from '../api/videos'
import VideoPlayer from '../components/VideoPlayer.vue'

const route = useRoute()
const router = useRouter()

const video = ref(null)
const loading = ref(true)
const notFound = ref(false)
const showDeleteConfirm = ref(false)
const deleting = ref(false)

function hasNonSquarePixels(sampleAspectRatio) {
  if (!sampleAspectRatio || sampleAspectRatio === '1:1' || sampleAspectRatio === 'N/A' || sampleAspectRatio === '0:1') {
    return false
  }
  const parts = sampleAspectRatio.split(':')
  if (parts.length !== 2) return false
  const num = Number(parts[0])
  const den = Number(parts[1])
  if (!Number.isFinite(num) || !Number.isFinite(den) || num <= 0 || den <= 0) return false
  return num !== den
}

function shouldUseMp4Stream(item) {
  if (!item) return false
  if (item.playback_path) return true

  const rotation = ((Number(item.rotation) || 0) % 360 + 360) % 360
  if (rotation === 90 || rotation === 180 || rotation === 270) {
    return true
  }

  if (hasNonSquarePixels(item.sample_aspect_ratio)) {
    return true
  }

  const codec = (item.codec || '').toLowerCase()
  if (codec && codec !== 'h264') {
    return true
  }

  return false
}

const videoId = computed(() => Number(route.params.id))
const streamUrl = computed(() => videosApi.getStreamUrl(videoId.value))
const streamType = computed(() => {
  if (!video.value) return 'video/mp4'
  return shouldUseMp4Stream(video.value) ? 'video/mp4' : video.value.mime_type
})
const displayAspectRatio = computed(() => {
  if (!video.value) return ''
  return video.value.final_display_aspect_ratio || video.value.display_aspect_ratio || ''
})
const downloadUrl = computed(() => videosApi.getDownloadUrl(videoId.value))

async function fetchVideo() {
  loading.value = true
  try {
    const res = await videosApi.getVideo(videoId.value)
    video.value = res.data
  } catch (e) {
    if (e.response?.status === 404) {
      notFound.value = true
    }
  } finally {
    loading.value = false
  }
}

function confirmDelete() {
  showDeleteConfirm.value = true
}

async function doDelete() {
  deleting.value = true
  try {
    await videosApi.deleteVideo(videoId.value)
    router.push('/')
  } catch {
    alert('删除失败，请重试')
  } finally {
    deleting.value = false
    showDeleteConfirm.value = false
  }
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
  const h = String(d.getHours()).padStart(2, '0')
  const min = String(d.getMinutes()).padStart(2, '0')
  return `${y}-${m}-${day} ${h}:${min}`
}

onMounted(fetchVideo)
</script>
