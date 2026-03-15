#!/bin/bash
# VideoHub 预编码脚本 - Linux/macOS 快速开始

echo "==================================="
echo "VideoHub 视频预编码工具"
echo "==================================="
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 Python3"
    echo "请先安装 Python 3.7 或更高版本"
    echo "https://www.python.org/downloads/"
    exit 1
fi

echo "✓ Python 已安装"

# 检查 FFmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo ""
    echo "❌ 错误: 未找到 FFmpeg"
    echo ""
    echo "请按以下步骤安装 FFmpeg:"
    echo ""
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "Ubuntu/Debian:"
        echo "  sudo apt update"
        echo "  sudo apt install ffmpeg"
        echo ""
        echo "CentOS/RHEL:"
        echo "  sudo yum install ffmpeg"
        
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macOS (使用 Homebrew):"
        echo "  brew install ffmpeg"
        echo ""
        echo "如果没有 Homebrew，先安装:"
        echo '  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
    fi
    
    echo ""
    echo "安装完成后重新运行此脚本"
    exit 1
fi

echo "✓ FFmpeg 已安装"
echo ""

# 显示 FFmpeg 版本
FFMPEG_VERSION=$(ffmpeg -version | head -n1 | cut -d' ' -f3)
echo "FFmpeg 版本: $FFMPEG_VERSION"
echo ""

# 检查是否有硬件加速支持
echo "检查硬件加速支持..."
if ffmpeg -encoders 2>/dev/null | grep -q "h264_nvenc"; then
    echo "  ✓ NVIDIA GPU 加速可用 (h264_nvenc)"
fi
if ffmpeg -encoders 2>/dev/null | grep -q "h264_videotoolbox"; then
    echo "  ✓ macOS VideoToolbox 可用 (h264_videotoolbox)"
fi
if ffmpeg -encoders 2>/dev/null | grep -q "h264_v4l2m2m"; then
    echo "  ✓ V4L2 硬件编码可用 (h264_v4l2m2m)"
fi
echo ""

echo "==================================="
echo "环境检查通过！"
echo "==================================="
echo ""
echo "使用示例:"
echo ""
echo "1. 处理单个视频:"
echo "   python3 pre_encode.py my_video.mp4"
echo ""
echo "2. 批量处理文件夹:"
echo "   python3 pre_encode.py /path/to/videos/"
echo ""
echo "3. 使用 NVIDIA GPU 加速:"
echo "   python3 pre_encode.py video.mp4 --vcodec h264_nvenc"
echo ""
echo "4. 调整质量和速度:"
echo "   python3 pre_encode.py video.mp4 --crf 20 --preset slow"
echo ""
echo "详细说明请查看 README.md"
echo ""
