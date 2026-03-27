#!/usr/bin/env python3
"""内联执行复制 - 直接使用 Python 代码"""
import shutil
import time
from pathlib import Path

def ignore_pycache(dirname, filenames):
	return [f for f in filenames if f == '__pycache__' or f.endswith(('.pyc', '.pyo'))]

# 执行复制
project_root = Path(__file__).parent.parent
source = project_root / "venv" / "lib" / "python3.13" / "site-packages" / "nonebot_plugin_xiuxian_2"
target = project_root / "src" / "plugins" / "xiuxian_2"

if not source.exists():
	raise FileNotFoundError(f"源目录不存在: {source}")

# 备份现有目录
if target.exists():
	backup_dir = target.with_name(f"{target.name}.backup.{int(time.time())}")
	if backup_dir.exists():
		shutil.rmtree(str(backup_dir))
	shutil.move(str(target), str(backup_dir))

# 执行复制
shutil.copytree(str(source), str(target), ignore=ignore_pycache)

# 统计
py_files = list(target.rglob("*.py"))
print(f"✅ 复制完成！Python 文件: {len(py_files)} 个")

