#!/usr/bin/env python3
"""最终完整复制脚本 - 使用 shutil 直接复制"""
import shutil
import sys
from pathlib import Path

def ignore_func(dirname, filenames):
	"""忽略 __pycache__ 和 .pyc 文件"""
	ignored = []
	for f in filenames:
		if f == '__pycache__' or f.endswith('.pyc') or f.endswith('.pyo'):
			ignored.append(f)
	return ignored

project_root = Path(__file__).parent.parent
source = project_root / "venv" / "lib" / "python3.13" / "site-packages" / "nonebot_plugin_xiuxian_2"
target = project_root / "src" / "plugins" / "xiuxian_2"

print(f"源目录: {source}")
print(f"目标目录: {target}")

if not source.exists():
	print(f"❌ 源目录不存在")
	sys.exit(1)

# 如果目标目录存在，先删除（因为我们已经复制了部分文件）
if target.exists():
	print("⚠️ 目标目录已存在，将删除后重新复制...")
	shutil.rmtree(str(target))

# 使用 copytree 复制
try:
	shutil.copytree(str(source), str(target), ignore=ignore_func)
	print(f"✅ 复制完成！")
except Exception as e:
	print(f"❌ 复制失败: {e}")
	import traceback
	traceback.print_exc()
	sys.exit(1)

