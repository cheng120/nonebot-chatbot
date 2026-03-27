#!/usr/bin/env python3
"""完整复制 nonebot_plugin_xiuxian_2 插件所有文件"""
import shutil
import sys
from pathlib import Path

def ignore_pycache(dirname, filenames):
	"""忽略 __pycache__ 目录和 .pyc 文件"""
	return [f for f in filenames if f == '__pycache__' or f.endswith('.pyc')]

# 项目根目录
project_root = Path(__file__).parent.parent

# 源目录和目标目录
source_dir = project_root / "venv" / "lib" / "python3.13" / "site-packages" / "nonebot_plugin_xiuxian_2"
target_dir = project_root / "src" / "plugins" / "xiuxian_2"

print("=" * 60)
print("完整复制 nonebot_plugin_xiuxian_2 插件")
print("=" * 60)
print(f"源目录: {source_dir}")
print(f"目标目录: {target_dir}")

# 检查源目录是否存在
if not source_dir.exists():
	print(f"❌ 源目录不存在: {source_dir}")
	sys.exit(1)

# 如果目标目录已存在，先备份（但保留已复制的文件）
if target_dir.exists():
	import time
	backup_dir = target_dir.with_name(f"{target_dir.name}.bak.{int(time.time())}")
	print(f"⚠️ 目标目录已存在，备份到: {backup_dir}")
	shutil.move(str(target_dir), str(backup_dir))

# 使用 copytree 复制整个目录（排除 __pycache__）
try:
	shutil.copytree(
		str(source_dir),
		str(target_dir),
		ignore=ignore_pycache,
		dirs_exist_ok=False
	)
	print(f"✅ 复制完成！")
	print(f"   目标路径: {target_dir}")
	print(f"   插件路径: src.plugins.xiuxian_2")
except Exception as e:
	print(f"❌ 复制失败: {e}")
	import traceback
	traceback.print_exc()
	sys.exit(1)

