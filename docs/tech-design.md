# VideoHub 技术架构设计

> 基于 [PRD v1.1](./prd.md) 和 [MVP 范围文档](./scope.md)，本文档定义系统的技术架构、项目结构、接口协议与关键实现方案。

---

## 1. 架构总览

```
┌─────────────────────────────────────────────────────┐
│                     浏览器                           │
│  Vue 3 SPA (Vite + Tailwind CSS + Vue Router)       │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │
│  │ 首页列表  │  │ 上传页面  │  │ 播放页(Video.js) │   │
│  └──────────┘  └──────────┘  └──────────────────┘   │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP / JSON / multipart
                       │
┌──────────────────────▼──────────────────────────────┐
│                  Nginx (可选)                         │
│         静态文件托管 / 反向代理 /api → 后端            │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│            Python 后端 (FastAPI + Uvicorn)            │
│  ┌───────────┐  ┌────────────┐  ┌────────────────┐  │
│  │ 视频 CRUD  │  │ 文件上传    │  │ 流式播放/下载   │  │
│  │  Router    │  │ (UploadFile)│  │ (Range 支持)   │  │
│  └─────┬─────┘  └─────┬──────┘  └───────┬────────┘  │
│        │              │                  │           │
│  ┌─────▼──────────────▼──────────────────▼────────┐  │
│  │              Service 层                         │  │
│  │  视频元信息探测 (ffmpeg-python)                   │  │
│  └─────────────────────┬──────────────────────────┘  │
│                        │                             │
│  ┌─────────────────────▼──────────────────────────┐  │
│  │              SQLite (aiosqlite)                 │  │
│  └────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
                       │
              ┌────────▼────────┐
              │   本地磁盘存储    │
              │  data/videos/   │
              │  data/thumbs/   │
              └─────────────────┘
```

### 前后端分离策略

| 关注点 | 方案 |
|--------|------|
| 开发阶段 | 前端 Vite dev server (端口 5173) 通过 proxy 转发 `/api/*` 到后端 (端口 8000) |
| 生产部署 | 前端 `vite build` 输出静态文件，由 Nginx 托管；Nginx 反向代理 `/api/*` 到 Uvicorn 后端 |
| 替代方案 | 无 Nginx 时，FastAPI 通过 `StaticFiles` 同时托管前端静态文件和 API（单进程部署） |

---

## 2. 技术选型

| 层级 | 技术 | 版本 | 选型理由 |
|------|------|------|---------|
| 前端框架 | Vue 3 (Composition API) | 3.x | 轻量、响应式、生态成熟 |
| 构建工具 | Vite | 6.x | 开发体验好，HMR 快 |
| CSS | Tailwind CSS | 4.x | 原子化 CSS，响应式断点开箱可用 |
| 路由 | Vue Router | 4.x | 官方路由，SPA 标配 |
| HTTP 客户端 | Axios | 1.x | 上传进度回调、拦截器 |
| 播放器 | Video.js | 8.x | 功能完整、移动端兼容、插件生态 |
| 后端框架 | FastAPI | 0.115+ | 异步高性能，自带 API 文档，类型安全 |
| ASGI 服务器 | Uvicorn | 0.34+ | FastAPI 标配，支持异步 I/O |
| 数据库 | SQLite via aiosqlite | — | 异步操作，零配置，单文件数据库 |
| 视频处理 | ffmpeg-python | 0.2+ | FFmpeg 的 Python 封装，调用简洁 |
| 运行时 | Python | 3.11+ | 性能提升显著，类型提示完善 |
| 包管理 | pip + requirements.txt | — | Python 标准方式 |

---

## 3. 项目结构

