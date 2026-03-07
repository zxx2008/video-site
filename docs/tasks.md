# VideoHub MVP 开发任务清单

> 基于 [tech-design.md](./tech-design.md) 拆解，按开发顺序排列。
> 前置依赖标记为 `依赖: #N`，无标记表示可独立开始。

---

## 阶段一：项目初始化

### #1 后端项目初始化

**涉及文件：** `backend/`

- [ ] 创建 `backend/` 目录结构（`main.py`, `routers/`, `services/`, `db/`, `utils/`）
- [ ] 创建 `requirements.txt`，写入依赖（fastapi, uvicorn, aiosqlite, python-multipart, ffmpeg-python, aiofiles）
- [ ] 创建 Python 虚拟环境，安装依赖
- [ ] 编写 `main.py`，创建 FastAPI 应用实例，配置 CORS（允许前端开发端口 5173）
- [ ] 验证 `uvicorn main:app --reload --port 8000` 可正常启动
- [ ] 访问 `http://localhost:8000/docs` 确认 Swagger UI 可用

### #2 前端项目初始化

**涉及文件：** `frontend/`

- [ ] 使用 `npm create vue@latest` 创建 Vue 3 项目（选择 Vue Router）
- [ ] 安装依赖：`tailwindcss`, `axios`, `video.js`
- [ ] 配置 Tailwind CSS
- [ ] 配置 `vite.config.js` 中的 `/api` 代理指向 `http://localhost:8000`
- [ ] 验证 `npm run dev` 可正常启动，访问 `http://localhost:5173` 看到默认页面

### #3 创建运行时数据目录

**涉及文件：** `data/`, `.gitignore`

- [ ] 创建 `data/videos/`, `data/thumbs/`, `data/chunks/` 目录
- [ ] 在 `.gitignore` 中添加 `data/` 忽略规则
- [ ] 后端启动时自动检查并创建这些目录（在 `main.py` 的 startup 事件中）

---

## 阶段二：后端核心 API

### #4 数据库初始化

**依赖：** #1
**涉及文件：** `backend/db/schema.sql`, `backend/db/database.py`

- [ ] 编写 `schema.sql` 建表语句（videos 表 + created_at 索引）
- [ ] 编写 `database.py`：
  - 使用 aiosqlite 连接 `data/videohub.db`
  - 提供 `get_db()` 异步上下文管理器
  - 应用启动时自动执行 `schema.sql` 建表
- [ ] 验证启动后 `data/videohub.db` 文件生成，表结构正确

### #5 FFmpeg 工具函数

**依赖：** #1
**涉及文件：** `backend/utils/ffmpeg.py`

- [ ] 实现 `probe_video(file_path)` 函数：调用 ffprobe 返回 `{ duration, resolution, codec }`
- [ ] 实现 `generate_thumbnail(video_path, video_id)` 函数：截取第 1 秒画面，输出 320px 宽 JPG 到 `data/thumbs/{id}.jpg`
- [ ] 处理边界情况：视频不足 1 秒时截取第 0 秒；无视频流时返回默认值
- [ ] 用一个测试视频文件手动验证两个函数输出正确

### #6 文件类型校验工具

**依赖：** #1
**涉及文件：** `backend/services/video.py`

- [ ] 定义允许的 MIME 类型列表和扩展名列表
- [ ] 实现 `validate_video_file(filename, content_type)` 函数
- [ ] MIME 和扩展名必须同时匹配，任一不合法抛出 HTTPException(400)

### #7 整体上传接口

**依赖：** #4, #5, #6
**涉及文件：** `backend/routers/videos.py`, `backend/services/video.py`

- [ ] 实现 `POST /api/videos/upload`
  - 接收 `file: UploadFile` 和 `title: str`（可选，默认取文件名）
  - 调用文件类型校验
  - aiofiles 异步写入 `data/videos/{timestamp}_{filename}`（1MB 分块读写）
  - 调用 `probe_video()` 探测元信息
  - 调用 `generate_thumbnail()` 生成缩略图
  - INSERT 到 videos 表
  - 返回 201 + 视频记录 JSON
- [ ] 用 Swagger UI 或 curl 上传一个 MP4 文件验证完整流程
- [ ] 验证非视频文件上传返回 400

### #8 视频列表接口

**依赖：** #4
**涉及文件：** `backend/routers/videos.py`

