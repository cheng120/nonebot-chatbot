#!/usr/bin/env python3
"""直接复制 nonebot_plugin_xiuxian_2 插件到本地"""
import shutil
import sys
from pathlib import Path

# 项目根目录
project_root = Path(__file__).parent.parent

# 源目录和目标目录
source_dir = project_root / "venv" / "lib" / "python3.13" / "site-packages" / "nonebot_plugin_xiuxian_2"
target_dir = project_root / "src" / "plugins" / "xiuxian_2"

print("=" * 60)
print("开始迁移 nonebot_plugin_xiuxian_2 插件")
print("=" * 60)
print(f"源目录: {source_dir}")
print(f"目标目录: {target_dir}")

# 检查源目录是否存在
if not source_dir.exists():
	print(f"❌ 源目录不存在: {source_dir}")
	sys.exit(1)

# 如果目标目录已存在，先备份
if target_dir.exists():
	import time
	backup_dir = target_dir.with_name(f"{target_dir.name}.bak.{int(time.time())}")
	print(f"⚠️ 目标目录已存在，备份到: {backup_dir}")
	shutil.move(str(target_dir), str(backup_dir))

# 创建目标目录
target_dir.mkdir(parents=True, exist_ok=True)

# 复制所有文件（排除 __pycache__）
copied_count = 0
for item in source_dir.rglob("*"):
	if "__pycache__" in str(item):
		continue
	
	relative_path = item.relative_to(source_dir)
	target_path = target_dir / relative_path
	
	if item.is_dir():
		target_path.mkdir(parents=True, exist_ok=True)
	elif item.is_file():
		target_path.parent.mkdir(parents=True, exist_ok=True)
		shutil.copy2(item, target_path)
		copied_count += 1
		if copied_count % 10 == 0:
			print(f"已复制 {copied_count} 个文件...")

print(f"✅ 迁移完成！共复制 {copied_count} 个文件")
print(f"   目标路径: {target_dir}")
print(f"   插件路径: src.plugins.xiuxian_2")

