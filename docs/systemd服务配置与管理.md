# VideoHub systemd 服务配置与管理

本文档详细说明 VideoHub 在树莓派 5 上的 systemd 服务配置，以及日常管理方法。

## 一、服务文件配置详解

### 1.1 服务文件位置
```
/etc/systemd/system/videohub.service
```

### 1.2 服务文件内容
```ini
[Unit]
Description=VideoHub Video Management Service
After=network.target        # 网络就绪后启动

[Service]
Type=simple
User=zxx                    # 以您的用户名运行
WorkingDirectory=/home/zxx/video-site/backend  # 工作目录
Environment="PATH=/home/zxx/video-site/backend/venv/bin:/usr/bin:/bin"
ExecStart=/home/zxx/video-site/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always              # 服务崩溃自动重启
RestartSec=5                # 重启等待5秒

[Install]
WantedBy=multi-user.target  # 多用户模式启动
```

### 1.3 配置说明

| 配置项 | 说明 | 注意 |
|--------|------|------|
| `User=zxx` | 服务运行用户 | 必须与您的用户名一致 |
| `WorkingDirectory` | 工作目录 | 指向 `backend/` 目录 |
| `Environment="PATH=..."` | 环境变量 | 包含虚拟环境的 `bin` 目录 |
| `ExecStart` | 启动命令 | 使用虚拟环境中的 `uvicorn` |
| `Restart=always` | 自动重启 | 服务崩溃后自动恢复 |
| `RestartSec=5` | 重启间隔 | 等待5秒后重启 |

## 二、systemctl 管理命令

### 2.1 基本管理命令

| 命令 | 作用 | 示例输出说明 |
|------|------|--------------|
| `sudo systemctl status videohub` | 查看服务状态 | `active (running)` 表示正常运行 |
| `sudo systemctl start videohub` | 启动服务 | |
| `sudo systemctl stop videohub` | 停止服务 | |
| `sudo systemctl restart videohub` | 重启服务 | 配置更改后使用 |
| `sudo systemctl enable videohub` | 启用开机自启 | 已配置，无需重复执行 |
| `sudo systemctl disable videohub` | 禁用开机自启 | 如需手动控制时使用 |

### 2.2 状态检查命令

```bash
# 查看详细状态（推荐）
sudo systemctl status videohub --no-pager

# 查看服务是否已启用开机启动
systemctl is-enabled videohub

# 查看服务启动时间
systemctl show videohub -p ActiveEnterTimestamp
```

### 2.3 日志查看命令

```bash
# 查看完整日志
sudo journalctl -u videohub --no-pager

# 查看最近50条日志
sudo journalctl -u videohub -n 50 --no-pager

# 实时查看日志（按 Ctrl+C 退出）
sudo journalctl -u videohub -f

# 查看特定时间段的日志
sudo journalctl -u videohub --since "2026-03-08 12:00:00" --until "2026-03-08 13:00:00"
```

## 三、服务验证方法

### 3.1 本地访问测试
```bash
# 测试API文档页面
curl -s http://localhost:8000/docs | grep -o "<title>[^<]*</title>"

# 测试前端页面
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/

# 测试视频列表API
curl -s http://localhost:8000/api/videos | python3 -m json.tool
```

### 3.2 网络访问测试
```bash
# 使用树莓派IP地址测试（替换为您的IP）
curl -s -o /dev/null -w "%{http_code}" http://192.168.31.145:8000/
```

### 3.3 端口占用检查
```bash
# 检查8000端口是否被占用
sudo netstat -tlnp | grep :8000

# 查看占用端口的进程
sudo lsof -i :8000
```

## 四、常见问题排查

### 4.1 服务启动失败

**问题现象**：`sudo systemctl status videohub` 显示 `failed` 状态

**排查步骤**：
1. 查看详细错误日志
   ```bash
   sudo journalctl -u videohub -n 30 --no-pager
   ```

2. 检查端口占用
   ```bash
   sudo lsof -i :8000
   # 如果端口被占用，结束占用进程
   sudo kill <PID>
   ```

3. 检查路径权限
   ```bash
   ls -la /home/zxx/video-site/backend/venv/bin/uvicorn
   ls -la /home/zxx/video-site/backend/main.py
   ```