- [ ] 实现 `GET /api/videos`
  - 接收查询参数 `page`（默认 1）, `pageSize`（默认 20）
  - 查询 videos 表，按 `created_at DESC` 排序
  - 返回 `{ items, total, page, pageSize }`
  - `thumbnail_path` 字段映射为 `/api/videos/{id}/thumbnail`
- [ ] 验证空列表、有数据、分页边界情况

### #9 视频详情接口

**依赖：** #4
**涉及文件：** `backend/routers/videos.py`

- [ ] 实现 `GET /api/videos/:id`
  - 查询单条视频记录
  - 存在返回 200 + 视频 JSON
  - 不存在返回 404 `{ "detail": "视频不存在" }`

### #10 视频流播放接口

**依赖：** #4
**涉及文件：** `backend/routers/videos.py`

- [ ] 实现 `GET /api/videos/:id/stream`
  - 查询 DB 获取 `storage_path` 和 `mime_type`
  - 解析请求头 `Range`
  - 有 Range：返回 206 + `Content-Range` + `StreamingResponse`
  - 无 Range：返回 200 + 完整文件流
  - 设置 `Accept-Ranges: bytes` 头
- [ ] 实现 `file_iterator(path, start, end)` 异步生成器（aiofiles 分块读取）
- [ ] 用浏览器直接访问验证视频可播放、可拖拽跳转

### #11 视频下载接口

**依赖：** #10
**涉及文件：** `backend/routers/videos.py`

- [ ] 实现 `GET /api/videos/:id/download`
  - 复用 stream 逻辑
  - 额外添加 `Content-Disposition: attachment; filename="原始文件名"` 头
- [ ] 验证浏览器触发下载而非播放

### #12 视频删除接口

**依赖：** #4
**涉及文件：** `backend/routers/videos.py`, `backend/services/video.py`

- [ ] 实现 `DELETE /api/videos/:id`
  - 查询 DB 获取 `storage_path` 和 `thumbnail_path`
  - 删除视频文件（`os.remove`，文件不存在不报错）
  - 删除缩略图文件（同上）
  - 删除数据库记录
  - 返回 200 `{ "message": "删除成功" }`
  - 视频不存在返回 404
- [ ] 验证删除后文件和 DB 记录均已清理

### #13 缩略图接口

**依赖：** #4
**涉及文件：** `backend/routers/videos.py`

- [ ] 实现 `GET /api/videos/:id/thumbnail`
  - 查询 DB 获取 `thumbnail_path`
  - 文件存在：返回 `FileResponse`，`Content-Type: image/jpeg`
  - 文件不存在：返回默认占位图（内置一个 placeholder）
- [ ] 验证有缩略图和无缩略图两种情况

### #14 分片上传接口

**依赖：** #5, #6
**涉及文件：** `backend/routers/videos.py`, `backend/services/video.py`

- [ ] 实现 `POST /api/videos/upload/chunk`
  - 接收 `file`, `uploadId`, `chunkIndex`, `totalChunks`, `filename`
  - 将分片写入 `data/chunks/{uploadId}/{chunkIndex}`
  - 返回 200 `{ "chunkIndex": N, "uploaded": true }`
- [ ] 实现 `POST /api/videos/upload/merge`
  - 接收 `uploadId`, `filename`, `totalChunks`, `title`
  - 验证所有分片存在（0 到 totalChunks-1）
  - 按序合并分片为完整文件写入 `data/videos/`
  - 校验文件类型
  - 调用 `probe_video()` + `generate_thumbnail()`
  - INSERT 到 videos 表
  - 删除 `data/chunks/{uploadId}/` 临时目录
  - 返回 201 + 视频记录
- [ ] 用脚本模拟分片上传验证完整流程
- [ ] 验证断点续传：中断后重新上传，已有分片跳过

### #15 路由注册与整体联调

**依赖：** #7 ~ #14
**涉及文件：** `backend/main.py`

- [ ] 在 `main.py` 中注册视频路由 `app.include_router(video_router, prefix="/api")`
- [ ] 用 Swagger UI 逐一测试所有接口
- [ ] 确认接口响应格式与 tech-design.md 一致

---

## 阶段三：前端基础框架

### #16 前端路由与布局

**依赖：** #2
**涉及文件：** `frontend/src/router/index.js`, `frontend/src/App.vue`

- [ ] 配置三条路由：`/`（HomeView）, `/upload`（UploadView）, `/video/:id`（VideoView）
- [ ] 创建三个空白页面组件占位
- [ ] 验证路由跳转正常

