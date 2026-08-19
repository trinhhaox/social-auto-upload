#!/bin/bash

# ==============================================================================
# Script dừng toàn bộ tiến trình Social Auto Upload
# ==============================================================================

echo "🛑 Đang dừng toàn bộ dịch vụ Social Auto Upload..."

kill $(lsof -ti:5409) 2>/dev/null || true
kill $(lsof -ti:5173) 2>/dev/null || true

echo "✅ Đã tắt hoàn toàn Backend và Frontend."
