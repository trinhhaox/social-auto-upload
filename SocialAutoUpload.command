#!/bin/bash

# Chuyển đến thư mục chứa file
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

# Chạy start.sh
chmod +x ./start.sh ./stop.sh
./start.sh
