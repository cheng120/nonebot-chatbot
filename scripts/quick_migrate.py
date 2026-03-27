#!/usr/bin/env python3
"""
快速迁移脚本 - 直接执行插件迁移
用法: python scripts/quick_migrate.py <插件名称>
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 设置脚本模式
os.environ["MIGRATE_SCRIPT_MODE"] = "1"

# 导入迁移函数
from src.plugins.migrate_plugin import (
	install_plugin,
	find_plugin_module,
	copy_plugin_to_local,
	update_plugin_config_in_yaml,
	add_plugin_config_to_yaml,
	detect_plugin_config,
	get_plugin_config_template,
)

def migrate(plugin_name: str):
	"""执行完整迁移流程"""
	print(f"\n{'='*60}")
	print(f"🔄 开始迁移插件: {plugin_name}")
	print(f"{'='*60}\n")
	
	# 步骤1: 安装插件
	print("📦 [1/5] 安装插件...")
	install_success, error_detail = install_plugin(plugin_name)
	if not install_success:
		print(f"❌ 安装失败:\n{error_detail}")
		return False
	print("✅ 插件安装成功\n")
	
	# 步骤2: 查找模块
	print("🔍 [2/5] 查找插件模块...")
	module_name = find_plugin_module(plugin_name)
	if not module_name:
		print("❌ 无法找到插件模块")
		return False
	print(f"✅ 找到模块: {module_name}\n")
	
	# 步骤3: 检测配置
	print("⚙️  [3/5] 检测插件配置...")
	plugin_config = detect_plugin_config(module_name)
	config_added = False
	if plugin_config:
		print(f"✅ 检测到配置字段: {list(plugin_config.keys())}")
		plugin_key = module_name.replace("nonebot_plugin_", "").replace("_", "-")
		config_template = {plugin_key: plugin_config}
		config_added = add_plugin_config_to_yaml(plugin_name, config_template)
		if config_added:
			print("✅ 已添加配置到 config.yaml")
	else:
		config_template = get_plugin_config_template(plugin_name)
		if config_template:
			config_added = add_plugin_config_to_yaml(plugin_name, config_template)
			if config_added:
				print("✅ 已添加配置模板到 config.yaml")
	if not config_added:
		print("ℹ️  未检测到配置需求")
	print()
	
	# 步骤4: 复制到本地
	print("📋 [4/5] 复制插件到本地...")
	copy_success, local_plugin_path, copy_error = copy_plugin_to_local(module_name, plugin_name)
	if not copy_success:
		print(f"❌ 复制失败: {copy_error}")
		return False
	print(f"✅ 插件已复制到: {local_plugin_path}\n")
	
	# 步骤5: 更新配置
	print("📝 [5/5] 更新配置文件...")
	update_success = update_plugin_config_in_yaml(plugin_name, local_plugin_path)
	if update_success:
		print(f"✅ 配置文件已更新: {plugin_name} -> {local_plugin_path}")
	else:
		print("⚠️  配置文件更新失败，请手动检查")
	print()
	
	print(f"{'='*60}")
	print(f"✅ 迁移完成！")
	print(f"📦 本地插件路径: {local_plugin_path}")
	print(f"💡 提示: 重启机器人后即可使用迁移后的插件")
	print(f"{'='*60}\n")
	return True

if __name__ == "__main__":
	if len(sys.argv) < 2:
		print("""
用法: python scripts/quick_migrate.py <插件名称>

示例:
  python scripts/quick_migrate.py nonebot-plugin-pokemonle
  python scripts/quick_migrate.py nonebot-plugin-epicfree
		""".strip())
		sys.exit(1)
	
	plugin_name = sys.argv[1]
	success = migrate(plugin_name)
	sys.exit(0 if success else 1)

