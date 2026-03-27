#!/usr/bin/env python3
"""
修复已迁移插件中的外部插件引用
将 require("nonebot_plugin_xxx") 和 import 语句改为本地插件路径
"""
import re
from pathlib import Path
import sys

def fix_plugin_references(file_path: Path) -> bool:
	"""
	修复单个文件中的外部插件引用
	
	Returns:
		是否进行了修改
	"""
	try:
		with open(file_path, "r", encoding="utf-8") as f:
			content = f.read()
		
		original_content = content
		
		# 修复 require() 调用
		def replace_require(match):
			plugin_name = match.group(1)
			if plugin_name.startswith("nonebot_plugin_"):
				local_name = plugin_name.replace("nonebot_plugin_", "")
				return f'require("src.plugins.{local_name}")'
			return match.group(0)
		
		content = re.sub(r'require\(["\'](nonebot_plugin_\w+)["\']\)', replace_require, content)
		
		# 修复 from import 语句
		def replace_from_import(match):
			plugin_name = match.group(1)
			if plugin_name.startswith("nonebot_plugin_"):
				local_name = plugin_name.replace("nonebot_plugin_", "")
				return f'from src.plugins.{local_name}'
			return match.group(0)
		
		content = re.sub(r'from (nonebot_plugin_\w+)', replace_from_import, content)
		
		# 修复 import 语句
		def replace_import(match):
			plugin_name = match.group(1)
			if plugin_name.startswith("nonebot_plugin_"):
				local_name = plugin_name.replace("nonebot_plugin_", "")
				return f'import src.plugins.{local_name}'
			return match.group(0)
		
		content = re.sub(r'^import (nonebot_plugin_\w+)', replace_import, content, flags=re.MULTILINE)
		
		# 修复 inherit_supported_adapters() 调用
		def replace_inherit_adapters(match):
			# 匹配 inherit_supported_adapters("plugin1", "plugin2", ...)
			args_str = match.group(1)
			# 解析参数列表（处理引号和空格）
			plugins = []
			for p in args_str.split(","):
				p = p.strip().strip('"\'')
				if p:
					plugins.append(p)
			
			# 转换每个插件名
			new_plugins = []
			for plugin in plugins:
				if plugin.startswith("nonebot_plugin_"):
					local_name = plugin.replace("nonebot_plugin_", "")
					new_plugins.append(f'"src.plugins.{local_name}"')
				else:
					# 保持原样（可能是外部插件或其他格式）
					new_plugins.append(f'"{plugin}"')
			return f'inherit_supported_adapters({", ".join(new_plugins)})'
		
		# 匹配 inherit_supported_adapters("plugin1", "plugin2", ...) 或 inherit_supported_adapters("plugin1")
		content = re.sub(
			r'inherit_supported_adapters\(([^)]+)\)',
			replace_inherit_adapters,
			content
		)
		
		# 如果内容有变化，写回文件
		if content != original_content:
			with open(file_path, "w", encoding="utf-8") as f:
				f.write(content)
			return True
		
		return False
	except Exception as e:
		print(f"❌ 修复文件 {file_path} 时出错: {e}")
		return False

def main():
	"""主函数"""
	# 获取项目根目录
	script_dir = Path(__file__).parent
	project_root = script_dir.parent
	plugins_dir = project_root / "src" / "plugins"
	
	if not plugins_dir.exists():
		print(f"❌ 插件目录不存在: {plugins_dir}")
		sys.exit(1)
	
	print(f"🔍 扫描插件目录: {plugins_dir}")
	print("=" * 60)
	
	fixed_count = 0
	total_files = 0
	
	# 遍历所有 Python 文件
	for py_file in plugins_dir.rglob("*.py"):
		total_files += 1
		relative_path = py_file.relative_to(plugins_dir)
		
		if fix_plugin_references(py_file):
			print(f"✅ 已修复: {relative_path}")
			fixed_count += 1
	
	print("=" * 60)
	print(f"📊 统计:")
	print(f"  - 总文件数: {total_files}")
	print(f"  - 修复文件数: {fixed_count}")
	print(f"  - 无需修复: {total_files - fixed_count}")
	
	if fixed_count > 0:
		print("\n💡 提示: 已修复所有外部插件引用，请重启机器人以应用更改")
	else:
		print("\n✅ 所有插件引用已正确，无需修复")

if __name__ == "__main__":
	main()

