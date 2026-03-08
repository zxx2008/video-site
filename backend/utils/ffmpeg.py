import math
from pathlib import Path
from typing import Optional

import ffmpeg

THUMBS_DIR = Path("/mnt/mydisk/video-site/thumbs")
PLAYBACK_DIR = Path("/mnt/mydisk/video-site/playback")

BROWSER_FRIENDLY_CODECS = {"h264"}


def _parse_ratio(value: str) -> Optional[tuple[int, int]]:
    if not value or value in {"N/A", "0:1"}:
        return None

    try:
        num_str, den_str = value.split(":", 1)
        num = int(num_str)
        den = int(den_str)
    except (ValueError, AttributeError):
        return None

    if num <= 0 or den <= 0:
        return None

    return num, den


def _normalize_rotation(value) -> int:
    try:
        normalized = int(round(float(value))) % 360
    except (TypeError, ValueError):
        return 0

    if normalized in {90, 180, 270}:
        return normalized
    return 0


def parse_rotation(video_stream: dict) -> int:
    """从 ffprobe 视频流中提取旋转角度"""
    for side_data in video_stream.get("side_data_list", []):
        if "rotation" in side_data:
            return _normalize_rotation(side_data.get("rotation"))

    tags = video_stream.get("tags", {}) or {}
    return _normalize_rotation(tags.get("rotate"))


def compute_display_geometry(
    width: Optional[int],
    height: Optional[int],
    sample_aspect_ratio: str,
    rotation: int,
) -> tuple[int, int, str]:
    """计算最终显示宽高与显示比例"""
    if not width or not height:
        return 0, 0, ""

    sar = _parse_ratio(sample_aspect_ratio) or (1, 1)
    sar_num, sar_den = sar

    display_width = round(width * sar_num / sar_den)
    display_height = round(height)

    if rotation in {90, 270}:
        display_width, display_height = display_height, display_width

    if display_width <= 0 or display_height <= 0:
        return 0, 0, ""

    divisor = math.gcd(display_width, display_height)
    aspect_ratio = f"{display_width // divisor}:{display_height // divisor}"
    return display_width, display_height, aspect_ratio


def probe_video(file_path: str) -> dict:
    """调用 ffprobe 返回视频元信息"""
    try:
        probe = ffmpeg.probe(file_path)
    except ffmpeg.Error:
        return {
            "duration": 0,
            "resolution": "",
            "codec": "",
            "sample_aspect_ratio": "",
            "display_aspect_ratio": "",
            "rotation": 0,
            "display_width": 0,
            "display_height": 0,
            "final_display_aspect_ratio": "",
            "needs_normalization": False,
        }

    video_stream = next(
        (s for s in probe.get("streams", []) if s.get("codec_type") == "video"),
        None,
    )
    if not video_stream:
        return {
            "duration": float(probe.get("format", {}).get("duration", 0)),
            "resolution": "",
            "codec": "",
            "sample_aspect_ratio": "",
            "display_aspect_ratio": "",
            "rotation": 0,
            "display_width": 0,
            "display_height": 0,
            "final_display_aspect_ratio": "",
            "needs_normalization": False,
        }

    width = video_stream.get("width")
    height = video_stream.get("height")
    resolution = f"{width}x{height}" if width and height else ""
    sample_aspect_ratio = video_stream.get("sample_aspect_ratio", "")
    display_aspect_ratio = video_stream.get("display_aspect_ratio", "")
    codec = video_stream.get("codec_name", "")
    rotation = parse_rotation(video_stream)
    display_width, display_height, final_display_aspect_ratio = compute_display_geometry(
        width,
        height,
        sample_aspect_ratio,
        rotation,
    )

    metadata = {
        "duration": float(probe.get("format", {}).get("duration", 0)),
        "resolution": resolution,
        "codec": codec,
        "sample_aspect_ratio": sample_aspect_ratio,
        "display_aspect_ratio": display_aspect_ratio,
        "rotation": rotation,
        "display_width": display_width,
        "display_height": display_height,
        "final_display_aspect_ratio": final_display_aspect_ratio,
    }
    metadata["needs_normalization"] = needs_playback_normalization(metadata)
    return metadata


def has_non_square_pixels(sample_aspect_ratio: str) -> bool:
    """判断像素宽高比是否为非 1:1"""
    ratio = _parse_ratio(sample_aspect_ratio)
    if not ratio:
        return False
    num, den = ratio
    return num != den


def needs_playback_normalization(metadata: dict) -> bool:
    """判断是否需要转成兼容播放副本"""
    if has_non_square_pixels(metadata.get("sample_aspect_ratio", "")):
        return True

    if _normalize_rotation(metadata.get("rotation", 0)) != 0:
        return True

    codec = (metadata.get("codec") or "").lower()
    if codec and codec not in BROWSER_FRIENDLY_CODECS:
        return True

    return False


def generate_playback_video(video_path: str, video_id: int) -> str:
    """生成方形像素播放副本，返回副本路径"""
    PLAYBACK_DIR.mkdir(parents=True, exist_ok=True)
    playback_path = str(PLAYBACK_DIR / f"{video_id}.mp4")

    # ffmpeg 默认会按源文件旋转元信息自动旋转画面并写入新帧尺寸
    vf_chain = "scale=trunc(iw*sar/2)*2:trunc(ih/2)*2,setsar=1"

    try:
        (
            ffmpeg
            .input(video_path)
            .output(
                playback_path,
                vf=vf_chain,
                vcodec="libx264",
                acodec="aac",
                pix_fmt="yuv420p",
                movflags="+faststart",
                crf=22,
                preset="veryfast",
            )
            .overwrite_output()
            .run(quiet=True)
        )
    except ffmpeg.Error:
        return ""

    return playback_path


def generate_thumbnail(video_path: str, video_id: int) -> str:
    """截取视频画面生成缩略图，返回缩略图路径"""
    thumbnail_path = str(THUMBS_DIR / f"{video_id}.jpg")

    # 先尝试 ss=1（第1秒），失败则 ss=0
    for ss in [1, 0]:
        try:
            (
                ffmpeg
                .input(video_path, ss=ss)
                .filter("scale", 320, -1)
                .output(thumbnail_path, vframes=1)
                .overwrite_output()
                .run(quiet=True)
            )
            return thumbnail_path
        except ffmpeg.Error:
            if ss == 0:
                return ""
            continue

    return ""