```
video-site/
├── docs/                          # 文档
│   ├── prd.md
│   ├── scope.md
│   └── tech-design.md
│
├── frontend/                      # 前端项目 (Vue 3)
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── src/
│   │   ├── main.js                # 入口
│   │   ├── App.vue                # 根组件
│   │   ├── router/
│   │   │   └── index.js           # 路由定义
│   │   ├── views/                 # 页面组件
│   │   │   ├── HomeView.vue       # 首页 — 视频列表
│   │   │   ├── UploadView.vue     # 上传页
│   │   │   └── VideoView.vue      # 播放页
│   │   ├── components/            # 通用组件
│   │   │   ├── VideoCard.vue      # 视频卡片
│   │   │   ├── VideoPlayer.vue    # 播放器封装
│   │   │   ├── Pagination.vue     # 分页器
│   │   │   └── NavBar.vue         # 导航栏
│   │   ├── api/
│   │   │   └── videos.js          # API 调用封装
│   │   └── assets/                # 静态资源
│   │       └── placeholder.svg    # 缩略图占位图
│   └── public/
│
├── backend/                       # 后端项目 (FastAPI)
│   ├── requirements.txt           # Python 依赖
│   ├── main.py                    # 应用入口，Uvicorn 启动
│   ├── routers/
│   │   └── videos.py              # /api/videos 路由
│   ├── services/
│   │   └── video.py               # 视频业务逻辑
│   ├── db/
│   │   ├── database.py            # 数据库连接与初始化
│   │   └── schema.sql             # 建表语句
│   └── utils/
│       └── ffmpeg.py              # FFmpeg 元信息探测
│
├── data/                          # 运行时数据（gitignore）
│   ├── videos/                    # 视频文件存储
│   ├── thumbs/                    # 缩略图存储
│   ├── chunks/                    # 分片临时存储（合并后自动清理）
│   └── videohub.db                # SQLite 数据库文件
│
└── nginx.conf                     # Nginx 配置示例（可选）
```

### 后端依赖 (requirements.txt)

```
fastapi>=0.115.0
uvicorn[standard]>=0.34.0
aiosqlite>=0.20.0
python-multipart>=0.0.18
ffmpeg-python>=0.2.0
aiofiles>=24.1.0
```

---

## 4. API 详细设计

所有接口前缀 `/api`，数据格式 JSON，文件上传使用 `multipart/form-data`。

FastAPI 自动生成交互式 API 文档：
- Swagger UI：`http://localhost:8000/docs`
- ReDoc：`http://localhost:8000/redoc`

### 4.1 获取视频列表

```
GET /api/videos?page=1&pageSize=20
```

**响应 200：**

```json
{
  "items": [
    {
      "id": 1,
      "title": "示例视频",
      "filename": "example.mp4",
      "mime_type": "video/mp4",
      "file_size": 104857600,
      "duration": 120.5,
      "resolution": "1920x1080",
      "codec": "h264",
      "thumbnail_path": "/api/videos/1/thumbnail",
      "created_at": "2026-03-06T10:00:00.000Z"
    }
  ],
  "total": 50,
  "page": 1,
  "pageSize": 20
}
```

### 4.2 获取视频详情

```
GET /api/videos/:id
```

**响应 200：** 同列表中的单个对象。

**响应 404：**

```json
{ "detail": "视频不存在" }
```

### 4.3 上传视频

```
POST /api/videos/upload
Content-Type: multipart/form-data

字段:
  file: (二进制文件)
  title: (可选，字符串)
```

**处理流程：**

1. FastAPI `UploadFile` 接收文件，异步写入 `data/videos/`
2. 校验 MIME 类型和扩展名
3. 调用 FFmpeg 探测元信息（duration、resolution、codec）
4. 写入数据库
5. 返回视频记录

**响应 201：**

```json
{
  "id": 2,
  "title": "my-video.mp4",
  "filename": "my-video.mp4",
  "file_size": 52428800,
  "duration": 60.0,
  "resolution": "1280x720",
  "codec": "h264",
  "created_at": "2026-03-06T12:00:00.000Z"
}
```

**响应 400：**

```json
{ "detail": "不支持的文件类型" }
```

### 4.4 删除视频

```
DELETE /api/videos/:id
```

**处理流程：**

