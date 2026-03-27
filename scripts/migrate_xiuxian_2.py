#!/usr/bin/env python3
"""临时脚本：迁移 nonebot_plugin_xiuxian_2 插件"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 切换到项目根目录
import os
os.chdir(str(project_root))

# 导入迁移函数
from src.plugins.migrate_plugin import copy_plugin_to_local

if __name__ == "__main__":
	print("=" * 60)
	print("开始迁移 nonebot_plugin_xiuxian_2 插件")
	print("=" * 60)
	
	success, path, error = copy_plugin_to_local(
		'nonebot_plugin_xiuxian_2',
		'nonebot-plugin-xiuxian-2'
	)
	
	if success:
		print(f"✅ 迁移成功！")
		print(f"   本地插件路径: {path}")
	else:
		print(f"❌ 迁移失败: {error}")
		sys.exit(1)

