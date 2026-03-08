import ffmpeg
from pathlib import Path

THUMBS_DIR = Path("/mnt/mydisk/video-site/thumbs")


def probe_video(file_path: str) -> dict:
    """调用 ffprobe 返回视频元信息 { duration, resolution, codec }"""
    try:
        probe = ffmpeg.probe(file_path)
    except ffmpeg.Error:
        return {"duration": 0, "resolution": "", "codec": ""}

    video_stream = next(
        (s for s in probe.get("streams", []) if s.get("codec_type") == "video"),
        None,
    )
    if not video_stream:
        return {
            "duration": float(probe.get("format", {}).get("duration", 0)),
            "resolution": "",
            "codec": "",
        }

    return {
        "duration": float(probe.get("format", {}).get("duration", 0)),
        "resolution": f"{video_stream['width']}x{video_stream['height']}",
        "codec": video_stream.get("codec_name", ""),
    }


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
