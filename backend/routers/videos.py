import os
import time
import shutil
from pathlib import Path
from typing import Optional

import aiofiles
from fastapi import APIRouter, File, Form, UploadFile, Request, Depends, HTTPException
from fastapi.responses import FileResponse, StreamingResponse

from db.database import get_db
from services.video import validate_video_file
from utils.ffmpeg import (
    probe_video,
    generate_thumbnail,
    generate_playback_video,
    has_non_square_pixels,
)

DATA_DIR = Path("/mnt/mydisk/video-site")
VIDEOS_DIR = DATA_DIR / "videos"
THUMBS_DIR = DATA_DIR / "thumbs"
CHUNKS_DIR = DATA_DIR / "chunks"

# 默认占位缩略图
PLACEHOLDER_THUMB = Path(__file__).resolve().parent.parent / "static" / "placeholder.jpg"

router = APIRouter(prefix="/videos", tags=["videos"])


# ==================== #8 视频列表 ====================

@router.get("")
async def list_videos(page: int = 1, pageSize: int = 20, db=Depends(get_db)):
    offset = (page - 1) * pageSize

    cursor = await db.execute("SELECT COUNT(*) FROM videos")
    row = await cursor.fetchone()
    total = row[0]

    cursor = await db.execute(
        "SELECT * FROM videos ORDER BY created_at DESC LIMIT ? OFFSET ?",
        (pageSize, offset),
    )
    rows = await cursor.fetchall()

    items = []
    for r in rows:
        item = dict(r)
        item["thumbnail_path"] = f"/api/videos/{item['id']}/thumbnail"
        items.append(item)

    return {"items": items, "total": total, "page": page, "pageSize": pageSize}


# ==================== #9 视频详情 ====================

@router.get("/{video_id}")
async def get_video(video_id: int, db=Depends(get_db)):
    cursor = await db.execute("SELECT * FROM videos WHERE id = ?", (video_id,))
    row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="视频不存在")
    item = dict(row)
    item["thumbnail_path"] = f"/api/videos/{item['id']}/thumbnail"
    return item


# ==================== #7 整体上传 ====================

