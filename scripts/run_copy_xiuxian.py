#!/usr/bin/env python3
"""执行复制操作 - 直接使用 Python 代码"""
import shutil
import sys
from pathlib import Path

def ignore_pycache(dirname, filenames):
	return [f for f in filenames if f == '__pycache__' or f.endswith('.pyc') or f.endswith('.pyo')]

project_root = Path(__file__).parent.parent
source = project_root / "venv" / "lib" / "python3.13" / "site-packages" / "nonebot_plugin_xiuxian_2"
target = project_root / "src" / "plugins" / "xiuxian_2"

if not source.exists():
	print(f"❌ 源目录不存在: {source}")
	sys.exit(1)

if target.exists():
	print("⚠️ 删除现有目标目录...")
	shutil.rmtree(str(target))

try:
	shutil.copytree(str(source), str(target), ignore=ignore_pycache)
	print(f"✅ 复制完成！目标: {target}")
except Exception as e:
	print(f"❌ 失败: {e}")
	sys.exit(1)

