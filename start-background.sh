#!/bin/bash
# nonebot-chatbot 后台启动
set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
mkdir -p logs data

PIDFILE="logs/bot.pid"
LOGFILE="logs/bot.log"

if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
	echo "nonebot-chatbot 已在运行 (PID: $(cat "$PIDFILE"))，请先执行 ./stop-background.sh"
	exit 1
fi

if [ -d "$ROOT/venv" ]; then
	set +u
	source venv/bin/activate
	set -u
fi

if ! command -v python3 &>/dev/null; then
	echo "未找到 python3"
	exit 1
fi

nohup python3 bot.py >> "$LOGFILE" 2>&1 &
echo $! > "$PIDFILE"
echo "nonebot-chatbot 已后台启动，PID: $(cat "$PIDFILE")，日志: $LOGFILE"
