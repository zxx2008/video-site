# VideoHub 树莓派5部署调试计划

> 基于实际配置：数据目录 `/mnt/mydisk/video-site`，使用阿里云镜像源
> 创建日期：2026-03-08
> 适用环境：Raspberry Pi 5 (ARM64)，Raspberry Pi OS 64-bit

## 一、配置概览

### 关键配置变更
| 配置项 | 原始值 | 修改后值 | 说明 |
|--------|--------|----------|------|
| 数据目录 | `data/` | `/mnt/mydisk/video-site/` | 外接存储路径 |
| Python包版本 | `>=` 宽松版本 | `==` 精确版本 | 加速安装，确保兼容性 |
| PyPI镜像 | 官方源 | `http://mirrors.aliyun.com/pypi/simple/` | 国内加速 |
| npm镜像 | 官方源 | `https://registry.npmmirror.com` | 国内加速 |

### 已修改文件清单
1. `backend/main.py:15` - `DATA_DIR = Path("/mnt/mydisk/video-site")`
2. `backend/routers/videos.py:15-18` - `DATA_DIR = Path("/mnt/mydisk/video-site")`
3. `backend/utils/ffmpeg.py:4` - `THUMBS_DIR = Path("/mnt/mydisk/video-site/thumbs")`
4. `backend/db/database.py:5` - `DB_PATH = Path("/mnt/mydisk/video-site/videohub.db")`
5. `backend/requirements.txt` - 固定版本 + 阿里云镜像说明

## 二、部署调试计划

### 📋 阶段一：环境准备与验证（1-2小时）
1. **树莓派系统检查**
   - [ ] 确认Raspberry Pi OS 64-bit已安装
   - [ ] 验证Python版本 ≥ 3.11：`python3 --version`
   - [ ] 检查FFmpeg安装：`ffmpeg -version`
   - [ ] 确认存储设备挂载：`lsblk`，确认`/mnt/mydisk`存在

2. **网络与权限配置**
   - [ ] 设置静态IP（可选）
   - [ ] 验证SSH连接
   - [ ] 确保用户对`/mnt/mydisk`有读写权限

### 📦 阶段二：代码传输与结构验证（30分钟）
1. **传输项目代码**
   ```bash
   # 在开发机上执行
   rsync -avz --exclude 'node_modules' --exclude 'venv' --exclude 'data' \
     /path/to/video-site/ pi@<树莓派IP>:~/video-site/
   ```

2. **路径配置验证**
   - [ ] 检查所有硬编码路径已从`data/`改为`/mnt/mydisk/video-site/`
   - [ ] 验证目录结构：`ls -la /mnt/mydisk/video-site/`

### 🔧 阶段三：依赖安装与配置（1-2小时）
1. **Python环境搭建**
   ```bash
   cd ~/video-site/backend
   python3 -m venv venv
   source venv/bin/activate
   pip install -i http://mirrors.aliyun.com/pypi/simple/ -r requirements.txt
   ```

2. **前端构建选项**
   - **选项A（树莓派构建）**: 安装Node.js 20+后执行 `npm install --registry=https://registry.npmmirror.com` 和 `npm run build`
   - **选项B（交叉构建）**: 在开发机构建后传输 `dist/` 目录

### 💾 阶段四：存储配置（30分钟）
1. **创建数据目录结构**
   ```bash
   sudo mkdir -p /mnt/mydisk/video-site/{videos,thumbs,chunks}
   sudo chown -R $(whoami):$(whoami) /mnt/mydisk/video-site
   ```

### 🚀 阶段五：服务启动与测试（1小时）
1. **后端服务验证**
   ```bash
   cd ~/video-site/backend
   source venv/bin/activate
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```
   
2. **功能测试清单**
   - [ ] API端点：`http://<树莓派IP>:8000/docs`
   - [ ] 前端页面：`http://<树莓派IP>:8000`
   - [ ] 视频上传（小文件 < 100MB）
   - [ ] 分块上传（大文件 ≥ 100MB）
   - [ ] 视频播放（HTTP Range支持）
   - [ ] 缩略图自动生成