@router.post("/upload", status_code=201)
async def upload_video(
    file: UploadFile = File(...),
    title: Optional[str] = Form(default=None),
    db=Depends(get_db),
):
    filename = file.filename or ""
    content_type = file.content_type or ""
    validate_video_file(filename, content_type)

    if not title:
        title = Path(filename).stem

    # 写入磁盘
    storage_filename = f"{int(time.time())}_{filename}"
    storage_path = str(VIDEOS_DIR / storage_filename)

    file_size = 0
    async with aiofiles.open(storage_path, "wb") as f:
        while chunk := await file.read(1024 * 1024):  # 1MB
            await f.write(chunk)
            file_size += len(chunk)

    # 探测元信息
    metadata = probe_video(storage_path)

    # 写入数据库
    cursor = await db.execute(
        """INSERT INTO videos (title, filename, storage_path, mime_type, file_size,
           duration, resolution, sample_aspect_ratio, display_aspect_ratio, codec)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (title, filename, storage_path, content_type, file_size,
         metadata["duration"], metadata["resolution"], metadata["sample_aspect_ratio"],
         metadata["display_aspect_ratio"], metadata["codec"]),
    )
    await db.commit()
    video_id = cursor.lastrowid

    # 生成方形像素播放副本（仅针对非 1:1 像素宽高比）
    if has_non_square_pixels(metadata["sample_aspect_ratio"]):
        playback_path = generate_playback_video(storage_path, video_id)
        if playback_path:
            await db.execute(
                "UPDATE videos SET playback_path = ? WHERE id = ?",
                (playback_path, video_id),
            )
            await db.commit()

    # 生成缩略图
    thumb_path = generate_thumbnail(storage_path, video_id)
    if thumb_path:
        await db.execute(
            "UPDATE videos SET thumbnail_path = ? WHERE id = ?",
            (thumb_path, video_id),
        )
        await db.commit()

    # 返回完整记录
    cursor = await db.execute("SELECT * FROM videos WHERE id = ?", (video_id,))
    row = await cursor.fetchone()
    item = dict(row)
    item["thumbnail_path"] = f"/api/videos/{video_id}/thumbnail"
    return item


# ==================== #10 视频流播放 ====================

async def file_iterator(file_path: str, start: int, end: int, chunk_size: int = 1024 * 1024):
    """异步文件分块读取生成器"""
    async with aiofiles.open(file_path, "rb") as f:
        await f.seek(start)
        remaining = end - start + 1
        while remaining > 0:
            read_size = min(chunk_size, remaining)
            data = await f.read(read_size)
            if not data:
                break
            remaining -= len(data)
            yield data


@router.get("/{video_id}/stream")
async def stream_video(video_id: int, request: Request, db=Depends(get_db)):
    cursor = await db.execute(
        """SELECT storage_path, playback_path, mime_type, resolution, codec,
           sample_aspect_ratio, display_aspect_ratio FROM videos WHERE id = ?""",
        (video_id,),
    )
    row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="视频不存在")

    storage_path = row["storage_path"]
    file_path = storage_path
    mime_type = row["mime_type"]

    if not os.path.exists(storage_path):
        raise HTTPException(status_code=404, detail="视频文件不存在")

    playback_path = row["playback_path"]
    if playback_path and os.path.exists(playback_path):
        file_path = playback_path
        mime_type = "video/mp4"
    else:
        metadata = None
        sample_aspect_ratio = row["sample_aspect_ratio"] or ""

        # 老数据补齐元信息
        if not sample_aspect_ratio or not row["display_aspect_ratio"] or not row["resolution"] or not row["codec"]:
            metadata = probe_video(storage_path)
            sample_aspect_ratio = metadata["sample_aspect_ratio"]
            await db.execute(
                """UPDATE videos
                   SET resolution = ?, codec = ?, sample_aspect_ratio = ?, display_aspect_ratio = ?
                   WHERE id = ?""",
                (
                    metadata["resolution"],
                    metadata["codec"],
                    metadata["sample_aspect_ratio"],
                    metadata["display_aspect_ratio"],
                    video_id,
                ),
            )
            await db.commit()

        # 针对非方形像素视频生成兼容播放副本，修复浏览器纵向拉伸
        if has_non_square_pixels(sample_aspect_ratio):
            new_playback_path = generate_playback_video(storage_path, video_id)
            if new_playback_path and os.path.exists(new_playback_path):
                await db.execute(
                    "UPDATE videos SET playback_path = ? WHERE id = ?",
                    (new_playback_path, video_id),
                )
                await db.commit()
                file_path = new_playback_path
                mime_type = "video/mp4"

    file_size = os.path.getsize(file_path)
    range_header = request.headers.get("range")

    if range_header:
        # 解析 Range: bytes=start-end
        range_spec = range_header.replace("bytes=", "")
        parts = range_spec.split("-")
        start = int(parts[0]) if parts[0] else 0
        end = int(parts[1]) if parts[1] else file_size - 1
        end = min(end, file_size - 1)

        return StreamingResponse(
            file_iterator(file_path, start, end),
            status_code=206,
            headers={
                "Content-Range": f"bytes {start}-{end}/{file_size}",
                "Content-Length": str(end - start + 1),
                "Accept-Ranges": "bytes",
            },
            media_type=mime_type,
        )

    return StreamingResponse(
        file_iterator(file_path, 0, file_size - 1),
        media_type=mime_type,
        headers={
            "Accept-Ranges": "bytes",
            "Content-Length": str(file_size),
        },
    )


# ==================== #11 视频下载 ====================

@router.get("/{video_id}/download")
async def download_video(video_id: int, request: Request, db=Depends(get_db)):
    cursor = await db.execute(
        "SELECT storage_path, mime_type, filename, file_size FROM videos WHERE id = ?",
        (video_id,),
    )
    row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="视频不存在")

    file_path = row["storage_path"]
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="视频文件不存在")

    filename = row["filename"]
    file_size = os.path.getsize(file_path)
    mime_type = row["mime_type"]
    range_header = request.headers.get("range")

    headers = {
        "Accept-Ranges": "bytes",
        "Content-Disposition": f'attachment; filename="{filename}"',
    }

    if range_header:
        range_spec = range_header.replace("bytes=", "")
        parts = range_spec.split("-")
        start = int(parts[0]) if parts[0] else 0
        end = int(parts[1]) if parts[1] else file_size - 1
        end = min(end, file_size - 1)
        headers["Content-Range"] = f"bytes {start}-{end}/{file_size}"
        headers["Content-Length"] = str(end - start + 1)

        return StreamingResponse(
            file_iterator(file_path, start, end),
            status_code=206,
            headers=headers,
            media_type=mime_type,
        )

    headers["Content-Length"] = str(file_size)
    return StreamingResponse(
        file_iterator(file_path, 0, file_size - 1),
        headers=headers,
        media_type=mime_type,
    )


# ==================== #12 视频删除 ====================

@router.delete("/{video_id}")
async def delete_video(video_id: int, db=Depends(get_db)):
    cursor = await db.execute(
        "SELECT storage_path, playback_path, thumbnail_path FROM videos WHERE id = ?",
        (video_id,),
    )
    row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="视频不存在")

    # 删除文件（忽略不存在的情况）
    for path in [row["storage_path"], row["playback_path"], row["thumbnail_path"]]:
        if path:
            try:
                os.remove(path)
            except OSError:
                pass

    await db.execute("DELETE FROM videos WHERE id = ?", (video_id,))
    await db.commit()

    return {"message": "删除成功"}


# ==================== #13 缩略图 ====================

@router.get("/{video_id}/thumbnail")
async def get_thumbnail(video_id: int, db=Depends(get_db)):
    cursor = await db.execute(
        "SELECT thumbnail_path FROM videos WHERE id = ?",
        (video_id,),
    )
    row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="视频不存在")

    thumb_path = row["thumbnail_path"]
    if thumb_path and os.path.exists(thumb_path):
        return FileResponse(thumb_path, media_type="image/jpeg")

    # 返回占位图
    if PLACEHOLDER_THUMB.exists():
        return FileResponse(str(PLACEHOLDER_THUMB), media_type="image/jpeg")

    raise HTTPException(status_code=404, detail="缩略图不存在")


# ==================== #14 分片上传 ====================

@router.post("/upload/chunk")
async def upload_chunk(
    file: UploadFile = File(...),
    uploadId: str = Form(...),
    chunkIndex: int = Form(...),
    totalChunks: int = Form(...),
    filename: str = Form(...),
):
    chunk_dir = CHUNKS_DIR / uploadId
    chunk_dir.mkdir(parents=True, exist_ok=True)

    chunk_path = chunk_dir / str(chunkIndex)
    async with aiofiles.open(str(chunk_path), "wb") as f:
        while data := await file.read(1024 * 1024):
            await f.write(data)

    return {"chunkIndex": chunkIndex, "uploaded": True}


@router.post("/upload/merge", status_code=201)
async def merge_chunks(
    data: dict,
    db=Depends(get_db),
):
    upload_id = data["uploadId"]
    filename = data["filename"]
    total_chunks = data["totalChunks"]
    title = data.get("title") or Path(filename).stem

    chunk_dir = CHUNKS_DIR / upload_id

    # 验证所有分片存在
    for i in range(total_chunks):
        if not (chunk_dir / str(i)).exists():
            raise HTTPException(status_code=400, detail=f"缺少分片 {i}")

    # 合并分片
    storage_filename = f"{int(time.time())}_{filename}"
    storage_path = str(VIDEOS_DIR / storage_filename)

    file_size = 0
    async with aiofiles.open(storage_path, "wb") as out:
        for i in range(total_chunks):
            chunk_path = str(chunk_dir / str(i))
            async with aiofiles.open(chunk_path, "rb") as chunk_file:
                while block := await chunk_file.read(1024 * 1024):
                    await out.write(block)
                    file_size += len(block)

    # 校验文件类型（通过扩展名推断 MIME）
    import mimetypes
    mime_type, _ = mimetypes.guess_type(filename)
    if not mime_type:
        mime_type = "video/mp4"
    validate_video_file(filename, mime_type)

    # 探测元信息
    metadata = probe_video(storage_path)

    # 写入数据库
    cursor = await db.execute(
        """INSERT INTO videos (title, filename, storage_path, mime_type, file_size,
           duration, resolution, sample_aspect_ratio, display_aspect_ratio, codec)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (title, filename, storage_path, mime_type, file_size,
         metadata["duration"], metadata["resolution"], metadata["sample_aspect_ratio"],
         metadata["display_aspect_ratio"], metadata["codec"]),
    )
    await db.commit()
    video_id = cursor.lastrowid

    # 生成方形像素播放副本（仅针对非 1:1 像素宽高比）
    if has_non_square_pixels(metadata["sample_aspect_ratio"]):
        playback_path = generate_playback_video(storage_path, video_id)
        if playback_path:
            await db.execute(
                "UPDATE videos SET playback_path = ? WHERE id = ?",
                (playback_path, video_id),
            )
            await db.commit()

    # 生成缩略图
    thumb_path = generate_thumbnail(storage_path, video_id)
    if thumb_path:
        await db.execute(
            "UPDATE videos SET thumbnail_path = ? WHERE id = ?",
            (thumb_path, video_id),
        )
        await db.commit()

    # 清理分片
    shutil.rmtree(str(chunk_dir), ignore_errors=True)

    # 返回完整记录
    cursor = await db.execute("SELECT * FROM videos WHERE id = ?", (video_id,))
    row = await cursor.fetchone()
    item = dict(row)
    item["thumbnail_path"] = f"/api/videos/{video_id}/thumbnail"
    return item
