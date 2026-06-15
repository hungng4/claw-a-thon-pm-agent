#!/usr/bin/env bash
# Chạy Telegram bridge BỀN BỈ trên máy luôn-bật:
#  - tự restart nếu tiến trình chết
#  - ghi log ra bridge/bridge.log
#
# Dùng (từ thư mục gốc repo):
#   macOS  (chặn máy ngủ):   caffeinate -is bash bridge/run_bridge.sh
#   Linux:                   bash bridge/run_bridge.sh
#   Chạy nền, đóng terminal vẫn sống:
#     nohup caffeinate -is bash bridge/run_bridge.sh >/dev/null 2>&1 &   # macOS
#     nohup bash bridge/run_bridge.sh >/dev/null 2>&1 &                  # Linux
#
# Yêu cầu: file .env có TELEGRAM_BOT_TOKEN, AGENT_ENDPOINT_URL, BOT_USERNAME.
set -u
cd "$(dirname "$0")/.."
LOG="${BRIDGE_LOG:-bridge/bridge.log}"
echo "[$(date)] run_bridge khởi động — log: $LOG"
while true; do
  echo "[$(date)] starting telegram_bridge.py" >> "$LOG"
  python3 bridge/telegram_bridge.py >> "$LOG" 2>&1
  code=$?
  echo "[$(date)] bridge thoát (code=$code) — restart sau 5s" >> "$LOG"
  sleep 5
done