### ⚙️ 阶段六：生产化部署（1小时）
1. **Systemd服务配置**
   ```bash
   sudo tee /etc/systemd/system/videohub.service << 'EOF'
   [Unit]
   Description=VideoHub Video Management Service
   After=network.target
   
   [Service]
   Type=simple
   User=<你的用户名>
   WorkingDirectory=/home/<你的用户名>/video-site/backend
   Environment="PATH=/home/<你的用户名>/video-site/backend/venv/bin:/usr/bin:/bin"
   ExecStart=/home/<你的用户名>/video-site/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
   Restart=always
   RestartSec=5
   
   [Install]
   WantedBy=multi-user.target
   EOF
   ```

### 🌐 阶段七：Nginx配置（可选，30分钟）
1. **反向代理设置**（如需要80端口访问）
   ```nginx
   # /etc/nginx/sites-available/videohub
   server {
       listen 80;
       server_name _;
       
       root /home/pi/video-site/frontend/dist;
       index index.html;
       
       client_max_body_size 2G;
       
       location /api/ {
           proxy_pass http://127.0.0.1:8000;
           proxy_buffering off;
           proxy_request_buffering off;
       }
       
       location / {
           try_files $uri $uri/ /index.html;
       }
   }
   ```

### 🐛 阶段八：调试与故障排除
1. **常见问题排查**
   ```bash
   # 服务日志
   sudo journalctl -u videohub -f
   
   # 路径权限检查
    ls -la /mnt/mydisk/video-site/
   
   # 端口监听检查
   sudo netstat -tlnp | grep :8000
   ```

## 三、风险评估与缓解

| 风险点 | 可能性 | 影响 | 缓解措施 | 状态 |
|--------|--------|------|----------|------|
| ARM64包兼容性问题 | 低 | 高 | 使用固定版本，优先wheel包 | ⏳ |
| 外接存储性能瓶颈 | 中 | 中 | 使用USB 3.0硬盘/NVMe SSD | ⏳ |
| 路径配置错误 | 中 | 高 | 验证所有硬编码路径 | ⏳ |
| 内存不足（4GB版） | 低 | 高 | 监控内存，限制并发 | ⏳ |
| 网络传输中断 | 中 | 中 | 使用有线网络，断点续传 | ⏳ |

## 四、成功标准

### 核心功能验证
- [ ] 后端服务稳定运行在8000端口
- [ ] 前端页面正常加载和交互
- [ ] 视频上传/播放/删除功能正常
- [ ] 缩略图自动生成
- [ ] Systemd服务自动重启正常
- [ ] 存储路径正确使用`/mnt/mydisk/video-site`

### 性能指标
- [ ] 视频播放无卡顿（本地网络）
- [ ] 上传速度 ≥ 10MB/s（千兆有线网络）
- [ ] 服务内存占用 < 1GB
- [ ] 启动时间 < 30秒

## 五、检查清单

### 前置条件检查
- [ ] 树莓派5已安装64-bit OS
- [ ] 外接存储已挂载到`/mnt/mydisk`
- [ ] 网络连接稳定（推荐有线）
- [ ] 用户对存储设备有读写权限

### 配置验证
- [ ] `requirements.txt` 包含阿里云镜像说明
- [ ] 所有Python文件中的路径已更新
- [ ] 前端构建配置正确

### 部署完成确认
- [ ] 服务可通过 `http://<IP>:8000` 访问
- [ ] 可通过 `sudo systemctl status videohub` 查看状态
- [ ] 数据文件正确存储在 `/mnt/mydisk/video-site/`

## 六、后续优化建议

1. **监控与告警**
   - 添加服务健康检查端点
   - 配置磁盘空间监控
   - 设置日志轮转

2. **性能优化**
   - 启用Nginx gzip压缩
   - 配置静态资源缓存
   - 考虑视频转码预处理

3. **安全加固**
   - 限制上传文件类型
   - 设置请求速率限制
   - 考虑基本认证（如需要）