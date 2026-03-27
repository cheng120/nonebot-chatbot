#!/usr/bin/env python3
"""
测试插件检测逻辑
"""
import sys
import importlib.util
import yaml
import os
from pathlib import Path

def get_project_root() -> Path:
	"""获取项目根目录"""
	return Path(__file__).parent.parent

# 添加项目根目录到 Python 路径
project_root = get_project_root()
if str(project_root) not in sys.path:
	sys.path.insert(0, str(project_root))

# 检查并添加虚拟环境路径
venv_path = project_root / "venv"
if venv_path.exists():
	for python_version in [f"python{sys.version_info.major}.{sys.version_info.minor}", "python3"]:
		site_packages = venv_path / "lib" / python_version / "site-packages"
		if site_packages.exists() and str(site_packages) not in sys.path:
			sys.path.insert(0, str(site_packages))
			print(f"已添加虚拟环境路径: {site_packages}")
			break

# 读取配置文件
config_path = project_root / "configs" / "config.yaml"
with open(config_path, "r", encoding="utf-8") as f:
	config = yaml.safe_load(f) or {}

enabled_plugins = config.get("plugins", {}).get("enabled", [])

print(f"项目根目录: {project_root}")
print(f"\n已启用的插件列表 ({len(enabled_plugins)} 个):")
for plugin_name in enabled_plugins:
	print(f"  - {plugin_name}")

print("\n" + "=" * 60)
print("检测外部插件:")
print("=" * 60)

external_count = 0
for plugin_name in enabled_plugins:
	if not plugin_name.startswith("src.plugins."):
		external_count += 1
		print(f"\n插件: {plugin_name}")
		
		# 尝试多种方式查找模块
		spec = None
		origin_path = None
		
		# 方法1: 使用 find_spec
		try:
			spec = importlib.util.find_spec(plugin_name)
			if spec and spec.origin:
				origin_path = Path(spec.origin)
				print(f"  find_spec 成功: {origin_path}")
		except Exception as e:
			print(f"  find_spec 失败: {e}")
		
		# 方法2: 尝试直接导入
		if not spec or not origin_path:
			try:
				module = importlib.import_module(plugin_name)
				if hasattr(module, '__file__') and module.__file__:
					origin_path = Path(module.__file__)
					print(f"  直接导入成功: {origin_path}")
			except Exception as e:
				print(f"  直接导入失败: {e}")
		
		# 方法3: 检查包是否已安装
		if not origin_path:
			possible_package_names = []
			if plugin_name.startswith("nonebot_plugin_"):
				base_name = plugin_name.replace("nonebot_plugin_", "")
				possible_package_names.extend([
					plugin_name.replace("_", "-"),
					f"nonebot-plugin-{base_name.replace('_', '-')}",
					plugin_name,
				])
			else:
				possible_package_names.extend([
					plugin_name.replace("_", "-"),
					f"nonebot-plugin-{plugin_name.replace('_', '-')}",
					plugin_name,
				])
			
			possible_package_names = list(dict.fromkeys(possible_package_names))
			
			for pkg_name in possible_package_names:
				try:
					import pkg_resources
					dist = pkg_resources.get_distribution(pkg_name)
					print(f"  ✅ 包已安装: {pkg_name} (位置: {dist.location})")
					break
				except Exception:
					continue
			else:
				print(f"  ⚠️ 包未安装 (尝试的包名: {', '.join(possible_package_names)})")

print(f"\n" + "=" * 60)
print(f"共发现 {external_count} 个外部插件")
print("=" * 60)

