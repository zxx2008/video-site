# VideoHub 树莓派 5 部署指南

## 兼容性说明

**结论：完全可以在树莓派 5 上部署。**

树莓派 5 搭载 BCM2712 (ARM Cortex-A76) 四核处理器，4GB/8GB 内存，运行 64 位 Raspberry Pi OS (Debian Bookworm)。VideoHub 的所有依赖均支持 ARM64 架构：

| 组件 | 兼容性 | 说明 |
|------|--------|------|
| Python 3.11+ | ✅ | Raspberry Pi OS 自带 Python 3.11 |
| FastAPI + Uvicorn | ✅ | 纯 Python，uvloop/httptools 有 ARM64 wheel |
| aiosqlite (SQLite) | ✅ | Python 内置 sqlite3 模块 |
| FFmpeg | ✅ | 系统包管理器直接安装 |
| Node.js 20+ | ✅ | 官方提供 ARM64 二进制包 |
| Vue 3 + Vite | ✅ | 构建产物为纯静态文件 |

**性能参考**：树莓派 5 足以应对 1~5 人同时在线观看视频的场景。视频播放本质是文件 I/O，瓶颈在存储和网络带宽而非 CPU。

---

## 一、硬件准备

- 树莓派 5（推荐 8GB 内存版本，4GB 也可）
- MicroSD 卡 32GB+（仅装系统），或 NVMe SSD（通过 HAT 连接，推荐）
- **外接存储**：USB 移动硬盘或 NVMe SSD（用于存放视频文件，强烈推荐）
- 有线网络连接（推荐，千兆网口吞吐稳定）
- 电源：官方 27W USB-C 电源适配器

---

## 二、系统准备

### 2.1 烧录系统

