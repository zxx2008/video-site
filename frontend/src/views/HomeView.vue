<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
    <!-- Loading -->
    <div v-if="loading" class="flex justify-center py-20">
      <svg class="animate-spin h-8 w-8 text-blue-600" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none" />
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
      </svg>
    </div>

    <!-- Empty state -->
    <div v-else-if="videos.length === 0" class="text-center py-20">
      <svg class="mx-auto h-16 w-16 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
          d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
      </svg>
      <p class="mt-4 text-gray-500 text-lg">暂无视频</p>
      <router-link to="/upload" class="mt-4 inline-flex items-center px-5 py-2.5 min-h-[44px] bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors">
        去上传一个吧
      </router-link>
    </div>

    <!-- Video grid -->
    <template v-else>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 sm:gap-6">
        <VideoCard v-for="video in videos" :key="video.id" :video="video" />
      </div>
      <div class="mt-8">
        <Pagination :current-page="page" :total="total" :page-size="pageSize" @change="goToPage" />
      </div>
    </template>

    <!-- Error -->
    <div v-if="error" class="mt-4 p-4 bg-red-50 text-red-700 rounded-lg text-sm">
      {{ error }}
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import videosApi from '../api/videos'
import VideoCard from '../components/VideoCard.vue'
import Pagination from '../components/Pagination.vue'

const route = useRoute()
const router = useRouter()

const videos = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const loading = ref(false)
const error = ref('')

function initPageFromQuery() {
  const pageFromQuery = parseInt(route.query.page)
  if (pageFromQuery && pageFromQuery > 0) {
    page.value = pageFromQuery
  }
}

async function fetchVideos() {
  loading.value = true
  error.value = ''
  try {
    const res = await videosApi.getVideos(page.value, pageSize)
    videos.value = res.data.items
    total.value = res.data.total
  } catch (e) {
    error.value = '加载视频列表失败'
  } finally {
    loading.value = false
  }
}

function goToPage(p) {
  page.value = p
  router.replace({ query: { ...route.query, page: p } })
  fetchVideos()
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

onMounted(() => {
  initPageFromQuery()
  fetchVideos()
})
</script>