1. 查询数据库获取 `storage_path`
2. 删除磁盘文件（视频 + 缩略图）
3. 删除数据库记录

**响应 200：**

```json
{ "message": "删除成功" }
```

### 4.5 视频流播放

```
GET /api/videos/:id/stream
```

**关键实现：**

- 读取请求头 `Range: bytes=start-end`
- 有 Range 时：返回 `206 Partial Content`，设置 `Content-Range` 头
- 无 Range 时：返回 `200`，完整文件流
- 设置 `Content-Type` 为视频的 MIME 类型
- 使用 FastAPI `StreamingResponse` 流式输出，配合 `aiofiles` 异步读取文件

**响应头示例（206）：**

```
HTTP/1.1 206 Partial Content
Content-Range: bytes 0-1048575/104857600
Content-Length: 1048576
Content-Type: video/mp4
Accept-Ranges: bytes
```

### 4.6 分片上传 — 上传分片

```
POST /api/videos/upload/chunk
Content-Type: multipart/form-data

字段:
  file: (分片二进制数据)
  uploadId: (字符串，文件唯一标识，由前端根据文件名+大小+修改时间生成哈希)
  chunkIndex: (整数，分片序号，从 0 开始)
  totalChunks: (整数，总分片数)
  filename: (字符串，原始文件名)
```

**响应 200：**

```json
{ "chunkIndex": 0, "uploaded": true }
```

### 4.7 分片上传 — 合并分片

```
POST /api/videos/upload/merge
Content-Type: application/json

{
  "uploadId": "abc123",
  "filename": "my-video.mp4",
  "totalChunks": 10,
  "title": "我的视频"
}
```

**处理流程：**

1. 按序读取所有分片，合并为完整文件写入 `data/videos/`
2. 校验 MIME 类型和扩展名
3. 调用 FFmpeg 探测元信息
4. 调用 FFmpeg 生成缩略图
5. 写入数据库
6. 清理临时分片文件
7. 返回视频记录

**响应 201：** 同 4.3 上传视频响应。

### 4.8 获取缩略图

```
GET /api/videos/:id/thumbnail
```

**响应 200：** 返回 JPG 图片，`Content-Type: image/jpeg`

**响应 404：** 缩略图不存在时返回默认占位图。

### 4.9 视频下载

```
GET /api/videos/:id/download
```

**与 stream 的区别：**

- 增加 `Content-Disposition: attachment; filename="原始文件名"` 头
- 同样支持 Range 断点续传

---

## 5. 数据库设计

### 5.1 建表 SQL

```sql
CREATE TABLE IF NOT EXISTS videos (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    title         TEXT    NOT NULL,
    filename      TEXT    NOT NULL,
    storage_path  TEXT    NOT NULL,
    thumbnail_path TEXT   DEFAULT NULL,
    mime_type     TEXT    NOT NULL,
    file_size     INTEGER NOT NULL,
    duration      REAL    DEFAULT 0,
    resolution    TEXT    DEFAULT '',
    codec         TEXT    DEFAULT '',
    created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_videos_created_at ON videos(created_at DESC);
```

### 5.2 存储规则

- 视频文件保存路径：`data/videos/{timestamp}_{原始文件名}`
- 缩略图保存路径：`data/thumbs/{id}.jpg`（上传后 FFmpeg 自动生成）
- 分片临时目录：`data/chunks/{uploadId}/`（合并后自动清理）
- 数据库文件路径：`data/videohub.db`

---

## 6. 关键实现方案

### 6.1 文件上传

```
浏览器                         FastAPI 后端
  │                                │
  │  POST /api/videos/upload       │
  │  Content-Type: multipart       │
  │  ──────────────────────────►   │
  │                                ├─ UploadFile 接收
  │                                ├─ 校验 MIME + 扩展名
  │                                ├─ aiofiles 异步写入 data/videos/
  │                                ├─ ffprobe 探测元信息
  │                                ├─ ffmpeg 生成缩略图
  │                                ├─ INSERT INTO videos
  │  ◄──────────────────────────   │
  │  201 { id, title, ... }        │
  │                                │
```

