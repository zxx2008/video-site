# AGENTS.md

This file provides guidance to agentic coding assistants working with this repository.

## Project Overview

VideoHub — a self-hosted video management and streaming web platform with frontend-backend separation:
- **Frontend**: Vue 3 SPA (`frontend/`) — Vite + Tailwind CSS v4 + Vue Router + Axios + Video.js
- **Backend**: Python FastAPI (`backend/`) — Uvicorn + aiosqlite (SQLite) + ffmpeg-python + aiofiles
- **Data**: `data/` directory stores videos, thumbnails, upload chunks, and SQLite database

## Build and Development Commands

### Backend
```bash
cd backend
source venv/bin/activate
# Development server
uvicorn main:app --reload --port 8000
# Swagger UI: http://localhost:8000/docs
```

### Frontend
```bash
cd frontend
npm run dev          # Vite dev server at http://localhost:5173
npm run build        # Production build → frontend/dist/
npm run preview      # Preview production build locally
```

### Combined Development (using start.sh)
```bash
./start.sh           # Starts both backend (8000) and frontend (5173) servers
```

### Package Installation with Mirrors
**pip**: Must use Xiaomi internal mirror:
```bash
pip install -i https://pkgs.d.xiaomi.net/artifactory/api/pypi/pypi-virtual/simple --trusted-host pkgs.d.xiaomi.net <package>
```

**npm**: Use npmmirror:
```bash
npm install --registry=https://registry.npmmirror.com <package>
```

### Testing
**No test suite is currently implemented.** When adding tests:
- Backend: Use `pytest` with `pytest-asyncio` for async tests
- Frontend: Use `vitest` or `jest` with Vue Test Utils
- Create test files matching `*_test.py` (backend) or `*.spec.js` (frontend)

### Linting and Formatting
**No linting/formatting configuration exists.** Consider adding:
- Backend: `ruff` for linting, `black` for formatting
- Frontend: `eslint` with Vue plugin, `prettier`
- Run lint checks before committing

## Code Style Guidelines

### Python (Backend)

#### Imports
- Group imports: standard library, third-party, local modules
- Use absolute imports for project modules
- Import order: `import os`, `from pathlib import Path`, `from fastapi import ...`

Example:
```python
import os
import time
from pathlib import Path
from typing import Optional

import aiofiles
from fastapi import APIRouter, File, Form, UploadFile
from db.database import get_db
from services.video import validate_video_file
```

#### Naming Conventions
- **Variables/Functions**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private**: Prefix with `_` (e.g., `_internal_helper`)
- **Async functions**: Prefix with `async def`, use `await` appropriately

#### Error Handling
- Use `HTTPException` from FastAPI for API errors
- Provide descriptive Chinese error messages for user-facing errors
- Use `try-except` for external calls (ffmpeg, file operations)
- Return appropriate HTTP status codes: 400 (bad request), 404 (not found), 500 (internal error)

#### Type Hints
- Use Python type hints for function parameters and return values
- Example: `def probe_video(file_path: str) -> dict:`

#### Documentation
- Use docstrings for public functions/modules (Chinese or English)
- Inline comments in Chinese for complex logic

#### File Structure
- Router files in `backend/routers/` handle HTTP endpoints
- Service files in `backend/services/` contain business logic
- Utility files in `backend/utils/` for reusable helpers
- Database files in `backend/db/` for SQLite operations

### JavaScript/Vue (Frontend)

#### Imports
- Group imports: Vue/composition APIs, third-party, local modules
- Use ES6 `import/export` syntax
- Prefer named imports for Vue APIs

Example:
```javascript
import { computed, ref } from 'vue'
import axios from 'axios'
import videosApi from '../api/videos'
```

#### Component Structure (Vue SFC)
1. `<template>`: Use Tailwind CSS classes, `@` for event handlers, `:` for bindings
2. `<script setup>`: Use Composition API with `defineProps`, `defineEmits`
3. `<style>`: Typically empty (Tailwind handles styling)

#### Naming Conventions
- **Components**: `PascalCase` (e.g., `VideoCard.vue`)
- **Variables/Functions**: `camelCase`
- **Constants**: `UPPER_SNAKE_CASE` or `camelCase`
- **Composables**: `useCamelCase` (e.g., `useVideoPlayer`)
- **Props**: `camelCase` in JS, `kebab-case` in template

#### Vue Conventions
- Use `defineProps` with type objects
- Use `computed` for derived state
- Use `ref` for reactive primitives, `reactive` for objects
- Event handlers: `onEventName` pattern (e.g., `onImgError`)
- Template directives: prefer `v-if` over `v-show` when appropriate

#### Error Handling
- Use `try-catch` for API calls
- Handle image errors with `@error` binding
- Show user-friendly error messages

#### API Layer
- Centralize API calls in `src/api/` modules
- Use Axios with base URL `/api` (proxied in dev)
- Handle upload progress callbacks

## Project Structure Conventions

### Backend
```
backend/
├── main.py              # FastAPI app, CORS, static file serving
├── requirements.txt     # Python dependencies
├── routers/             # API endpoints (prefix: /api)
├── services/           # Business logic
├── utils/              # Helpers (ffmpeg, file ops)
├── db/                 # Database schema and connection
└── static/             # Static assets (placeholder.jpg)
```

### Frontend
```
frontend/
├── vite.config.js      # Vite config with proxy to backend
├── src/
│   ├── main.js         # Vue app entry
│   ├── App.vue         # Root component
│   ├── router/         # Vue Router configuration
│   ├── views/          # Page components (routes)
│   ├── components/     # Reusable UI components
│   ├── api/            # API client modules
│   ├── utils/          # Helper functions
│   └── assets/         # Static assets
```

### Data Directory
```
data/                   # Created at runtime
├── videos/            # Original uploaded video files
├── thumbs/            # Generated thumbnails (ID.jpg)
├── chunks/            # Temporary upload chunks
└── videohub.db        # SQLite database
```

## Key Design Decisions

- **No authentication**: All endpoints public
- **SQLite single table**: `videos` table only
- **File naming**: `{timestamp}_{filename}` for videos, `{id}.jpg` for thumbnails
- **Upload strategy**: <100MB whole-file, ≥100MB chunked (5MB chunks)
- **Video streaming**: HTTP Range requests with `StreamingResponse`
- **Thumbnail generation**: FFmpeg extracts frame at 1s, 320px width
- **File validation**: MIME type + extension double-check

## When Adding New Features

1. **Backend first**: Implement API endpoint in `backend/routers/`
2. **Add service layer** if complex logic in `backend/services/`
3. **Update database schema** if needed in `backend/db/schema.sql`
4. **Frontend integration**: Add API method in `frontend/src/api/`
5. **Create/update Vue components** in appropriate directory
6. **Test manually** using Swagger UI (backend) and browser (frontend)

## Commit Message Convention

Use descriptive commit messages in English:
- `feat: add chunked upload support`
- `fix: correct thumbnail generation for short videos`
- `refactor: extract video validation logic to service`
- `docs: update API documentation`

## Production Deployment

- Build frontend: `cd frontend && npm run build`
- Backend serves static files from `frontend/dist/` when exists
- Alternative: Use Nginx reverse proxy (see `nginx.conf`)
- Ensure `data/` directory is writable and has sufficient storage