### #17 导航栏组件

**依赖：** #16
**涉及文件：** `frontend/src/components/NavBar.vue`, `frontend/src/App.vue`

- [ ] 实现 NavBar 组件：Logo（链接到首页）、上传按钮（链接到 /upload）
- [ ] 在 App.vue 中引入 NavBar，置于 `<router-view>` 之上
- [ ] 响应式：手机端 Logo 缩小，按钮保持可触控尺寸（≥ 44px）

### #18 API 封装层

**依赖：** #2
**涉及文件：** `frontend/src/api/videos.js`

- [ ] 创建 axios 实例（baseURL: `/api`）
- [ ] 封装以下方法：
  - `getVideos(page, pageSize)` → GET /api/videos
  - `getVideo(id)` → GET /api/videos/:id
  - `uploadVideo(file, title, onProgress)` → POST /api/videos/upload
  - `uploadChunk(formData)` → POST /api/videos/upload/chunk
  - `mergeChunks(data)` → POST /api/videos/upload/merge
  - `deleteVideo(id)` → DELETE /api/videos/:id
  - `getStreamUrl(id)` → 返回 URL 字符串
  - `getDownloadUrl(id)` → 返回 URL 字符串
  - `getThumbnailUrl(id)` → 返回 URL 字符串

---

## 阶段四：前端页面开发

### #19 首页 — 视频列表

**依赖：** #8, #13, #16, #17, #18
**涉及文件：** `frontend/src/views/HomeView.vue`, `frontend/src/components/VideoCard.vue`, `frontend/src/components/Pagination.vue`

- [ ] 实现 VideoCard 组件：
  - 展示缩略图（`/api/videos/:id/thumbnail`）、标题、时长、文件大小、上传时间
  - 点击跳转到 `/video/:id`
  - 时长格式化为 `mm:ss` 或 `hh:mm:ss`
  - 文件大小格式化为 `MB` / `GB`
- [ ] 实现 Pagination 组件：
  - 显示当前页/总页数
  - 上一页/下一页按钮
  - 首页/末页快捷跳转
- [ ] 实现 HomeView：
  - 页面加载时调用 `getVideos()` 获取数据
  - 网格布局：手机 1 列，平板 2 列，桌面 3-4 列
  - 空状态提示："暂无视频，去上传一个吧"
  - 分页器切换页码时重新请求数据
- [ ] 验证与后端联调：上传视频后首页正确显示

### #20 上传页 — 基础整体上传

**依赖：** #7, #16, #18
**涉及文件：** `frontend/src/views/UploadView.vue`

- [ ] 实现文件选择：点击按钮触发 `<input type="file" accept="video/*">`
- [ ] 实现标题输入框（默认填充文件名，可修改）
- [ ] 实现上传进度条：显示百分比 + 已传大小/总大小
- [ ] 调用 `uploadVideo()` 接口执行上传
- [ ] 上传成功后提示并跳转到视频播放页
- [ ] 上传失败显示错误信息
- [ ] 上传中禁用提交按钮，防止重复提交

### #21 上传页 — 分片上传逻辑

**依赖：** #14, #20
**涉及文件：** `frontend/src/views/UploadView.vue` 或 `frontend/src/utils/chunkedUpload.js`

- [ ] 实现分片上传工具函数：
  - 根据文件大小判断：< 100MB 走整体上传，≥ 100MB 走分片上传
  - 生成 uploadId：`MD5(文件名 + 文件大小 + lastModified)`（可用 spark-md5 库）
  - 将文件按 5MB 切片（`file.slice(start, end)`）
  - 控制并发数为 3
  - 计算总体上传进度（已完成分片数 / 总分片数）
  - 所有分片上传完成后调用 merge 接口
- [ ] 断点续传：上传前查询已上传的分片，跳过已完成的
- [ ] 上传页进度条兼容两种上传模式
- [ ] 验证大文件（> 100MB）分片上传全流程

### #22 播放页 — 视频播放器

**依赖：** #9, #10, #16, #18
**涉及文件：** `frontend/src/views/VideoView.vue`, `frontend/src/components/VideoPlayer.vue`

- [ ] 实现 VideoPlayer 组件：
  - 初始化 Video.js 播放器
  - 设置 `src` 为 `/api/videos/:id/stream`
  - 配置播放器控制条：播放/暂停、进度条、音量、全屏
  - 组件销毁时 dispose 播放器实例
