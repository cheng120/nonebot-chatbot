#!/usr/bin/env python3
"""完整复制 nonebot_plugin_xiuxian_2 所有文件"""
import shutil
import sys
from pathlib import Path

def ignore_pycache(dirname, filenames):
	return [f for f in filenames if f == '__pycache__' or f.endswith(('.pyc', '.pyo'))]

project_root = Path(__file__).parent.parent
source = project_root / "venv" / "lib" / "python3.13" / "site-packages" / "nonebot_plugin_xiuxian_2"
target = project_root / "src" / "plugins" / "xiuxian_2"

print("=" * 60)
print("完整复制 nonebot_plugin_xiuxian_2 插件")
print("=" * 60)
print(f"源目录: {source}")
print(f"目标目录: {target}")

if not source.exists():
	print(f"❌ 源目录不存在: {source}")
	sys.exit(1)

# 如果目标目录已存在，先备份已复制的文件，然后删除
if target.exists():
	print("⚠️ 目标目录已存在，备份现有文件...")
	import time
	backup_dir = target.with_name(f"{target.name}.backup.{int(time.time())}")
	if backup_dir.exists():
		shutil.rmtree(str(backup_dir))
	shutil.move(str(target), str(backup_dir))
	print(f"   已备份到: {backup_dir}")

# 使用 copytree 完整复制
try:
	print("开始复制文件...")
	shutil.copytree(str(source), str(target), ignore=ignore_pycache)
	
	# 统计复制的文件数量
	py_files = list(target.rglob("*.py"))
	other_files = []
	for ext in ['.json', '.yaml', '.yml', '.txt', '.md', '.html', '.css', '.js', 
	            '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ttf', '.woff']:
		other_files.extend(list(target.rglob(f"*{ext}")))
	
	print(f"✅ 复制完成！")
	print(f"   Python 文件: {len(py_files)} 个")
	print(f"   其他文件: {len(other_files)} 个")
	print(f"   目标路径: {target}")
	print(f"   插件路径: src.plugins.xiuxian_2")
except Exception as e:
	print(f"❌ 复制失败: {e}")
	import traceback
	traceback.print_exc()
	sys.exit(1)

