import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from db.database import init_db
from routers.videos import router as video_router

# 项目根目录（video-site/）
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path("/mnt/mydisk/video-site")

# 运行时数据目录
VIDEOS_DIR = DATA_DIR / "videos"
THUMBS_DIR = DATA_DIR / "thumbs"
CHUNKS_DIR = DATA_DIR / "chunks"
PLAYBACK_DIR = DATA_DIR / "playback"
DB_PATH = DATA_DIR / "videohub.db"


def ensure_data_dirs():
    """确保运行时数据目录存在"""
    for d in [VIDEOS_DIR, THUMBS_DIR, CHUNKS_DIR, PLAYBACK_DIR]:
        d.mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时
    ensure_data_dirs()
    await init_db()
    yield
    # 关闭时（无清理操作）


app = FastAPI(
    title="VideoHub",
    description="远程视频播放平台 API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS 配置：允许前端开发服务器访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(video_router, prefix="/api")


@app.get("/api/health")
async def health_check():
    return {"status": "ok"}


# 生产模式：托管前端静态文件（npm run build 产出）
FRONTEND_DIST = BASE_DIR / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="static")

    @app.get("/{full_path:path}")
    async def serve_spa(request: Request, full_path: str):
        """SPA fallback: 非 /api 路径统一返回 index.html"""
        file_path = FRONTEND_DIST / full_path
        if full_path and file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(FRONTEND_DIST / "index.html"))
