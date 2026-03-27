#!/bin/bash
ROOT="$(cd "$(dirname "$0")" && pwd)"
PIDFILE="$ROOT/logs/bot.pid"
if [ -f "$PIDFILE" ]; then
	pid=$(cat "$PIDFILE")
	if kill -0 "$pid" 2>/dev/null; then
		kill "$pid"
		echo "已停止 nonebot-chatbot (PID $pid)"
	fi
	rm -f "$PIDFILE"
fi
