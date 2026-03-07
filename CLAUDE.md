# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

VideoHub — a self-hosted video management and streaming web platform. Users can upload, browse, play, download, and delete videos via browser. No authentication; fully open access. Designed for personal/NAS and small team use on internal networks.

## Architecture

Frontend-backend separation:
- **Frontend**: Vue 3 SPA (`frontend/`) — Vite + Tailwind CSS v4 + Vue Router + Axios + Video.js
- **Backend**: Python FastAPI (`backend/`) — Uvicorn + aiosqlite (SQLite) + ffmpeg-python + aiofiles
- **Data**: `data/` directory at project root stores videos, thumbnails, upload chunks, and the SQLite database file

In development, Vite proxies `/api/*` to the backend at `:8000`. In production, either Nginx reverse-proxies or FastAPI serves the frontend static files directly.

## Development Commands

### Backend
```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --port 8000
```
Swagger UI at http://localhost:8000/docs

### Frontend
```bash
cd frontend
npm run dev          # Vite dev server at http://localhost:5173
npm run build        # Production build → frontend/dist/
```

### MANDATORY: Package Mirror Sources

**pip**: PyPI 官方源不可达，所有 `pip install` 命令必须使用小米内部镜像源，否则会安装失败：
```bash
pip install -i https://pkgs.d.xiaomi.net/artifactory/api/pypi/pypi-virtual/simple --trusted-host pkgs.d.xiaomi.net <package>
```

**npm**: 使用 npmmirror 镜像：
```bash
npm install --registry=https://registry.npmmirror.com <package>
```

### System dependencies
- Python 3.12+, Node.js 20+, FFmpeg (`sudo apt install ffmpeg`)

## Key Design Decisions

- **No auth**: All endpoints are public, no login/session/JWT
- **SQLite single table**: `videos` table only, database at `data/videohub.db`
- **File storage convention**: Videos at `data/videos/{timestamp}_{filename}`, thumbnails at `data/thumbs/{id}.jpg`, chunks at `data/chunks/{uploadId}/{chunkIndex}`
- **Upload strategy**: Files < 100MB use whole-file upload (`POST /api/videos/upload`); ≥ 100MB use chunked upload (5MB chunks, 3 concurrent) with `POST /api/videos/upload/chunk` + `POST /api/videos/upload/merge`
- **Video streaming**: HTTP Range requests via `StreamingResponse` + `aiofiles`, returns 206 Partial Content
- **Thumbnail generation**: FFmpeg extracts frame at 1 second, 320px wide JPG
- **Playback progress**: Stored in browser localStorage, throttled save every 5 seconds
- **File type validation**: MIME + extension double check; allowed formats: MP4, MKV, AVI, MOV, WMV, FLV, WebM

## Design Documents

Detailed requirements, scope, task breakdown, and technical architecture are in `docs/`:
- `docs/prd.md` — Product requirements
- `docs/scope.md` — MVP scope and acceptance criteria
- `docs/tech-design.md` — Full technical design with API specs, DB schema, implementation details
- `docs/tasks.md` — 26 development tasks across 6 phases with dependency graph