使用 [Raspberry Pi Imager](https://www.raspberrypi.com/software/) 烧录 **Raspberry Pi OS (64-bit, Lite)**（无桌面版本，节省资源）。

烧录时在高级设置中配置：
- 主机名：如 `videohub`
- 启用 SSH
- 设置用户名密码
- 配置 Wi-Fi（若无有线网络）

### 2.2 首次启动与更新

```bash
# SSH 连接到树莓派
ssh <用户名>@<树莓派IP>

# 更新系统
sudo apt update && sudo apt upgrade -y
```

### 2.3 安装系统依赖

```bash
sudo apt install -y python3 python3-venv python3-pip ffmpeg git
```

验证安装：

```bash
python3 --version    # 应 >= 3.11
ffmpeg -version      # 确认已安装
ffprobe -version     # 确认已安装（随 ffmpeg 一起）
```

### 2.4 安装 Node.js（构建前端用）

```bash
# 使用 NodeSource 安装 Node.js 20 LTS
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo bash -
sudo apt install -y nodejs

node --version   # 应 >= 20
npm --version
```

> **提示**：如果你选择在其他机器上构建前端（见第五节"交叉构建"），树莓派上可以不装 Node.js。

---

## 三、部署 VideoHub

### 3.1 获取项目代码

```bash
cd ~
git clone <你的仓库地址> video-site
cd video-site
```

或者直接将项目文件通过 `scp` / `rsync` 传输到树莓派：

```bash
# 在你的开发机上执行
rsync -avz --exclude 'node_modules' --exclude 'venv' --exclude 'data' \
  /path/to/video-site/ <用户名>@<树莓派IP>:~/video-site/
```

### 3.2 后端设置

```bash
cd ~/video-site/backend

# 创建 Python 虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

> **注意**：如果 PyPI 访问慢，可使用国内镜像：
> ```bash
> pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
> ```

### 3.3 前端构建

```bash
cd ~/video-site/frontend

# 安装依赖
npm install

# 构建生产版本
npm run build
```

构建完成后 `frontend/dist/` 目录将包含所有静态文件。

> 在树莓派 5 上执行 `npm run build` 大约需要 1~3 分钟，这是正常的。

### 3.4 验证启动

```bash
cd ~/video-site/backend
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000
```

在浏览器访问 `http://<树莓派IP>:8000`，确认页面正常加载。`Ctrl+C` 停止。

---

## 四、配置外接存储（推荐）

视频文件通常很大，建议将 `data/` 目录放在外接硬盘上。

### 4.1 挂载外接硬盘

```bash
# 查看磁盘
lsblk

# 假设外接硬盘为 /dev/sda1，格式化为 ext4（仅首次，会清空数据！）
sudo mkfs.ext4 /dev/sda1

# 创建挂载点并挂载
sudo mkdir -p /mnt/videos
sudo mount /dev/sda1 /mnt/videos
sudo chown $(whoami):$(whoami) /mnt/videos
```

### 4.2 设置开机自动挂载

```bash
# 获取 UUID
sudo blkid /dev/sda1

# 编辑 fstab，添加一行（替换为实际 UUID）
echo 'UUID=<你的UUID>  /mnt/videos  ext4  defaults,noatime  0  2' | sudo tee -a /etc/fstab
```

### 4.3 链接 data 目录

```bash
cd ~/video-site

# 如果已有 data 目录，先迁移数据
mv data/* /mnt/videos/ 2>/dev/null
rmdir data 2>/dev/null

# 创建软链接
ln -s /mnt/videos data
```

---

## 五、生产部署（Systemd 服务）

### 5.1 创建 systemd 服务文件

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

> 将上面的 `<你的用户名>` 替换为实际用户名。

### 5.2 启动并设置开机自启

```bash
sudo systemctl daemon-reload
sudo systemctl enable videohub
sudo systemctl start videohub
```

### 5.3 管理服务

```bash
sudo systemctl status videohub     # 查看状态
sudo systemctl restart videohub    # 重启
sudo systemctl stop videohub       # 停止
journalctl -u videohub -f          # 查看实时日志
```

---

## 六、（可选）Nginx 反向代理

如果希望通过 80 端口访问，或需要更好的静态文件性能：

### 6.1 安装 Nginx

```bash
sudo apt install -y nginx
```

### 6.2 配置站点

```bash
sudo tee /etc/nginx/sites-available/videohub << 'EOF'
server {
    listen 80;
    server_name _;

    # 前端静态文件
    root /home/<你的用户名>/video-site/frontend/dist;
    index index.html;

    # 上传大小限制
    client_max_body_size 2G;

    # API 反向代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 流式响应（视频播放/下载）
        proxy_buffering off;
        proxy_request_buffering off;
    }

    # SPA 路由 fallback
    location / {
        try_files $uri $uri/ /index.html;
    }

    # 静态资源缓存
    location /assets/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# 启用站点
sudo ln -sf /etc/nginx/sites-available/videohub /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# 测试配置并启动
sudo nginx -t
sudo systemctl enable nginx
sudo systemctl restart nginx
```

此时通过 `http://<树莓派IP>` （80端口）即可访问。

---

## 七、交叉构建前端（可选）

如果不想在树莓派上安装 Node.js，可以在开发机上构建好前端再传输：

```bash
# 在开发机上
cd /path/to/video-site/frontend
npm install
npm run build

# 将构建产物传输到树莓派
rsync -avz dist/ <用户名>@<树莓派IP>:~/video-site/frontend/dist/
```

这样树莓派上只需要 Python 环境和 FFmpeg。

---

## 八、常见问题

### Q: 视频播放卡顿？

- 确认使用**有线网络**连接，千兆网口理论带宽 125MB/s，足以流畅播放 4K 视频
- 如果使用 MicroSD 卡存储视频，读取速度可能成为瓶颈，建议换用 USB 3.0 硬盘或 NVMe SSD
- 检查视频编码，H.264 兼容性最好，浏览器可硬解

### Q: 上传大文件失败？

- 使用 Nginx 时确认 `client_max_body_size` 设置足够大
- 大于 100MB 的文件会自动走分块上传，确保 `data/chunks/` 所在磁盘空间充足

### Q: 缩略图生成失败？

- 确认 FFmpeg 已正确安装：`ffmpeg -version`
- 检查视频文件是否完整，损坏的视频无法提取帧

### Q: 如何备份？

- 数据库文件：`data/videohub.db`（SQLite 单文件）
- 视频文件：`data/videos/`
- 缩略图：`data/thumbs/`

```bash
# 简单备份脚本
rsync -avz ~/video-site/data/ /mnt/backup/videohub-data/
```

### Q: 如何更新版本？

```bash
cd ~/video-site
git pull

# 更新后端依赖
cd backend && source venv/bin/activate && pip install -r requirements.txt

# 重新构建前端
cd ../frontend && npm install && npm run build

# 重启服务
sudo systemctl restart videohub
```

---

## 部署架构总览

```
┌──────────────────────────────────────────────────┐
│                  树莓派 5                         │
│                                                  │
│  ┌──────────┐     ┌───────────────────────────┐  │
│  │  Nginx   │────▶│  Uvicorn (FastAPI :8000)  │  │
│  │  (:80)   │     │  ├─ /api/*  REST 接口     │  │
│  │          │     │  ├─ 视频流 (HTTP Range)    │  │
│  └────┬─────┘     │  └─ 静态文件 fallback      │  │
│       │           └──────────┬────────────────┘  │
│       │                      │                   │
│  frontend/dist/         data/ (软链接)           │
│  (静态文件)              │                       │
│                     /mnt/videos/                  │
│                     ├─ videohub.db                │
│                     ├─ videos/                    │
│                     └─ thumbs/                    │
│                                                  │
│              ┌──────────────┐                    │
│              │ USB 硬盘/SSD │                    │
│              └──────────────┘                    │
└──────────────────────────────────────────────────┘
```