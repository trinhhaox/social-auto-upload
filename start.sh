#!/bin/bash

# ==============================================================================
# Script khởi động tự động Social Auto Upload
# ==============================================================================

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo "=================================================="
echo "🚀 Đang khởi động Social Auto Upload..."
echo "=================================================="

# 1. Dọn dẹp tiến trình cũ nếu còn chạy
kill $(lsof -ti:5409) 2>/dev/null || true
kill $(lsof -ti:5173) 2>/dev/null || true

# 2. Khởi động Backend Python Flask
echo "📦 1. Đang khởi chạy Backend API (Port 5409)..."
if [ -d ".venv" ]; then
    PYTHON_CMD=".venv/bin/python"
else
    PYTHON_CMD="python3"
fi

$PYTHON_CMD sau_backend.py > logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "   -> Backend PID: $BACKEND_PID"

# Đợi Backend sẵn sàng
sleep 2

# 3. Khởi động Frontend Vite
echo "🌐 2. Đang khởi chạy Giao diện Frontend (Port 5173)..."
cd "$PROJECT_DIR/sau_frontend"
npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "   -> Frontend PID: $FRONTEND_PID"

cd "$PROJECT_DIR"

# Đợi Frontend sẵn sàng
sleep 2

# 4. Tự động mở trình duyệt web
echo "✨ 3. Mở ứng dụng trên trình duyệt..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    open "http://localhost:5173"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    xdg-open "http://localhost:5173" &>/dev/null || true
fi

echo "=================================================="
echo "✅ Ứng dụng đã sẵn sàng tại: http://localhost:5173"
echo "👉 Bạn có thể sử dụng ứng dụng ngay bây giờ!"
echo "=================================================="
