<template>
  <div class="max-w-xl mx-auto px-4 sm:px-6 py-6">
    <h1 class="text-xl font-bold text-gray-900">上传视频</h1>

    <!-- File select area -->
    <div
      class="mt-6 border-2 border-dashed rounded-lg p-6 sm:p-8 text-center transition-colors cursor-pointer"
      :class="dragOver ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'"
      @click="triggerFileInput"
      @dragover.prevent="dragOver = true"
      @dragleave="dragOver = false"
      @drop.prevent="onDrop"
    >
      <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
          d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
      </svg>
      <p class="mt-3 text-sm text-gray-600">
        <span class="text-blue-600 font-medium">点击选择文件</span> 或拖拽到此处
      </p>
      <p class="mt-1 text-xs text-gray-500">支持 MP4, MKV, AVI, MOV, WMV, FLV, WebM</p>
      <input
        ref="fileInput"
        type="file"
        accept="video/*"
        class="hidden"
        @change="onFileChange"
      />
    </div>

    <!-- Selected file info -->
    <div v-if="file" class="mt-4 p-3 bg-gray-50 rounded-lg">
      <div class="flex items-center justify-between">
        <div class="min-w-0">
          <p class="text-sm font-medium text-gray-900 truncate">{{ file.name }}</p>
          <p class="text-xs text-gray-500">{{ formatSize(file.size) }}{{ file.size >= SIZE_THRESHOLD ? ' (分片上传)' : '' }}</p>
        </div>
        <button v-if="!uploading" @click="clearFile" class="ml-2 p-1.5 min-w-[44px] min-h-[44px] flex items-center justify-center text-gray-400 hover:text-gray-600">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>

    <!-- Title input -->
    <div v-if="file" class="mt-4">
      <label class="block text-sm font-medium text-gray-700 mb-1">视频标题</label>
      <input
        v-model="title"
        type="text"
        class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        placeholder="输入视频标题"
        :disabled="uploading"
      />
    </div>

    <!-- Progress bar -->
    <div v-if="uploading" class="mt-4">
      <div class="flex items-center justify-between text-sm text-gray-600 mb-1">
        <span>上传中...</span>
        <span>{{ progress }}%</span>
      </div>
      <div class="w-full bg-gray-200 rounded-full h-2.5">
        <div class="bg-blue-600 h-2.5 rounded-full transition-all duration-300" :style="{ width: progress + '%' }"></div>
      </div>
    </div>

    <!-- Error message -->
    <div v-if="errorMsg" class="mt-4 p-3 bg-red-50 text-red-700 rounded-lg text-sm">
      {{ errorMsg }}
    </div>

    <!-- Upload button -->
    <button
      v-if="file"
      :disabled="uploading"
      class="mt-6 w-full py-2.5 min-h-[44px] bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      @click="startUpload"
    >
      {{ uploading ? '上传中...' : '开始上传' }}
    </button>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { smartUpload, SIZE_THRESHOLD } from '../utils/chunkedUpload'

const router = useRouter()

const fileInput = ref(null)
const file = ref(null)
const title = ref('')
const uploading = ref(false)
const progress = ref(0)
const errorMsg = ref('')
const dragOver = ref(false)

function triggerFileInput() {
  fileInput.value?.click()
}

function onFileChange(e) {
  selectFile(e.target.files[0])
}

function onDrop(e) {
  dragOver.value = false
  const f = e.dataTransfer?.files[0]
  if (f) selectFile(f)
}

function selectFile(f) {
  if (!f) return
  file.value = f
  title.value = f.name.replace(/\.[^.]+$/, '')
  errorMsg.value = ''
  progress.value = 0
}

function clearFile() {
  file.value = null
  title.value = ''
  errorMsg.value = ''
  progress.value = 0
  if (fileInput.value) fileInput.value.value = ''
}

async function startUpload() {
  if (!file.value || uploading.value) return
  uploading.value = true
  errorMsg.value = ''
  progress.value = 0

  try {
    const result = await smartUpload(file.value, title.value, (p) => {
      progress.value = p
    })
    router.push(`/video/${result.id}`)
  } catch (e) {
    const detail = e.response?.data?.detail
    errorMsg.value = detail || '上传失败，请重试'
  } finally {
    uploading.value = false
  }
}

function formatSize(bytes) {
  if (!bytes) return '0 B'
  if (bytes >= 1073741824) return (bytes / 1073741824).toFixed(1) + ' GB'
  if (bytes >= 1048576) return (bytes / 1048576).toFixed(1) + ' MB'
  return (bytes / 1024).toFixed(1) + ' KB'
}
</script>