**文件类型校验：**

```
允许的 MIME 类型:
  video/mp4, video/x-matroska, video/avi, video/quicktime,
  video/x-ms-wmv, video/x-flv, video/webm

允许的扩展名:
  .mp4, .mkv, .avi, .mov, .wmv, .flv, .webm
```

校验策略：MIME 类型和扩展名必须同时匹配，两者任一不合法则拒绝。

**上传实现要点：**

```python
@router.post("/upload", status_code=201)
async def upload_video(
    file: UploadFile = File(...),
    title: str = Form(default=None),
):
    # 1. 校验文件类型
    validate_video_file(file.filename, file.content_type)

    # 2. 异步写入磁盘
    storage_path = generate_storage_path(file.filename)
    async with aiofiles.open(storage_path, "wb") as f:
        while chunk := await file.read(1024 * 1024):  # 1MB 分块读写
            await f.write(chunk)

    # 3. FFmpeg 探测元信息
    metadata = probe_video(storage_path)

    # 4. FFmpeg 生成缩略图
    thumbnail_path = generate_thumbnail(storage_path, video_id)

    # 5. 写入数据库并返回
    video = await db_insert_video(...)
    return video
```

### 6.2 视频流播放（Range 请求）

```
浏览器 <video> 标签               FastAPI 后端
  │                                │
  │  GET /api/videos/1/stream      │
  │  Range: bytes=0-               │
  │  ──────────────────────────►   │
  │                                ├─ 查询 DB 获取 storage_path
  │                                ├─ os.path.getsize 获取文件大小
  │                                ├─ 解析 Range 头
  │  ◄──────────────────────────   │
  │  206 Partial Content           │
  │  Content-Range: bytes 0-...    │
  │  (StreamingResponse)           │
  │                                │
  │  ── 用户拖拽进度条 ──           │
  │                                │
  │  GET /api/videos/1/stream      │
  │  Range: bytes=52428800-        │
  │  ──────────────────────────►   │
  │                                ├─ aiofiles.open + seek(start)
  │  ◄──────────────────────────   │
  │  206 Partial Content           │
  │                                │
```

**流式响应实现要点：**

```python
@router.get("/{video_id}/stream")
async def stream_video(video_id: int, request: Request):
    video = await db_get_video(video_id)
    file_path = video["storage_path"]
    file_size = os.path.getsize(file_path)

    range_header = request.headers.get("range")
    if range_header:
        start, end = parse_range(range_header, file_size)
        return StreamingResponse(
            file_iterator(file_path, start, end),
            status_code=206,
            headers={
                "Content-Range": f"bytes {start}-{end}/{file_size}",
                "Content-Length": str(end - start + 1),
                "Accept-Ranges": "bytes",
            },
            media_type=video["mime_type"],
        )

    return StreamingResponse(
        file_iterator(file_path, 0, file_size - 1),
        media_type=video["mime_type"],
        headers={"Accept-Ranges": "bytes"},
    )
```

### 6.3 FFmpeg 元信息探测

上传完成后调用 `ffprobe` 提取：

```json
{
  "duration": 120.5,
  "resolution": "1920x1080",
  "codec": "h264"
}
```

**实现方式：**

```python
import ffmpeg

def probe_video(file_path: str) -> dict:
    probe = ffmpeg.probe(file_path)
    video_stream = next(
        s for s in probe["streams"] if s["codec_type"] == "video"
    )
    return {
        "duration": float(probe["format"].get("duration", 0)),
        "resolution": f"{video_stream['width']}x{video_stream['height']}",
        "codec": video_stream.get("codec_name", ""),
    }
```

### 6.4 分片上传