### 4.2 无法访问服务

**问题现象**：服务状态正常但无法通过浏览器访问

**排查步骤**：
1. 检查防火墙设置
   ```bash
   sudo ufw status
   # 如果需要开放端口
   sudo ufw allow 8000
   ```

2. 检查网络连接
   ```bash
   # 本地测试
   curl http://localhost:8000/
   
   # 网络测试（从其他设备）
   # 在其他设备上执行
   curl http://<树莓派IP>:8000/
   ```

3. 检查服务绑定地址
   ```bash
   # 确认服务绑定到 0.0.0.0
   sudo ss -tlnp | grep :8000
   ```

### 4.3 数据存储问题

**问题现象**：视频上传失败或缩略图无法生成

**排查步骤**：
1. 检查存储目录权限
   ```bash
   ls -la /mnt/mydisk/video-site/
   # 确保目录可写
   touch /mnt/mydisk/video-site/test.txt && rm /mnt/mydisk/video-site/test.txt
   ```

2. 检查子目录是否存在
   ```bash
   ls -la /mnt/mydisk/video-site/{videos,thumbs,chunks}
   ```

## 五、维护与更新

### 5.1 更新代码后的操作
```bash
# 1. 停止服务
sudo systemctl stop videohub

# 2. 更新代码（通过 git pull 或其他方式）

# 3. 重启服务
sudo systemctl start videohub

# 4. 验证服务
sudo systemctl status videohub
```

### 5.2 更新依赖后的操作
```bash
# 1. 停止服务
sudo systemctl stop videohub

# 2. 更新Python依赖
cd /home/zxx/video-site/backend
source venv/bin/activate
pip install -i http://mirrors.aliyun.com/pypi/simple/ -r requirements.txt

# 3. 更新前端依赖（如需）
cd /home/zxx/video-site/frontend
npm install --registry=https://registry.npmmirror.com
npm run build

# 4. 重启服务
sudo systemctl start videohub
```

### 5.3 服务配置修改
```bash
# 1. 修改服务文件
sudo nano /etc/systemd/system/videohub.service

# 2. 重载配置
sudo systemctl daemon-reload

# 3. 重启服务
sudo systemctl restart videohub
```

## 六、监控与维护脚本

### 6.1 健康检查脚本
创建 `/home/zxx/check-videohub.sh`：
```bash
#!/bin/bash
SERVICE="videohub"
URL="http://localhost:8000/api/videos"

# 检查服务状态
if systemctl is-active --quiet $SERVICE; then
    echo "$(date): 服务运行正常"
    
    # 检查API响应
    if curl -s --max-time 10 "$URL" > /dev/null; then
        echo "$(date): API接口正常"
    else
        echo "$(date): API接口异常，尝试重启服务"
        sudo systemctl restart $SERVICE
    fi
else
    echo "$(date): 服务未运行，尝试启动"
    sudo systemctl start $SERVICE
fi
```

### 6.2 日志清理脚本
```bash
# 保留最近7天的日志
sudo journalctl --vacuum-time=7d

# 清理videohub服务日志
sudo journalctl --vacuum-time=7d --unit=videohub
```

## 七、注意事项

1. **用户权限**：确保服务文件中 `User=` 的值与您的用户名一致
2. **路径正确性**：工作目录和虚拟环境路径必须正确
3. **存储空间**：定期检查 `/mnt/mydisk/video-site/` 的可用空间
4. **网络配置**：如果树莓派IP地址变更，需要更新访问地址
5. **备份策略**：定期备份 `/mnt/mydisk/video-site/videohub.db` 数据库文件

## 八、快速参考

### 服务状态检查
```bash
# 一键检查
sudo systemctl status videohub && \
curl -s -o /dev/null -w "HTTP状态码: %{http_code}\n" http://localhost:8000/
```

### 重启服务流程
```bash
sudo systemctl stop videohub
sudo systemctl start videohub
sudo systemctl status videohub
```

### 查看实时日志
```bash
sudo journalctl -u videohub -f
```

---

**最后更新时间**：2026-03-08  
**适用版本**：VideoHub 树莓派部署版本  
**维护者**：系统管理员