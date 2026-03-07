#!/bin/bash

# VideoHub 开发模式启动脚本
# 同时启动后端 (8000) 和前端 (5173)

DIR="$(cd "$(dirname "$0")" && pwd)"

cleanup() {
    echo ""
    echo "正在停止服务..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    wait $BACKEND_PID $FRONTEND_PID 2>/dev/null
    echo "已停止"
    exit 0
}

trap cleanup INT TERM

# 启动后端
echo "启动后端 http://localhost:8000 ..."
cd "$DIR/backend"
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# 启动前端
echo "启动前端 http://localhost:5173 ..."
cd "$DIR/frontend"
npm run dev -- --host 0.0.0.0 &
FRONTEND_PID=$!

echo ""
echo "按 Ctrl+C 停止所有服务"

wait
