#!/usr/bin/env python3
"""执行迁移 nonebot_plugin_xiuxian_2"""
import sys
import os
from pathlib import Path

# 设置项目根目录
project_root = Path(__file__).parent.parent
os.chdir(str(project_root))
sys.path.insert(0, str(project_root))

# 设置环境变量，避免 NoneBot 初始化问题
os.environ["MIGRATE_SCRIPT_MODE"] = "1"

try:
	# 导入迁移函数
	from src.plugins.migrate_plugin import copy_plugin_to_local
	
	print("=" * 60)
	print("开始迁移 nonebot_plugin_xiuxian_2 插件")
	print("=" * 60)
	
	# 执行迁移
	success, path, error = copy_plugin_to_local(
		'nonebot_plugin_xiuxian_2',
		'nonebot-plugin-xiuxian-2'
	)
	
	if success:
		print(f"\n✅ 迁移成功！")
		print(f"   本地插件路径: {path}")
		print(f"   目标目录: {project_root / 'src' / 'plugins' / 'xiuxian_2'}")
	else:
		print(f"\n❌ 迁移失败: {error}")
		sys.exit(1)
		
except Exception as e:
	print(f"❌ 执行失败: {e}")
	import traceback
	traceback.print_exc()
	sys.exit(1)