```
浏览器                              FastAPI 后端
  │                                     │
  │  ── 前端将文件切分为 5MB 分片 ──      │
  │                                     │
  │  POST /api/videos/upload/chunk      │
  │  { uploadId, chunkIndex: 0, ... }   │
  │  ──────────────────────────────►    │
  │                                     ├─ 写入 data/chunks/{uploadId}/0
  │  ◄──────────────────────────────    │
  │  200 { chunkIndex: 0, uploaded }    │
  │                                     │
  │  ... 重复上传剩余分片 ...            │
  │                                     │
  │  POST /api/videos/upload/merge      │
  │  { uploadId, filename, totalChunks }│
  │  ──────────────────────────────►    │
  │                                     ├─ 按序合并分片 → data/videos/
  │                                     ├─ 清理 data/chunks/{uploadId}/
  │                                     ├─ ffprobe 探测元信息
  │                                     ├─ ffmpeg 生成缩略图
  │                                     ├─ INSERT INTO videos
  │  ◄──────────────────────────────    │
  │  201 { id, title, ... }             │
  │                                     │
```

**前端分片策略：**

- 分片大小：5MB
- uploadId 生成：`MD5(文件名 + 文件大小 + 最后修改时间)`
- 上传前先查询已上传分片列表，跳过已完成的分片（断点续传）
- 并发上传分片数：3（控制带宽占用）
- 文件 < 100MB 时使用整体上传接口，≥ 100MB 时自动切换为分片上传

**后端分片存储：**

```python
# 分片保存路径
data/chunks/{uploadId}/0
data/chunks/{uploadId}/1
data/chunks/{uploadId}/2
...
```

### 6.5 缩略图生成

上传完成后调用 FFmpeg 截取视频第 1 秒画面：

```python
import ffmpeg

def generate_thumbnail(video_path: str, video_id: int) -> str:
    thumbnail_path = f"data/thumbs/{video_id}.jpg"
    (
        ffmpeg
        .input(video_path, ss=1)
        .filter("scale", 320, -1)
        .output(thumbnail_path, vframes=1)
        .overwrite_output()
        .run(quiet=True)
    )
    return thumbnail_path
```

- 截取时间点：第 1 秒（`ss=1`）
- 输出尺寸：宽度 320px，高度等比缩放
- 输出格式：JPEG
- 如果视频不足 1 秒则截取第 0 秒

### 6.6 播放进度记忆

纯前端实现，基于 localStorage：

```js
// VideoPlayer.vue 中的逻辑

// 存储格式：{ "video_3": 120.5, "video_7": 45.2, ... }
const STORAGE_KEY = 'videohub_progress'

// 读取进度 — 播放器初始化时调用
function loadProgress(videoId) {
  const data = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}')
  return data[`video_${videoId}`] || 0
}

// 保存进度 — 播放器 timeupdate 事件中节流调用（每 5 秒保存一次）
function saveProgress(videoId, currentTime) {
  const data = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}')
  data[`video_${videoId}`] = currentTime
  localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
}

// 清除进度 — 视频播放完毕时调用
function clearProgress(videoId) {
  const data = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}')
  delete data[`video_${videoId}`]
  localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
}
```

---

## 7. 前端架构

### 7.1 路由

```js
const routes = [
  { path: '/',           name: 'home',   component: HomeView   },
  { path: '/upload',     name: 'upload', component: UploadView },
  { path: '/video/:id',  name: 'video',  component: VideoView  },
]
```

### 7.2 组件关系

```
App.vue
├── NavBar.vue                  # 全局导航栏
└── <router-view>
    ├── HomeView.vue            # 首页
    │   ├── VideoCard.vue × N   # 视频卡片（循环渲染）
    │   └── Pagination.vue      # 分页器
    ├── UploadView.vue          # 上传页
    └── VideoView.vue           # 播放页
        └── VideoPlayer.vue     # Video.js 封装
```

### 7.3 API 封装

`frontend/src/api/videos.js` 统一封装所有后端调用：

