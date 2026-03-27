#!/usr/bin/env python3
"""
测试迁移脚本
用于直接测试插件迁移功能，无需启动机器人
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 设置脚本模式环境变量
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
	list_local_migrated_plugins
)

def main():
	if len(sys.argv) < 2:
		print("""
用法: python scripts/test_migrate.py <插件名称> [操作]

操作:
  - migrate: 执行完整迁移（默认）
  - list: 列出已迁移的本地插件
  - check: 仅检查插件是否已安装

示例:
  python scripts/test_migrate.py nonebot-plugin-pokemonle migrate
  python scripts/test_migrate.py list
		""".strip())
		return
	
	plugin_name = sys.argv[1]
	operation = sys.argv[2] if len(sys.argv) > 2 else "migrate"
	
	if plugin_name == "list":
		print("📋 检查已迁移的本地插件...")
		migrated = list_local_migrated_plugins()
		if migrated:
			print(f"\n✅ 找到 {len(migrated)} 个已迁移的插件:")
			for name, path in migrated.items():
				print(f"  • {name}: {path}")
		else:
			print("\n✅ 未找到已迁移的插件")
		return
	
	if operation == "check":
		print(f"🔍 检查插件: {plugin_name}")
		module_name = find_plugin_module(plugin_name)
		if module_name:
			print(f"✅ 找到模块: {module_name}")
		else:
			print(f"❌ 未找到模块，可能需要先安装插件")
		return
	
	print(f"🔄 开始迁移插件: {plugin_name}")
	print("=" * 60)
	
	# 步骤1: 安装插件
	print("\n📦 步骤1: 安装插件...")
	install_success, error_detail = install_plugin(plugin_name)
	if not install_success:
		print(f"❌ 安装失败: {error_detail}")
		return
	print("✅ 插件安装成功")
	
	# 步骤2: 查找插件模块
	print("\n🔍 步骤2: 查找插件模块...")
	module_name = find_plugin_module(plugin_name)
	if not module_name:
		print("❌ 无法找到插件模块")
		return
	print(f"✅ 找到模块: {module_name}")
	
	# 步骤3: 检测配置
	print("\n⚙️  步骤3: 检测插件配置...")
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
	
	# 步骤4: 复制插件到本地
	print("\n📋 步骤4: 复制插件到本地...")
	copy_success, local_plugin_path, copy_error = copy_plugin_to_local(module_name, plugin_name)
	if not copy_success:
		print(f"❌ 复制失败: {copy_error}")
		return
	print(f"✅ 插件已复制到: {local_plugin_path}")
	
	# 步骤5: 更新配置文件
	print("\n📝 步骤5: 更新配置文件...")
	update_success = update_plugin_config_in_yaml(plugin_name, local_plugin_path)
	if update_success:
		print(f"✅ 配置文件已更新: {plugin_name} -> {local_plugin_path}")
	else:
		print("⚠️  配置文件更新失败，请手动检查")
	
	print("\n" + "=" * 60)
	print(f"✅ 迁移完成！插件路径: {local_plugin_path}")
	print("💡 提示: 重启机器人后即可使用迁移后的插件")

if __name__ == "__main__":
	main()

