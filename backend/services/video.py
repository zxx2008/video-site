from fastapi import HTTPException

# 允许的 MIME 类型
ALLOWED_MIME_TYPES = {
    "video/mp4",
    "video/x-matroska",
    "video/avi",
    "video/x-msvideo",
    "video/quicktime",
    "video/x-ms-wmv",
    "video/x-flv",
    "video/webm",
}

# 允许的扩展名
ALLOWED_EXTENSIONS = {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm"}


def validate_video_file(filename: str, content_type: str):
    """校验文件类型：MIME 和扩展名必须同时匹配"""
    if not filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")

    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="不支持的文件类型")

    if content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail="不支持的文件类型")
