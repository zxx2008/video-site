import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

export default {
  // 视频列表
  getVideos(page = 1, pageSize = 20) {
    return api.get('/videos', { params: { page, pageSize } })
  },

  // 视频详情
  getVideo(id) {
    return api.get(`/videos/${id}`)
  },

  // 上传视频（带进度回调）
  uploadVideo(file, title, onProgress) {
    const form = new FormData()
    form.append('file', file)
    if (title) form.append('title', title)
    return api.post('/videos/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (e) => {
        onProgress?.(Math.round((e.loaded / e.total) * 100))
      },
    })
  },

  // 分片上传
  uploadChunk(formData, onProgress) {
    return api.post('/videos/upload/chunk', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (e) => {
        onProgress?.(e)
      },
    })
  },

  // 合并分片
  mergeChunks(data) {
    return api.post('/videos/upload/merge', data)
  },

  // 删除视频
  deleteVideo(id) {
    return api.delete(`/videos/${id}`)
  },

  // 播放地址
  getStreamUrl(id) {
    return `/api/videos/${id}/stream`
  },

  // 下载地址
  getDownloadUrl(id) {
    return `/api/videos/${id}/download`
  },

  // 缩略图地址
  getThumbnailUrl(id) {
    return `/api/videos/${id}/thumbnail`
  },
}
