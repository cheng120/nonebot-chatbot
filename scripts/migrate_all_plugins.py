#!/usr/bin/env python3
"""
迁移所有已安装的第三方插件到本地插件目录
"""
import sys
import importlib.util
import yaml
import os
from pathlib import Path
from typing import List, Tuple

def get_project_root() -> Path:
	"""获取项目根目录"""
	return Path(__file__).parent.parent

# 添加项目根目录到 Python 路径，确保可以导入 src 模块
project_root = get_project_root()
if str(project_root) not in sys.path:
	sys.path.insert(0, str(project_root))

# 检查并添加虚拟环境路径
venv_path = project_root / "venv"
if venv_path.exists():
	# 添加虚拟环境的 site-packages 到路径
	site_packages = venv_path / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages"
	if site_packages.exists() and str(site_packages) not in sys.path:
		sys.path.insert(0, str(site_packages))
		print(f"已添加虚拟环境路径: {site_packages}")

# 切换到项目根目录
os.chdir(str(project_root))

def find_external_plugins() -> List[Tuple[str, str]]:
	"""
	查找所有已安装的外部插件
	
	Returns:
		[(模块名, 包名), ...] 列表
	"""
	external_plugins = []
	
	# 读取配置文件，获取已启用的插件列表
	config_path = get_project_root() / "configs" / "config.yaml"
	if not config_path.exists():
		print(f"❌ 配置文件不存在: {config_path}")
		return []
	
	with open(config_path, "r", encoding="utf-8") as f:
		config = yaml.safe_load(f) or {}
	
	enabled_plugins = config.get("plugins", {}).get("enabled", [])
	
	# 过滤出外部插件（不是 src.plugins.xxx 格式的）
	project_root = get_project_root()
	print(f"项目根目录: {project_root}")
	
	for plugin_name in enabled_plugins:
		if not plugin_name.startswith("src.plugins."):
			# 尝试多种方式查找模块
			spec = None
			origin_path = None
			
			# 方法1: 使用 find_spec
			try:
				spec = importlib.util.find_spec(plugin_name)
				if spec and spec.origin:
					origin_path = Path(spec.origin)
			except Exception:
				pass
			
			# 方法2: 如果 find_spec 失败，尝试直接导入
			if not spec or not origin_path:
				try:
					module = importlib.import_module(plugin_name)
					if hasattr(module, '__file__') and module.__file__:
						origin_path = Path(module.__file__)
						spec = importlib.util.find_spec(plugin_name)
				except Exception:
					pass
			
			# 方法3: 尝试查找已安装的包
			if not spec or not origin_path:
				try:
					import pkg_resources
					dist = pkg_resources.get_distribution(plugin_name.replace("_", "-"))
					if dist and dist.location:
						# 尝试找到主模块文件
						package_name = plugin_name.replace("_", "-")
						try:
							module = importlib.import_module(plugin_name)
							if hasattr(module, '__file__') and module.__file__:
								origin_path = Path(module.__file__)
						except:
							# 如果导入失败，至少我们知道包已安装
							origin_path = Path(dist.location) / plugin_name
				except Exception:
					pass
			
			if origin_path and origin_path.exists():
				origin_path = origin_path.resolve()
				project_root_resolved = project_root.resolve()
				
				print(f"检查插件: {plugin_name}")
				print(f"  模块路径: {origin_path}")
				
				# 检查是否在项目目录外（外部插件）
				# 注意：venv 目录中的 site-packages 应该被视为外部插件
				is_external = False
				try:
					relative_path = origin_path.relative_to(project_root_resolved)
					# 如果在项目目录内，检查是否在 venv 的 site-packages 中
					if "venv" in str(relative_path) or "site-packages" in str(relative_path):
						# 在 venv 的 site-packages 中，视为外部插件
						is_external = True
						print(f"  → 在 venv 的 site-packages 中，标记为外部插件")
					else:
						# 在项目目录内的 src 或其他目录，跳过
						print(f"  → 在项目目录内，跳过")
						continue
				except ValueError:
					# 不在项目目录内，是外部插件
					is_external = True
					print(f"  → 在项目目录外，标记为外部插件")
				
				if is_external:
					# 推断包名
					if plugin_name.startswith("nonebot_plugin_"):
						package_name = plugin_name.replace("_", "-")
					else:
						package_name = plugin_name.replace("_", "-")
					
					external_plugins.append((plugin_name, package_name))
					print(f"✅ 发现外部插件: {plugin_name} ({package_name})")
			else:
				# 如果无法找到模块，但仍然认为是外部插件（因为不是 src.plugins.xxx 格式）
				# 推断包名（尝试多种格式）
				possible_package_names = []
				if plugin_name.startswith("nonebot_plugin_"):
					# 尝试多种包名格式
					base_name = plugin_name.replace("nonebot_plugin_", "")
					possible_package_names.extend([
						plugin_name.replace("_", "-"),  # nonebot-plugin-xxx
						f"nonebot-plugin-{base_name.replace('_', '-')}",  # nonebot-plugin-xxx
						plugin_name,  # nonebot_plugin_xxx
					])
				else:
					possible_package_names.extend([
						plugin_name.replace("_", "-"),
						f"nonebot-plugin-{plugin_name.replace('_', '-')}",
						plugin_name,
					])
				
				# 去重
				possible_package_names = list(dict.fromkeys(possible_package_names))
				
				# 检查包是否已安装（尝试多种包名格式）
				package_found = False
				found_package_name = None
				
				for pkg_name in possible_package_names:
					try:
						import pkg_resources
						dist = pkg_resources.get_distribution(pkg_name)
						package_found = True
						found_package_name = pkg_name
						
						# 尝试从包的位置找到模块
						if dist and dist.location:
							package_location = Path(dist.location)
							print(f"检查插件: {plugin_name}")
							print(f"  包名: {pkg_name}")
							print(f"  包位置: {package_location}")
							
							# 尝试找到模块文件
							module_file = package_location / plugin_name / "__init__.py"
							if not module_file.exists():
								module_file = package_location / f"{plugin_name}.py"
							
							if module_file.exists():
								origin_path = module_file.resolve()
								project_root_resolved = project_root.resolve()
								
								print(f"  模块文件: {origin_path}")
								
								# 检查是否在项目目录外（外部插件）
								# 注意：venv 目录中的 site-packages 应该被视为外部插件
								is_external = False
								try:
									relative_path = origin_path.relative_to(project_root_resolved)
									relative_str = str(relative_path)
									# 如果在项目目录内，检查是否在 venv 的 site-packages 中
									if "venv" in relative_str or "site-packages" in relative_str or ".venv" in relative_str:
										# 在 venv 的 site-packages 中，视为外部插件
										is_external = True
										print(f"  → 在 venv 的 site-packages 中，标记为外部插件")
									elif relative_str.startswith("src/plugins/"):
										# 在项目目录内的 src/plugins 中，跳过
										print(f"  → 在项目目录内的 src/plugins 中，跳过")
										package_found = False
										break
									else:
										# 在项目目录内的其他位置，跳过
										print(f"  → 在项目目录内，跳过")
										package_found = False
										break
								except ValueError:
									# 不在项目目录内，是外部插件
									is_external = True
									print(f"  → 在项目目录外，标记为外部插件")
								
								if is_external:
									external_plugins.append((plugin_name, pkg_name))
									print(f"✅ 发现外部插件: {plugin_name} ({pkg_name})")
									package_found = True
									break
							else:
								# 包已安装但无法找到模块文件，仍然添加到迁移列表
								external_plugins.append((plugin_name, pkg_name))
								print(f"✅ 发现外部插件: {plugin_name} ({pkg_name}) [包已安装但无法获取模块路径]")
								package_found = True
								break
					except Exception:
						continue
				
				if not package_found:
					# 即使包未安装，如果配置中有，也尝试迁移（可能需要在迁移时安装）
					package_name = possible_package_names[0]
					external_plugins.append((plugin_name, package_name))
					print(f"⚠️ 插件 {plugin_name} 可能未安装，但仍会尝试迁移 (包名: {package_name})")
	
	return external_plugins

