"""
插件管理服务
支持插件加载、启用/禁用管理，插件配置的数据库持久化
"""
import os
import importlib.util
from pathlib import Path
from typing import Dict, Any, Optional, List
from nonebot import load_plugins, get_loaded_plugins
try:
	from nonebot.plugin import load_from_toml, load_plugin
except ImportError:
	# NoneBot 2.0+ 使用不同的导入方式
	try:
		from nonebot import load_from_toml, load_plugin
	except ImportError:
		load_from_toml = None
		load_plugin = None
from nonebot.plugin import Plugin
from src.database.plugin_config import PluginConfig, PluginStatus
from src.database.connection import DatabaseManager
from src.utils.logger import get_logger

logger = get_logger("plugin_manager")


class PluginManager:
	"""插件管理器"""
	
	def __init__(self, plugin_dir: str, db_manager: Optional[DatabaseManager] = None, plugins_config: Optional[Any] = None):
		"""
		初始化插件管理器
		
		Args:
			plugin_dir: 插件目录
			db_manager: 数据库管理器（可选）
			plugins_config: 插件配置对象（PluginsConfig，可选）
		"""
		self.plugin_dir = Path(plugin_dir)
		self.db_manager = db_manager
		self.plugins_config = plugins_config
		self.loaded_plugins: Dict[str, Plugin] = {}
		
		# 确保插件目录存在
		self.plugin_dir.mkdir(parents=True, exist_ok=True)
	
	async def load_all_plugins(self):
		"""
		加载所有插件
		支持从配置文件或数据库读取插件启用状态
		优先级：配置文件 > 数据库
		支持本地插件和外部插件（通过 pyproject.toml 配置）
		"""
		try:
			# 获取启用的插件列表（配置文件优先）
			enabled_plugins = await self._get_enabled_plugins()
			logger.info(f"启用的插件: {enabled_plugins}")
			
			# 1. 加载本地插件（从插件目录）
			plugin_files = self._scan_plugin_dir()
			logger.info(f"发现 {len(plugin_files)} 个本地插件文件")
			
			# 检查是否有包结构的插件（目录形式的插件）
			package_plugins = []
			for item in self.plugin_dir.iterdir():
				if item.is_dir() and not item.name.startswith("_"):
					# 检查是否是包结构（有 .py 文件，且有 __init__.py）
					init_file = item / "__init__.py"
					py_files = list(item.rglob("*.py"))
					if py_files and init_file.exists():
						# 检查是否在启用列表中
						package_name = f"src.plugins.{item.name}"
						if package_name in enabled_plugins:
							package_plugins.append((package_name, item.name))
							logger.info(f"发现包结构插件: {package_name}")
			
			# 加载所有插件（包括文件和包）
			# load_plugins 会自动加载目录中的插件，包括包结构插件
			if plugin_files or package_plugins:
				try:
					load_plugins(str(self.plugin_dir))
					logger.info(f"已通过 load_plugins 加载插件目录")
				except Exception as e:
					logger.error(f"load_plugins 加载失败: {e}", exc_info=True)
			
			# 检查包结构插件是否已被 load_plugins 自动加载
			# 注意：load_plugins 会自动加载包结构插件，不需要显式加载
			if package_plugins:
				loaded_plugins_after = get_loaded_plugins()
				plugin_names_after = [p.name for p in loaded_plugins_after]
				
				for package_name, simple_name in package_plugins:
					# 检查是否已经加载（通过简单名称、完整路径或部分匹配）
					is_loaded = False
					loaded_plugin_name = None
					
					# 检查完整匹配
					if simple_name in plugin_names_after:
						is_loaded = True
						loaded_plugin_name = simple_name
					elif package_name in plugin_names_after:
						is_loaded = True
						loaded_plugin_name = package_name
					else:
						# 检查部分匹配（例如 "manosaba_memes" 匹配 "src.plugins.manosaba_memes"）
						for loaded_name in plugin_names_after:
							if simple_name in loaded_name or loaded_name.endswith(f".{simple_name}"):
								is_loaded = True
								loaded_plugin_name = loaded_name
								break
					
					if is_loaded:
						logger.info(f"✅ 包结构插件 {package_name} 已被 load_plugins 自动加载 (名称: {loaded_plugin_name})")
					else:
						logger.warning(f"⚠️ 包结构插件 {package_name} 未被 load_plugins 加载，可能需要检查插件代码")
						# 不尝试显式加载，避免重复加载错误
						# load_plugins 应该已经处理了所有插件
			
			# 2. 自动迁移启用列表中的外部插件到本地（已安装则迁移，未安装则跳过）
			enabled_plugins = self._auto_migrate_external_plugins(enabled_plugins)
			
			# 3. 加载外部插件（通过 pyproject.toml 配置的插件）
			external_plugins = []
			for plugin_name in enabled_plugins:
				# 检查是否是外部插件（不是 src.plugins.xxx 格式）
				if not plugin_name.startswith("src.plugins.") and not plugin_name.startswith("src/plugins/"):
					external_plugins.append(plugin_name)
			
			if external_plugins:
				logger.info(f"检测到 {len(external_plugins)} 个外部插件: {external_plugins}")
				# 从 pyproject.toml 加载外部插件
				if load_from_toml:
					try:
						project_root = Path(__file__).parent.parent.parent
						pyproject_path = project_root / "pyproject.toml"
						if pyproject_path.exists():
							load_from_toml(str(pyproject_path))
							logger.info(f"已从 pyproject.toml 加载外部插件")
						else:
							logger.warning(f"pyproject.toml 文件不存在: {pyproject_path}")
					except Exception as e:
						logger.warning(f"从 pyproject.toml 加载插件失败: {e}", exc_info=True)
				
				# 尝试手动加载外部插件（如果 load_from_toml 失败或不可用）
				if load_plugin:
					for ext_plugin in external_plugins:
						loaded = False
						# 检查插件是否已经加载（避免重复加载）
						loaded_plugins_before = get_loaded_plugins()
						plugin_names_before = [p.name for p in loaded_plugins_before]
						
						# 如果插件已经加载，跳过
						if ext_plugin in plugin_names_before or any(ext_plugin.replace("-", "_") in pn or pn in ext_plugin.replace("-", "_") for pn in plugin_names_before):
							logger.info(f"✅ 外部插件 {ext_plugin} 已加载，跳过重复加载")
							continue
						
						# 尝试从 pyproject.toml 配置中获取模块名
						# 格式: nonebot-plugin-xxx = ["nonebot_plugin_xxx"]
						# 注意：如果 ext_plugin 已经是模块名格式（如 nonebot_plugin_alconna），直接使用
						if ext_plugin.startswith("nonebot_plugin_"):
							# 已经是模块名格式，直接使用
							module_name = ext_plugin
						else:
							# 从插件名转换为模块名
							module_name = ext_plugin.replace("nonebot-plugin-", "nonebot_plugin_").replace("-", "_")
						
						# 尝试多种可能的模块名格式
						alt_module_names = [
							ext_plugin,  # 直接使用原始名称（如果已经是模块名）
							module_name,  # nonebot_plugin_anans_sketchbook
							ext_plugin.replace("-", "_"),  # nonebot-plugin-anans-sketchbook -> nonebot_plugin_anans_sketchbook
							ext_plugin.replace("nonebot-plugin-", "").replace("-", "_"),  # anans_sketchbook
							f"nonebot_plugin_{ext_plugin.replace('nonebot-plugin-', '').replace('-', '_')}",  # nonebot_plugin_anans_sketchbook
						]
						# 去重
						alt_module_names = list(dict.fromkeys(alt_module_names))
						
						for alt_name in alt_module_names:
							try:
								load_plugin(alt_name)
								logger.info(f"✅ 已加载外部插件: {ext_plugin} (模块: {alt_name})")
								loaded = True
								break
							except Exception as load_error:
								logger.debug(f"尝试加载 {ext_plugin} 为 {alt_name} 失败: {load_error}")
								continue
						
						if not loaded:
							logger.error(f"❌ 无法加载外部插件 {ext_plugin}，已尝试所有可能的模块名: {alt_module_names}")
			
			# 获取已加载的插件
			loaded = get_loaded_plugins()
			logger.info(f"已加载的插件列表: {[p.name for p in loaded]}")
			logger.info(f"启用的插件列表: {enabled_plugins}")
			
			for plugin in loaded:
				plugin_name = plugin.name
				# NoneBot插件名称可能是完整路径，需要提取文件名部分
				# 例如: "src.plugins.example_plugin" -> "example_plugin"
				simple_name = plugin_name.split(".")[-1] if "." in plugin_name else plugin_name
				
				# 检查插件是否启用（支持完整名称和简单名称）
				# 对于外部插件，需要检查多种可能的名称格式
				is_enabled = False
				
				# 检查完整名称匹配
				if plugin_name in enabled_plugins:
					is_enabled = True
				# 检查简单名称匹配
				elif simple_name in enabled_plugins:
					is_enabled = True
				# 检查完整路径匹配（如果插件名是简单名称，但启用列表中是完整路径）
				elif f"src.plugins.{simple_name}" in enabled_plugins:
					is_enabled = True
				# 检查完整路径匹配（如果插件名是完整路径，但启用列表中是简单名称）
				elif plugin_name.startswith("src.plugins.") and simple_name in enabled_plugins:
					is_enabled = True
				# 对于外部插件，检查模块名匹配（如 nonebot_plugin_anans_sketchbook）
				elif any(ep in plugin_name or plugin_name in ep for ep in enabled_plugins if not ep.startswith("src.plugins.")):
					is_enabled = True
				# 检查插件名称是否包含外部插件名称（如 nonebot-plugin-anans-sketchbook）
				elif any(ep.replace("-", "_") in plugin_name or ep.replace("-", "_") in simple_name for ep in enabled_plugins if not ep.startswith("src.plugins.")):
					is_enabled = True
				
				# 调试：打印匹配信息
				logger.debug(f"插件匹配检查: plugin_name={plugin_name}, simple_name={simple_name}, enabled_plugins={enabled_plugins}")
				logger.debug(f"  完整名称匹配: {plugin_name in enabled_plugins}")
				logger.debug(f"  简单名称匹配: {simple_name in enabled_plugins}")
				logger.debug(f"  完整路径匹配: {f'src.plugins.{simple_name}' in enabled_plugins}")
				logger.debug(f"  最终启用状态: {is_enabled}")
				
				if is_enabled:
					self.loaded_plugins[plugin_name] = plugin
					await self._update_plugin_status(plugin_name, "enabled")
					logger.info(f"插件 {plugin_name} ({simple_name}) 已加载并启用")
				else:
					# 插件未启用，标记状态
					# 注意：NoneBot 已经加载了插件，所以命令处理器仍然会工作
					# 这里只是标记状态，不影响插件的实际运行
					await self._update_plugin_status(plugin_name, "disabled")
					logger.warning(f"插件 {plugin_name} ({simple_name}) 已加载但未启用 (不在启用列表中: {enabled_plugins})")
					logger.warning(f"  提示：NoneBot 已加载插件，命令处理器仍会工作，但建议在配置文件中启用插件")
			
			logger.info(f"插件加载完成，共加载 {len(self.loaded_plugins)} 个启用的插件")
		except Exception as e:
			logger.error(f"加载插件失败: {e}", exc_info=True)
			raise
	
	def _auto_migrate_external_plugins(self, enabled_plugins: List[str]) -> List[str]:
		"""将 enabled 中的外部插件（非 src.plugins.*）自动迁移到本地。
		
		目的：避免 third-party 插件内部 require("src.plugins.xxx") 但本地不存在时导致启动报错。
		策略：
		- 只迁移“已安装且可 find_spec 的外部插件”；不会在启动时 pip install。
		- 迁移成功后写回 `configs/config.yaml`，把 enabled 条目替换为 `src.plugins.<local>`。
		"""
		try:
			project_root = Path(__file__).parent.parent.parent
			config_path = project_root / "configs" / "config.yaml"
			plugins_dir = project_root / "src" / "plugins"
			
			# 延迟导入：此时 NoneBot 已初始化（on_startup），不会触发 "not initialized" 问题
			from src.plugins.migrate_plugin import copy_plugin_to_local
		except Exception as e:
			logger.debug(f"自动迁移外部插件初始化失败，跳过: {e}")
			return enabled_plugins
		
		# 读取现有配置（尽量只改 enabled 列表）
		try:
			import yaml
			if config_path.exists():
				with open(config_path, "r", encoding="utf-8") as f:
					config = yaml.safe_load(f) or {}
			else:
				config = {}
		except Exception as e:
			logger.debug(f"读取 config.yaml 失败，跳过自动迁移: {e}")
			return enabled_plugins
		
		enabled_list = (config.get("plugins", {}) or {}).get("enabled", [])
		if not isinstance(enabled_list, list):
			return enabled_plugins
		
		updated_enabled = list(enabled_plugins)
		changed = False
		
		def _to_module_and_package(name: str) -> tuple[str, str]:
			# name 可能是 module（nonebot_plugin_xxx）也可能是 package（nonebot-plugin-xxx）
			if name.startswith("nonebot_plugin_"):
				module = name
				package = name.replace("_", "-")
			elif name.startswith("nonebot-plugin-"):
				package = name
				module = name.replace("nonebot-plugin-", "nonebot_plugin_").replace("-", "_")
			else:
				module = name
				package = name.replace("_", "-")
			return module, package
		
		def _local_name_from_package(pkg: str) -> str:
			# copy_plugin_to_local 内部使用 plugin_name.replace("nonebot-plugin-", "").replace("-", "_")
			# 这里保持一致，保证 config 里写入的 local path 与实际目录匹配
			if pkg.startswith("nonebot-plugin-"):
				base = pkg.replace("nonebot-plugin-", "")
			else:
				base = pkg
			return base.replace("-", "_")
		
		for name in list(enabled_plugins):
			if name.startswith("src.plugins.") or name.startswith("src/plugins/"):
				continue
			
			module_name, package_name = _to_module_and_package(name)
			
			# 已经有本地同名插件目录则跳过（避免循环迁移）
			local_dir_guess = plugins_dir / _local_name_from_package(package_name)
			if local_dir_guess.exists():
				continue
			
			# 仅迁移已安装模块
			try:
				if not importlib.util.find_spec(module_name):
					continue
			except Exception:
				continue
			
			try:
				ok, local_plugin_path, err = copy_plugin_to_local(module_name, package_name)
				if not ok or not local_plugin_path:
					logger.warning(f"自动迁移外部插件失败: {name} -> {err}")
					continue
			except Exception as e:
				logger.warning(f"自动迁移外部插件异常: {name} -> {e}")
				continue
			
			# 更新 enabled：移除外部写法（module/package），添加本地写法
			candidates_to_remove = {
				name,
				module_name,
				package_name,
				package_name.lower(),
				module_name.lower(),
			}
			enabled_list = [p for p in enabled_list if str(p) not in candidates_to_remove]
			if local_plugin_path not in enabled_list:
				enabled_list.append(local_plugin_path)
			
			updated_enabled = [p for p in updated_enabled if p not in candidates_to_remove]
			if local_plugin_path not in updated_enabled:
				updated_enabled.append(local_plugin_path)
			
			logger.info(f"✅ 外部插件已自动迁移为本地插件: {name} -> {local_plugin_path}")
			changed = True
		
		if changed:
			try:
				config.setdefault("plugins", {})
				config["plugins"]["enabled"] = enabled_list
				with open(config_path, "w", encoding="utf-8") as f:
					yaml.safe_dump(config, f, allow_unicode=True, sort_keys=False)
			except Exception as e:
				logger.warning(f"写回 config.yaml 失败（但本次运行已使用内存中的启用列表）: {e}")
		
		return updated_enabled
	
	def _scan_plugin_dir(self) -> List[Path]:
		"""
		扫描插件目录
		
		Returns:
			插件文件列表
		"""
		plugin_files = []
		
		if not self.plugin_dir.exists():
			return plugin_files
		
		for file_path in self.plugin_dir.rglob("*.py"):
			# 跳过__init__.py和隐藏文件
			if file_path.name.startswith("_") or file_path.name == "__init__.py":
				continue
			plugin_files.append(file_path)
		
		return plugin_files
	
	async def _get_enabled_plugins(self) -> List[str]:
		"""
		获取启用的插件列表
		优先级：配置文件 > 数据库
		
		Returns:
			启用的插件名称列表
		"""
		enabled_plugins = []
		
		# 1. 优先从配置文件读取
		if self.plugins_config:
			use_config_file = getattr(self.plugins_config, 'use_config_file', True)
			logger.debug(f"use_config_file: {use_config_file}")
			logger.debug(f"plugins_config 对象: {self.plugins_config}")
			
			if use_config_file:
				config_enabled = getattr(self.plugins_config, 'enabled', []) or []
				config_disabled = getattr(self.plugins_config, 'disabled', []) or []
				
				logger.info(f"配置文件 enabled: {config_enabled} (类型: {type(config_enabled)})")
				logger.info(f"配置文件 disabled: {config_disabled}")
				
				# 从启用的插件列表中移除禁用的插件
				enabled_plugins = [p for p in config_enabled if p not in config_disabled]
				
				if enabled_plugins:
					logger.info(f"从配置文件读取到 {len(enabled_plugins)} 个启用的插件: {enabled_plugins}")
					return enabled_plugins
				else:
					logger.warning(f"配置文件中的 enabled 列表为空或全部被 disabled 禁用 (enabled: {config_enabled}, disabled: {config_disabled})")
			else:
				logger.info("use_config_file=False，跳过配置文件，使用数据库")
		else:
			logger.warning("plugins_config 未传入，无法从配置文件读取")
		
		# 2. 如果配置文件没有配置，从数据库读取
		if self.db_manager:
			try:
				async with self.db_manager.get_session() as session:
					configs = await PluginConfig.get_all_enabled(session)
					db_enabled = [config.plugin_name for config in configs]
					if db_enabled:
						logger.info(f"从数据库读取到 {len(db_enabled)} 个启用的插件: {db_enabled}")
						return db_enabled
			except Exception as e:
				logger.error(f"从数据库获取启用的插件列表失败: {e}")
		
		# 3. 如果都没有配置，返回空列表（所有插件禁用）
		if not enabled_plugins:
			logger.info("未找到启用的插件配置（配置文件或数据库）")
		
		return enabled_plugins
	
	async def _update_plugin_status(self, plugin_name: str, status: str, error_message: Optional[str] = None):
		"""
		更新插件状态
		
		Args:
			plugin_name: 插件名称
			status: 状态（loaded, enabled, disabled, error）
			error_message: 错误信息（可选）
		"""
		if not self.db_manager:
			return
		
		try:
			async with self.db_manager.get_session() as session:
				await PluginStatus.update_status(session, plugin_name, status, error_message)
		except Exception as e:
			logger.error(f"更新插件状态失败: {e}")
	
	async def enable_plugin(self, plugin_name: str) -> bool:
		"""
		启用插件
		
		Args:
			plugin_name: 插件名称
			
		Returns:
			是否成功
		"""
		try:
			if not self.db_manager:
				logger.error("数据库管理器未初始化，无法启用插件")
				return False
			
			async with self.db_manager.get_session() as session:
				# 更新数据库配置
				await PluginConfig.create_or_update(session, plugin_name, enabled=True)
				await self._update_plugin_status(plugin_name, "enabled")
			
			logger.info(f"插件 {plugin_name} 已启用")
			return True
		except Exception as e:
			logger.error(f"启用插件失败: {e}", exc_info=True)
			return False
	
	async def disable_plugin(self, plugin_name: str) -> bool:
		"""
		禁用插件
		
		Args:
			plugin_name: 插件名称
			
		Returns:
			是否成功
		"""
		try:
			if not self.db_manager:
				logger.error("数据库管理器未初始化，无法禁用插件")
				return False
			
			async with self.db_manager.get_session() as session:
				# 更新数据库配置
				await PluginConfig.create_or_update(session, plugin_name, enabled=False)
				await self._update_plugin_status(plugin_name, "disabled")
			
			logger.info(f"插件 {plugin_name} 已禁用")
			return True
		except Exception as e:
			logger.error(f"禁用插件失败: {e}", exc_info=True)
			return False
	
	async def get_plugin_config(self, plugin_name: str) -> Optional[Dict[str, Any]]:
		"""
		获取插件配置
		
		Args:
			plugin_name: 插件名称
			
		Returns:
			插件配置字典，如果不存在返回None
		"""
		if not self.db_manager:
			return None
		
		try:
			async with self.db_manager.get_session() as session:
				config = await PluginConfig.get_by_name(session, plugin_name)
				if config:
					return config.to_dict()
				return None
		except Exception as e:
			logger.error(f"获取插件配置失败: {e}")
			return None
	
	async def update_plugin_config(self, plugin_name: str, config_data: Dict[str, Any]) -> bool:
		"""
		更新插件配置
		
		Args:
			plugin_name: 插件名称
			config_data: 配置数据
			
		Returns:
			是否成功
		"""
		if not self.db_manager:
			logger.error("数据库管理器未初始化，无法更新插件配置")
			return False
		
		try:
			async with self.db_manager.get_session() as session:
				config = await PluginConfig.get_by_name(session, plugin_name)
				if config:
					await PluginConfig.create_or_update(session, plugin_name, enabled=config.enabled, config_data=config_data)
				else:
					await PluginConfig.create_or_update(session, plugin_name, enabled=True, config_data=config_data)
			
			logger.info(f"插件 {plugin_name} 配置已更新")
			return True
		except Exception as e:
			logger.error(f"更新插件配置失败: {e}", exc_info=True)
			return False


			
			logger.info(f"插件 {plugin_name} 已禁用")
			return True
		except Exception as e:
			logger.error(f"禁用插件失败: {e}", exc_info=True)
			return False
	
	async def get_plugin_config(self, plugin_name: str) -> Optional[Dict[str, Any]]:
		"""
		获取插件配置
		
		Args:
			plugin_name: 插件名称
			
		Returns:
			插件配置字典，如果不存在返回None
		"""
		if not self.db_manager:
			return None
		
		try:
			async with self.db_manager.get_session() as session:
				config = await PluginConfig.get_by_name(session, plugin_name)
				if config:
					return config.to_dict()
				return None
		except Exception as e:
			logger.error(f"获取插件配置失败: {e}")
			return None
	
	async def update_plugin_config(self, plugin_name: str, config_data: Dict[str, Any]) -> bool:
		"""
		更新插件配置
		
		Args:
			plugin_name: 插件名称
			config_data: 配置数据
			
		Returns:
			是否成功
		"""
		if not self.db_manager:
			logger.error("数据库管理器未初始化，无法更新插件配置")
			return False
		
		try:
			async with self.db_manager.get_session() as session:
				config = await PluginConfig.get_by_name(session, plugin_name)
				if config:
					await PluginConfig.create_or_update(session, plugin_name, enabled=config.enabled, config_data=config_data)
				else:
					await PluginConfig.create_or_update(session, plugin_name, enabled=True, config_data=config_data)
			
			logger.info(f"插件 {plugin_name} 配置已更新")
			return True
		except Exception as e:
			logger.error(f"更新插件配置失败: {e}", exc_info=True)
			return False
	
	async def _log_plugin_config(self, plugin_name: str, simple_name: str):
		"""
		在日志中输出插件的配置信息
		
		Args:
			plugin_name: 插件完整名称
			simple_name: 插件简单名称
		"""
		try:
			import yaml
			from pathlib import Path
			
			# 获取配置文件路径
			project_root = Path(__file__).parent.parent.parent
			config_path = project_root / "configs" / "config.yaml"
			
			if not config_path.exists():
				return
			
			# 加载配置文件
			with open(config_path, "r", encoding="utf-8") as f:
				config = yaml.safe_load(f) or {}
			
			# 获取插件配置键名（移除常见前缀）
			config_key = simple_name.replace("nonebot_plugin_", "").replace("nonebot-plugin-", "").replace("-", "_")
			
			# 尝试多种可能的配置键名
			possible_keys = [
				config_key,
				simple_name,
				plugin_name.split(".")[-1] if "." in plugin_name else plugin_name,
				plugin_name.replace(".", "_").replace("-", "_"),
			]
			
			plugin_config = None
			used_key = None
			
			for key in possible_keys:
				if key in config:
					plugin_config = config[key]
					used_key = key
					break
			
			# 如果找到了配置，输出到日志
			if plugin_config and isinstance(plugin_config, dict):
				# 过滤掉 enabled 等元数据字段，只显示实际配置
				config_items = {k: v for k, v in plugin_config.items() if k != "enabled" or len(plugin_config) == 1}
				
				if config_items:
					# 格式化配置值
					formatted_items = []
					for k, v in config_items.items():
						if isinstance(v, bool):
							formatted_value = "开启" if v else "关闭"
						elif isinstance(v, list):
							if not v:
								formatted_value = "[]"
							else:
								formatted_value = ", ".join([str(item) for item in v])
						else:
							formatted_value = str(v)
						formatted_items.append(f"  {k}: {formatted_value}")
					
					config_str = "\n".join(formatted_items)
					logger.info(f"📋 插件 {simple_name} 的配置 ({used_key}):\n{config_str}")
				else:
					logger.debug(f"插件 {simple_name} 的配置节点 {used_key} 存在但为空")
			else:
				# 尝试通过 get_plugin_config 获取（如果插件支持）
				try:
					import importlib.util
					
					# 尝试查找插件模块
					spec = importlib.util.find_spec(plugin_name)
					if spec and spec.origin:
						# 尝试导入插件模块的 config 子模块
						try:
							config_module_name = f"{plugin_name}.config"
							config_module = importlib.import_module(config_module_name)
							if hasattr(config_module, "plugin_config"):
								plugin_config_obj = config_module.plugin_config
								# 尝试获取配置值
								if hasattr(plugin_config_obj, "model_dump"):
									config_dict = plugin_config_obj.model_dump()
								elif hasattr(plugin_config_obj, "dict"):
									config_dict = plugin_config_obj.dict()
								else:
									config_dict = {}
								
								if config_dict:
									formatted_items = []
									for k, v in config_dict.items():
										if isinstance(v, bool):
											formatted_value = "开启" if v else "关闭"
										elif isinstance(v, list):
											formatted_value = ", ".join([str(item) for item in v]) if v else "[]"
										else:
											formatted_value = str(v)
										formatted_items.append(f"  {k}: {formatted_value}")
									
									if formatted_items:
										config_str = "\n".join(formatted_items)
										logger.info(f"📋 插件 {simple_name} 的配置 (从插件获取):\n{config_str}")
						except ImportError:
							# 插件没有 config 子模块，跳过
							pass
						except Exception as e:
							logger.debug(f"获取插件 {simple_name} 配置时出错: {e}")
				except Exception as e:
					logger.debug(f"尝试获取插件 {simple_name} 配置时出错: {e}")
		except Exception as e:
			logger.debug(f"输出插件 {simple_name} 配置信息时出错: {e}")

