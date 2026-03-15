# VideoHub 视频预编码脚本

在上传视频到 VideoHub 之前，使用此脚本将视频转为浏览器友好的标准格式（H.264 + AAC 的 MP4），可以**跳过服务器端的二次编码**，节省服务器资源。

## 特性

- ✅ **跨平台**：支持 Windows、Linux、macOS
- ✅ **批量处理**：支持单个文件或整个文件夹
- ✅ **智能跳过**：自动检测已是 H.264+AAC 格式的视频，跳过处理
- ✅ **硬件加速**：支持 NVIDIA GPU (h264_nvenc) 加速编码
- ✅ **进度显示**：实时显示处理进度

## 安装要求

### 1. 安装 FFmpeg

脚本依赖 FFmpeg，请先安装：

**Windows:**
```powershell
# 使用 chocolatey
choco install ffmpeg

# 或使用 scoop
scoop install ffmpeg
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install ffmpeg
```

**Linux (CentOS/RHEL):**
```bash
sudo yum install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

验证安装：
```bash
ffmpeg -version
```

### 2. 可选：安装 NVIDIA GPU 驱动（如需硬件加速）

Windows/Linux 安装 NVIDIA 显卡驱动和 CUDA Toolkit 后，可使用 `h264_nvenc` 编码器大幅加速。

## 使用方法

### 基本用法

```bash
# 处理单个视频
python pre_encode.py video.mp4

# 处理整个文件夹（批量）
python pre_encode.py /path/to/videos/

# 强制重新编码（即使已是友好格式）
python pre_encode.py video.mp4 --force
```

### 高级用法

```bash
# 调整质量（CRF 值越小质量越好，18-28 范围，默认 23）
python pre_encode.py video.mp4 --crf 20

# 调整编码速度预设（影响速度 vs 压缩率）
# 可选: ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow
python pre_encode.py video.mp4 --preset medium

# 使用 NVIDIA GPU 硬件加速编码
python pre_encode.py video.mp4 --vcodec h264_nvenc

# 批量处理并使用高质量设置
python pre_encode.py /path/to/videos/ --crf 18 --preset slow --vcodec h264_nvenc
```

## 输出文件

脚本会在原文件所在目录生成编码后的文件：

```
input_video.mp4 -> input_video_encoded.mp4
```

上传时选择 `*_encoded.mp4` 文件即可。

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--crf` | 视频质量系数（18-28，越小质量越好） | 23 |
| `--preset` | 编码速度预设 | superfast |
| `--vcodec` | 视频编码器（libx264/h264_nvenc 等） | libx264 |
| `--force` | 强制重新编码，即使已是友好格式 | False |

## 常见问题

### Q: 脚本提示 "未检测到 FFmpeg"
确保 FFmpeg 已安装并添加到系统 PATH。在终端运行 `ffmpeg -version` 验证。

### Q: 编码速度很慢
- 使用更快的 preset：`--preset ultrafast`
- 使用 GPU 加速：`--vcodec h264_nvenc`（需 NVIDIA 显卡）
- 降低质量要求：`--crf 28`

### Q: 输出文件比原文件还大
这是正常的，特别是原视频已经是高压缩格式时。预编码的目的是**浏览器兼容性**，不是压缩文件大小。

### Q: 可以跳过已编码的视频吗？
可以！脚本会自动检测已是 H.264+AAC 格式的视频并跳过。使用 `--force` 可强制重新编码。

## 许可证

与 VideoHub 项目保持一致。

## 更新日志

- **v1.0** (2026-03-16): 初始版本，支持跨平台批量预编码
