#!/usr/bin/env python3
"""
视频预编码脚本
在上传到 VideoHub 之前，将视频统一转码为浏览器友好的格式（H.264 + AAC 的 MP4）

支持平台：Windows / Linux / macOS
需要安装 FFmpeg 并添加到 PATH

用法：
    python pre_encode.py input_video.mp4
    python pre_encode.py /path/to/video_folder/        # 批量处理
    python pre_encode.py input.mp4 --crf 23 --preset medium

输出文件：
    input_video.mp4 -> input_video_encoded.mp4
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Optional, Tuple


def check_ffmpeg() -> bool:
    """检查 FFmpeg 是否已安装并可用"""
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def get_video_info(video_path: Path) -> Optional[dict]:
    """获取视频信息：视频编码、音频编码、时长"""
    try:
        # 使用 ffprobe 获取编码信息
        cmd = [
            "ffprobe",
            "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=codec_name",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(video_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        video_codec = result.stdout.strip()

        # 获取音频编码
        cmd = [
            "ffprobe",
            "-v", "error",
            "-select_streams", "a:0",
            "-show_entries", "stream=codec_name",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(video_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        audio_codec = result.stdout.strip()

        # 获取时长
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(video_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        duration = float(result.stdout.strip()) if result.stdout.strip() else 0

        return {
            "video_codec": video_codec.lower(),
            "audio_codec": audio_codec.lower() if audio_codec else None,
            "duration": duration
        }
    except Exception:
        return None


def is_browser_friendly(info: dict) -> bool:
    """检查视频是否已经是浏览器友好的格式"""
    if not info:
        return False
    
    # 视频必须是 H.264
    if info["video_codec"] not in ["h264", "libx264", "avc1", "h.264"]:
        return False
    
    # 音频必须是 AAC 或没有音频
    if info["audio_codec"] and info["audio_codec"] not in ["aac", "mp4a", "libfdk_aac"]:
        return False
    
    return True


def encode_video(
    input_path: Path,
    output_path: Path,
    crf: int = 23,
    preset: str = "superfast",
    video_codec: str = "libx264"
) -> bool:
    """
    使用 FFmpeg 转码视频为 H.264 + AAC 的 MP4
    
    Args:
        input_path: 输入视频路径
        output_path: 输出视频路径
        crf: 质量系数，越小质量越好（18-28 范围）
        preset: 编码速度预设，影响编码速度vs压缩率
        video_codec: 视频编码器
    """
    cmd = [
        "ffmpeg",
        "-i", str(input_path),           # 输入文件
        "-vcodec", video_codec,          # 视频编码器：libx264
        "-acodec", "aac",                # 音频编码器：AAC
        "-pix_fmt", "yuv420p",           # 像素格式（兼容性最好）
        "-movflags", "+faststart",       # 优化流式播放
        "-crf", str(crf),                # 质量系数
        "-preset", preset,               # 速度预设
        "-y",                            # 覆盖输出文件
        str(output_path)
    ]
    
    print(f"执行: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.DEVNULL,      # 不显示标准输出
            stderr=subprocess.STDOUT,       # 错误输出重定向
            timeout=3600                    # 1小时超时
        )
        return True
    except subprocess.TimeoutExpired:
        print(f"错误: 编码超时（超过1小时）")
        return False
    except subprocess.CalledProcessError as e:
        print(f"错误: FFmpeg 返回错误码 {e.returncode}")
        return False


def process_video(input_path: Path, args) -> Tuple[bool, str]:
    """处理单个视频：检查 -> 编码 -> 输出"""
    
    # 检查是否已经是浏览器友好格式
    info = get_video_info(input_path)
    if info and is_browser_friendly(info):
        print(f"跳过（已是友好格式）: {input_path}")
        print(f"  视频编码: {info['video_codec']}, 音频编码: {info['audio_codec']}")
        return True, "skipped"
    
    # 生成输出路径
    output_path = input_path.parent / f"{input_path.stem}_encoded{input_path.suffix}"
    
    # 检查输出文件是否已存在
    if output_path.exists() and not args.force:
        print(f"跳过（输出文件已存在，使用 --force 覆盖）: {output_path}")
        return True, "exists"
    
    # 执行编码
    print(f"\n开始编码: {input_path}")
    if info:
        duration_min = info.get('duration', 0) / 60
        print(f"  原视频信息: {info['video_codec']}/{info['audio_codec']}, 时长: {duration_min:.1f}分钟")
    
    success = encode_video(
        input_path,
        output_path,
        crf=args.crf,
        preset=args.preset,
        video_codec=args.vcodec
    )
    
    if success:
        print(f"完成: {output_path}")
        # 显示文件大小对比
        input_size = input_path.stat().st_size / (1024*1024)
        output_size = output_path.stat().st_size / (1024*1024)
        print(f"  大小: {input_size:.1f}MB -> {output_size:.1f}MB ({output_size/input_size*100:.1f}%)")
        return True, "encoded"
    else:
        print(f"失败: {input_path}")
        return False, "failed"


def main():
    parser = argparse.ArgumentParser(
        description="视频预编码脚本 - 将视频转为浏览器友好的 H.264+AAC 格式",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python pre_encode.py video.mp4
  python pre_encode.py /path/to/videos/ --crf 20 --preset slow
  python pre_encode.py *.mp4 --vcodec libx264 --force
        """
    )
    
    parser.add_argument(
        "input",
        help="输入视频文件或包含视频的文件夹"
    )
    
    parser.add_argument(
        "--crf",
        type=int,
        default=23,
        help="视频质量系数 (18-28, 越小质量越好)，默认 23"
    )
    
    parser.add_argument(
        "--preset",
        default="superfast",
        choices=["ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower", "veryslow"],
        help="编码速度预设，默认 superfast（速度快/压缩率低）"
    )
    
    parser.add_argument(
        "--vcodec",
        default="libx264",
        help="视频编码器，默认 libx264。可指定 h264_nvenc（NVIDIA GPU）等"
    )
    
    parser.add_argument(
        "--force",
        action="store_true",
        help="强制重新编码（即使输出文件已存在）"
    )
    
    parser.add_argument(
        "--skip-friendly",
        action="store_true",
        default=True,
        help="跳过已经是浏览器友好格式的视频（默认启用）"
    )
    
    args = parser.parse_args()
    
    # 检查 FFmpeg
    if not check_ffmpeg():
        print("错误: 未检测到 FFmpeg，请先安装 FFmpeg 并添加到 PATH")
        print("安装指南: https://ffmpeg.org/download.html")
        sys.exit(1)
    
    # 解析输入路径
    input_path = Path(args.input)
    
    if not input_path.exists():
        print(f"错误: 输入路径不存在: {input_path}")
        sys.exit(1)
    
    # 收集要处理的视频文件
    video_extensions = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.ts', '.mts'}
    
    if input_path.is_file():
        if input_path.suffix.lower() in video_extensions:
            video_files = [input_path]
        else:
            print(f"错误: 不支持的文件格式: {input_path.suffix}")
            sys.exit(1)
    else:
        # 遍历文件夹中的所有视频文件
        video_files = [
            f for f in input_path.rglob("*")
            if f.is_file() and f.suffix.lower() in video_extensions
        ]
        print(f"在 {input_path} 中找到 {len(video_files)} 个视频文件")
    
    if not video_files:
        print("没有找到需要处理的视频文件")
        sys.exit(0)
    
    # 处理所有视频
    print(f"\n开始处理 {len(video_files)} 个视频...")
    print(f"设置: CRF={args.crf}, Preset={args.preset}, 编码器={args.vcodec}\n")
    
    success_count = 0
    skip_count = 0
    fail_count = 0
    
    for i, video_file in enumerate(video_files, 1):
        print(f"\n[{i}/{len(video_files)}] ", end="")
        success, status = process_video(video_file, args)
        
        if status == "encoded":
            success_count += 1
        elif status == "skipped":
            skip_count += 1
        else:
            fail_count += 1
    
    # 总结
    print(f"\n\n{'='*50}")
    print("处理完成!")
    print(f"  成功编码: {success_count} 个")
    print(f"  已跳过(已是友好格式): {skip_count} 个")
    print(f"  失败: {fail_count} 个")
    print(f"{'='*50}\n")
    
    if fail_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