```js
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

  // 删除视频
  deleteVideo(id) {
    return api.delete(`/videos/${id}`)
  },

  // 播放地址（直接拼 URL，供 <video> src 使用）
  getStreamUrl(id) {
    return `/api/videos/${id}/stream`
  },

  // 下载地址
  getDownloadUrl(id) {
    return `/api/videos/${id}/download`
  },
}
```

### 7.4 Vite 开发代理

```js
// vite.config.js
export default defineConfig({
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
```

---

## 8. 响应式设计方案

基于 Tailwind CSS 断点实现：

| 断点 | 宽度 | 视频卡片网格列数 | 播放器宽度 |
|------|------|-----------------|-----------|
| 手机 | < 768px | 1 列 | 100% |
| 平板 | 768px - 1024px | 2 列 | 100% |
| 桌面 | > 1024px | 3-4 列 | 最大 960px 居中 |

Tailwind 类示例：

```html
<!-- 视频卡片网格 -->
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
  <VideoCard v-for="video in videos" :key="video.id" :video="video" />
</div>
```

---

## 9. 部署架构

### 9.1 单机部署（推荐）

```
┌─────────────────────────────────────────┐
│              服务器 / NAS                │
│                                         │
│  ┌──────────────────────────────────┐   │
│  │            Nginx                  │   │
│  │  :80                              │   │
│  │  /          → 前端静态文件         │   │
│  │  /api/*     → proxy 127.0.0.1:8000│   │
│  └──────────────────────────────────┘   │
│                                         │
│  ┌──────────────────────────────────┐   │
│  │  Uvicorn + FastAPI :8000          │   │
│  │  + SQLite + 本地磁盘存储           │   │
│  └──────────────────────────────────┘   │
│                                         │
│  data/                                  │
│  ├── videohub.db                        │
│  ├── videos/                            │
│  └── thumbs/                            │
└─────────────────────────────────────────┘
```

### 9.2 简化部署（无 Nginx）

FastAPI 直接托管前端静态文件：

```python
# main.py
from fastapi.staticfiles import StaticFiles

# API 路由先注册
app.include_router(video_router, prefix="/api")

# 前端静态文件托管
app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="spa")
```

此模式只需启动一个 Uvicorn 进程，适合最简化部署。

### 9.3 Nginx 配置示例

```nginx
server {
    listen 80;
    server_name _;
    client_max_body_size 4G;

    # 前端静态文件
    location / {
        root /opt/videohub/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # API 反向代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 600s;
        proxy_send_timeout 600s;
        client_max_body_size 4G;
    }
}
```

---

## 10. 开发与运行命令

```bash
# --- 后端 ---
cd backend
python -m venv venv                   # 创建虚拟环境
source venv/bin/activate              # 激活虚拟环境（Linux/macOS）
pip install -r requirements.txt       # 安装依赖
uvicorn main:app --reload --port 8000 # 开发模式，热重载

# --- 前端 ---
cd frontend
npm install
npm run dev                           # Vite 开发服务器 http://localhost:5173

# --- 生产构建与启动 ---
cd frontend && npm run build          # 输出到 frontend/dist/
cd backend && uvicorn main:app --host 0.0.0.0 --port 8000  # 生产启动

# --- 系统依赖 ---
# Python 3.11+
sudo apt install python3 python3-venv python3-pip   # Debian/Ubuntu

# FFmpeg (元信息探测)
sudo apt install ffmpeg               # Debian/Ubuntu
brew install ffmpeg                   # macOS
```

---

## 11. M2/M3 扩展预留

当前架构已为后续迭代预留扩展点：

| 后续功能 | 扩展方式 |
|---------|---------|
| 播放速度调节 | Video.js 内置支持，配置 `playbackRates: [0.5, 1, 1.5, 2]` |
| 搜索与排序 | 列表 API 增加 `keyword` / `sort` / `order` 查询参数，SQL 追加 WHERE/ORDER BY |
| 实时转码 | 新增转码 Service，使用 `ffmpeg -i input -c:v libx264 -f mp4 -movflags frag_keyframe+empty_moov pipe:1` 流式输出 |