- [ ] 实现 VideoView 页面：
  - 页面加载时调用 `getVideo(id)` 获取视频详情
  - 顶部渲染 VideoPlayer 组件（16:9 比例）
  - 下方展示视频信息：标题、时长、分辨率、文件大小、上传时间
  - 下载按钮：点击触发 `window.open(getDownloadUrl(id))`
  - 删除按钮：点击弹出确认对话框，确认后调用 `deleteVideo(id)`，删除成功跳转首页
  - 视频不存在时显示 404 提示

### #23 播放页 — 进度记忆

**依赖：** #22
**涉及文件：** `frontend/src/components/VideoPlayer.vue`

- [ ] 实现 `loadProgress(videoId)` — 从 localStorage 读取上次播放位置
- [ ] 实现 `saveProgress(videoId, currentTime)` — 节流保存（每 5 秒一次）
- [ ] 实现 `clearProgress(videoId)` — 播放结束时清除
- [ ] 播放器初始化后，如有存储进度则 `player.currentTime(savedTime)`
- [ ] 监听 `timeupdate` 事件，节流调用 `saveProgress`
- [ ] 监听 `ended` 事件，调用 `clearProgress`
- [ ] 验证：播放到一半关闭页面，重新打开后自动跳到上次位置

---

## 阶段五：响应式适配

### #24 全局响应式调整

**依赖：** #19, #20, #22
**涉及文件：** 所有前端组件

- [ ] 首页视频网格：`grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4`
- [ ] 导航栏：手机端紧凑布局，桌面端展开布局
- [ ] 上传页：手机端表单全宽，桌面端居中限宽
- [ ] 播放页：手机端播放器 100% 宽，桌面端最大 960px 居中
- [ ] 所有可点击元素尺寸 ≥ 44px（触屏友好）
- [ ] 手机端播放器支持横屏全屏
- [ ] 在 Chrome DevTools 模拟手机/平板/桌面三种尺寸验证

---

## 阶段六：联调与收尾

### #25 前后端完整联调

**依赖：** #15, #19, #20, #21, #22, #23, #24

- [ ] 启动后端（uvicorn）和前端（vite dev），走完全流程：
  1. 打开首页，确认空状态提示
  2. 进入上传页，上传一个小视频（< 100MB），验证进度条和跳转
  3. 回到首页，确认视频卡片显示（缩略图、标题、时长、大小）
  4. 点击卡片进入播放页，验证播放、拖拽、音量、全屏
  5. 播放到一半刷新页面，验证进度记忆续播
  6. 点击下载按钮，验证浏览器触发下载
  7. 点击删除按钮，确认后验证跳转首页且视频消失
  8. 上传一个大视频（≥ 100MB），验证分片上传流程
  9. 分片上传中途刷新页面，重新上传验证断点续传
  10. 用手机浏览器访问，验证所有功能可用

### #26 生产构建与部署验证

**依赖：** #25

- [ ] 前端执行 `npm run build`，确认 `frontend/dist/` 产出正常
- [ ] 后端配置 StaticFiles 托管 `frontend/dist/`（简化部署模式）
- [ ] 以生产模式启动：`uvicorn main:app --host 0.0.0.0 --port 8000`
- [ ] 验证通过 `http://服务器IP:8000` 可访问完整功能
- [ ] 编写 `nginx.conf` 配置示例文件
- [ ] 验证 Nginx 反向代理模式下前后端正常工作（如有 Nginx）

---

## 任务依赖关系图

```
阶段一 初始化
  #1 后端初始化 ──┬─► #4 数据库
  #2 前端初始化   │   #5 FFmpeg 工具
  #3 数据目录     │   #6 文件校验
                  │
阶段二 后端 API   │
  #4 ─────────────┼─► #7 整体上传 ──► #8 列表 ──► #9 详情
  #5 ─────────────┤                  #10 流播放 ──► #11 下载
  #6 ─────────────┤                  #12 删除
                  │                  #13 缩略图
                  ├─► #14 分片上传
                  └─► #15 路由注册与联调
                        │
阶段三 前端框架          │
  #16 路由布局 ──► #17 导航栏
  #18 API 封装           │
                         │
阶段四 前端页面          │
  #19 首页列表           │
  #20 基础上传 ──► #21 分片上传
  #22 播放页 ──► #23 进度记忆
                         │
阶段五 响应式            │
  #24 全局适配           │
                         │
阶段六 联调收尾          │
  #25 完整联调 ──► #26 部署验证
```
