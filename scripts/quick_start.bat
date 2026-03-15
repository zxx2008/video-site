@echo off
chcp 65001 >nul
title VideoHub 视频预编码工具

echo ===================================
echo VideoHub 视频预编码工具
echo ===================================
echo.

:: 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python
    echo.
    echo 请先安装 Python 3.7 或更高版本：
    echo https://www.python.org/downloads/
    echo.
    echo 安装时请勾选 "Add Python to PATH"
    pause
    exit /b 1
)

echo [OK] Python 已安装

:: 检查 FFmpeg
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo.
    echo [错误] 未找到 FFmpeg
    echo.
    echo 请按以下步骤安装 FFmpeg：
    echo.
    echo 方法 1 - 使用 winget（推荐）：
    echo   winget install Gyan.FFmpeg
    echo.
    echo 方法 2 - 手动下载：
    echo   1. 访问 https://github.com/BtbN/FFmpeg-Builds/releases
    echo   2. 下载 ffmpeg-master-latest-win64-gpl.zip
    echo   3. 解压到 C:\ffmpeg
    echo   4. 将 C:\ffmpeg\bin 添加到系统 PATH
    echo.
    echo 安装完成后重新运行此脚本
    pause
    exit /b 1
)

echo [OK] FFmpeg 已安装

:: 显示版本信息
for /f "tokens=*" %%a in ('ffmpeg -version ^| findstr "ffmpeg version"') do (
    echo FFmpeg 版本: %%a
)

:: 检查硬件加速
echo.
echo 检查硬件加速支持...
ffmpeg -encoders 2>nul | findstr "h264_nvenc" >nul
if not errorlevel 1 echo   [OK] NVIDIA GPU 加速可用 (h264_nvenc)

ffmpeg -encoders 2>nul | findstr "h264_qsv" >nul
if not errorlevel 1 echo   [OK] Intel QuickSync 可用 (h264_qsv)

ffmpeg -encoders 2>nul | findstr "h264_amf" >nul
if not errorlevel 1 echo   [OK] AMD 硬件编码可用 (h264_amf)

echo.
echo ===================================
echo 环境检查通过！
echo ===================================
echo.
echo 使用示例：
echo.
echo 1. 处理单个视频：
echo    python pre_encode.py my_video.mp4
echo.
echo 2. 批量处理文件夹：
echo    python pre_encode.py C:\Users\YourName\Videos\
echo.
echo 3. 使用 NVIDIA GPU 加速：
echo    python pre_encode.py video.mp4 --vcodec h264_nvenc
echo.
echo 4. 调整质量和速度：
echo    python pre_encode.py video.mp4 --crf 20 --preset slow
echo.
echo 详细说明请查看 README.md
echo.

pause
