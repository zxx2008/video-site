import ffmpeg
from pathlib import Path

THUMBS_DIR = Path("/mnt/mydisk/video-site/thumbs")
PLAYBACK_DIR = Path("/mnt/mydisk/video-site/playback")


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
        }

    width = video_stream.get("width")
    height = video_stream.get("height")
    resolution = f"{width}x{height}" if width and height else ""

    return {
        "duration": float(probe.get("format", {}).get("duration", 0)),
        "resolution": resolution,
        "codec": video_stream.get("codec_name", ""),
        "sample_aspect_ratio": video_stream.get("sample_aspect_ratio", ""),
        "display_aspect_ratio": video_stream.get("display_aspect_ratio", ""),
    }


def has_non_square_pixels(sample_aspect_ratio: str) -> bool:
    """判断像素宽高比是否为非 1:1"""
    if not sample_aspect_ratio or sample_aspect_ratio in {"0:1", "N/A"}:
        return False

    try:
        num_str, den_str = sample_aspect_ratio.split(":", 1)
        num = int(num_str)
        den = int(den_str)
    except (ValueError, AttributeError):
        return False

    if den == 0:
        return False

    return num != den


def generate_playback_video(video_path: str, video_id: int) -> str:
    """生成方形像素播放副本，返回副本路径"""
    PLAYBACK_DIR.mkdir(parents=True, exist_ok=True)
    playback_path = str(PLAYBACK_DIR / f"{video_id}.mp4")

    try:
        (
            ffmpeg
            .input(video_path)
            .output(
                playback_path,
                vf="scale=trunc(iw*sar/2)*2:trunc(ih/2)*2,setsar=1",
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
