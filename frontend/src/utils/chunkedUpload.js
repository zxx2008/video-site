import videosApi from '../api/videos'

const CHUNK_SIZE = 5 * 1024 * 1024 // 5MB
const CONCURRENCY = 3
const SIZE_THRESHOLD = 100 * 1024 * 1024 // 100MB

/**
 * Generate a simple uploadId from file properties
 */
function generateUploadId(file) {
  const raw = `${file.name}-${file.size}-${file.lastModified}`
  // Simple hash (FNV-1a inspired)
  let hash = 0x811c9dc5
  for (let i = 0; i < raw.length; i++) {
    hash ^= raw.charCodeAt(i)
    hash = (hash * 0x01000193) >>> 0
  }
  return hash.toString(16).padStart(8, '0')
}

/**
 * Upload a file — auto-selects whole or chunked based on size
 * @param {File} file
 * @param {string} title
 * @param {(progress: number) => void} onProgress
 * @returns {Promise<object>} video record
 */
export async function smartUpload(file, title, onProgress) {
  if (file.size < SIZE_THRESHOLD) {
    // Whole file upload
    const res = await videosApi.uploadVideo(file, title, onProgress)
    return res.data
  }

  // Chunked upload
  const uploadId = generateUploadId(file)
  const totalChunks = Math.ceil(file.size / CHUNK_SIZE)
  const completed = new Set()

  onProgress?.(0)

  // Upload chunks with concurrency control
  let nextIndex = 0

  async function uploadNext() {
    while (nextIndex < totalChunks) {
      const idx = nextIndex++
      const start = idx * CHUNK_SIZE
      const end = Math.min(start + CHUNK_SIZE, file.size)
      const blob = file.slice(start, end)

      const form = new FormData()
      form.append('file', blob)
      form.append('uploadId', uploadId)
      form.append('chunkIndex', idx)
      form.append('totalChunks', totalChunks)
      form.append('filename', file.name)

      await videosApi.uploadChunk(form)
      completed.add(idx)
      onProgress?.(Math.round((completed.size / totalChunks) * 95)) // 0-95% for chunks
    }
  }

  // Launch concurrent workers
  const workers = []
  for (let i = 0; i < Math.min(CONCURRENCY, totalChunks); i++) {
    workers.push(uploadNext())
  }
  await Promise.all(workers)

  // Merge
  onProgress?.(96)
  const res = await videosApi.mergeChunks({
    uploadId,
    filename: file.name,
    totalChunks,
    title: title || undefined,
  })
  onProgress?.(100)
  return res.data
}

export { SIZE_THRESHOLD }