def migrate_plugin(module_name: str, package_name: str) -> bool:
	"""迁移单个插件到本地"""
	try:
		# 确保项目根目录在路径中（双重保险）
		project_root = get_project_root()
		if str(project_root) not in sys.path:
			sys.path.insert(0, str(project_root))
		
		# 验证路径设置
		import os
		os.chdir(str(project_root))  # 切换到项目根目录
		
		# 使用 importlib 安全导入，避免触发 NoneBot 初始化
		import importlib.util
		migrate_plugin_path = project_root / "src" / "plugins" / "migrate_plugin.py"
		if not migrate_plugin_path.exists():
			print(f"❌ 找不到 migrate_plugin.py: {migrate_plugin_path}")
			return False
		
		# 使用 spec 和 loader 导入模块，避免执行顶层代码
		spec = importlib.util.spec_from_file_location("migrate_plugin", migrate_plugin_path)
		if spec is None or spec.loader is None:
			print(f"❌ 无法加载 migrate_plugin 模块")
			return False
		
		# 创建一个新的模块对象
		migrate_module = importlib.util.module_from_spec(spec)
		
		# 临时设置环境变量，让 migrate_plugin 知道这是脚本模式
		os.environ["MIGRATE_SCRIPT_MODE"] = "1"
		
		# 执行模块加载（这会执行模块代码，但 try/except 应该能捕获错误）
		try:
			spec.loader.exec_module(migrate_module)
		except ValueError as e:
			# 如果是因为 NoneBot 未初始化，尝试直接读取函数定义
			if "NoneBot has not been initialized" in str(e):
				# 使用 ast 解析文件并提取函数
				import ast
				with open(migrate_plugin_path, "r", encoding="utf-8") as f:
					code = f.read()
				
				# 创建一个命名空间，只包含必要的函数
				namespace = {}
				# 执行代码，但捕获所有异常
				try:
					exec(compile(ast.parse(code), migrate_plugin_path, "exec"), namespace)
				except Exception:
					# 如果执行失败，尝试直接导入函数（跳过顶层代码）
					pass
				
				# 从命名空间中提取函数
				copy_plugin_to_local = namespace.get("copy_plugin_to_local")
				update_plugin_config_in_yaml = namespace.get("update_plugin_config_in_yaml")
				detect_plugin_config = namespace.get("detect_plugin_config")
				add_plugin_config_to_yaml = namespace.get("add_plugin_config_to_yaml")
				get_plugin_config_template = namespace.get("get_plugin_config_template")
				
				if not all([copy_plugin_to_local, update_plugin_config_in_yaml]):
					print(f"❌ 无法从 migrate_plugin 模块中提取必要的函数")
					return False
			else:
				raise
		else:
			# 正常导入成功
			copy_plugin_to_local = migrate_module.copy_plugin_to_local
			update_plugin_config_in_yaml = migrate_module.update_plugin_config_in_yaml
			detect_plugin_config = migrate_module.detect_plugin_config
			add_plugin_config_to_yaml = migrate_module.add_plugin_config_to_yaml
			get_plugin_config_template = migrate_module.get_plugin_config_template
		
		# 清理环境变量
		if "MIGRATE_SCRIPT_MODE" in os.environ:
			del os.environ["MIGRATE_SCRIPT_MODE"]
		
		print(f"\n📦 开始迁移插件: {module_name}")
		
		# 1. 复制插件到本地
		copy_success, local_plugin_path, copy_error = copy_plugin_to_local(module_name, package_name)
		
		if not copy_success:
			print(f"❌ 复制插件失败: {copy_error}")
			return False
		
		# 2. 更新配置文件
		update_success = update_plugin_config_in_yaml(module_name, local_plugin_path)
		if not update_success:
			print(f"⚠️ 更新配置文件失败，但插件已复制到本地")
		
		# 3. 检测并添加配置
		plugin_config = detect_plugin_config(module_name)
		if plugin_config:
			plugin_key = module_name.replace("nonebot_plugin_", "").replace("_", "-")
			config_template = {plugin_key: plugin_config}
			add_plugin_config_to_yaml(package_name, config_template)
		else:
			config_template = get_plugin_config_template(package_name)
			if config_template:
				add_plugin_config_to_yaml(package_name, config_template)
		
		print(f"✅ 插件 {module_name} 迁移完成: {local_plugin_path}")
		return True
	except Exception as e:
		print(f"❌ 迁移插件 {module_name} 失败: {e}")
		import traceback
		traceback.print_exc()
		return False

def main():
	"""主函数"""
	print("=" * 60)
	print("迁移所有外部插件到本地插件目录")
	print("=" * 60)
	
	# 查找所有外部插件
	external_plugins = find_external_plugins()
	
	if not external_plugins:
		print("\n✅ 没有发现需要迁移的外部插件")
		return
	
	print(f"\n📋 发现 {len(external_plugins)} 个外部插件需要迁移:")
	for module_name, package_name in external_plugins:
		print(f"  - {module_name} ({package_name})")
	
	# 确认
	response = input("\n是否继续迁移？(y/n): ").strip().lower()
	if response != 'y':
		print("❌ 已取消迁移")
		return
	
	# 迁移所有插件
	success_count = 0
	failed_count = 0
	
	for module_name, package_name in external_plugins:
		if migrate_plugin(module_name, package_name):
			success_count += 1
		else:
			failed_count += 1
	
	# 输出结果
	print("\n" + "=" * 60)
	print("迁移完成")
	print("=" * 60)
	print(f"✅ 成功: {success_count} 个")
	if failed_count > 0:
		print(f"❌ 失败: {failed_count} 个")
	print("\n💡 提示: 请重启机器人以应用更改")

if __name__ == "__main__":
	main()

