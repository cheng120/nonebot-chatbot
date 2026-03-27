"""
通用插件配置管理
支持为任何插件动态配置参数
"""
import yaml
import ast
import importlib.util
from pathlib import Path
from typing import Optional, Dict, Any, List, Union, Tuple
from nonebot import on_command, get_loaded_plugins
from nonebot.adapters.onebot.v11 import MessageEvent, Message
from nonebot.params import CommandArg
from nonebot.plugin import PluginMetadata
from src.utils.logger import get_logger

__plugin_meta__ = PluginMetadata(
	name="插件配置管理",
	description="通用插件配置管理，支持为任何插件动态配置参数",
	usage="""
可用命令：
- /plugin_config - 查看所有插件的配置
- /plugin_config <插件名> - 查看指定插件的配置
- /plugin_config <插件名> set <参数名> <值> - 设置插件配置参数
- /plugin_config <插件名> get <参数名> - 查看指定参数的值

示例：
- /plugin_config pokemonle - 查看宝可梦插件的配置
- /plugin_config pokemonle set pokemonle_max_attempts 5 - 设置最大尝试次数
- /plugin_config pokemonle set pokemonle_gens 1,3,5 - 设置世代选择
- /plugin_config pokemonle set pokemonle_cheat true - 开启恶作剧
	""",
	type="application",
	homepage="https://github.com/your-username/nonebot-chatbot",
	supported_adapters={"~onebot.v11"},
)

logger = get_logger("plugin_config_manager")

# 配置文件路径
CONFIG_PATH = Path(__file__).parent.parent.parent / "configs" / "config.yaml"


def get_config_path() -> Path:
	"""获取配置文件路径"""
	return CONFIG_PATH


def load_yaml_config() -> dict:
	"""加载 YAML 配置"""
	try:
		with open(get_config_path(), "r", encoding="utf-8") as f:
			return yaml.safe_load(f) or {}
	except Exception as e:
		logger.error(f"加载配置文件失败: {e}")
		return {}


def save_yaml_config(config: dict) -> bool:
	"""保存 YAML 配置"""
	try:
		with open(get_config_path(), "w", encoding="utf-8") as f:
			yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
		logger.info(f"配置文件已保存: {get_config_path()}")
		return True
	except Exception as e:
		logger.error(f"保存配置文件失败: {e}")
		return False


def detect_plugin_config_fields(module_name: str) -> Optional[Dict[str, Dict[str, Any]]]:
	"""
	检测插件的配置字段
	支持从主模块和子模块（如 config.py）中查找 Config 类
	
	Args:
		module_name: 插件模块名称
		
	Returns:
		配置字段字典，格式: {字段名: {"type": 类型, "default": 默认值}}
	"""
	try:
		spec = importlib.util.find_spec(module_name)
		if not spec or not spec.origin:
			return None
		
		plugin_file = Path(spec.origin)
		if not plugin_file.exists():
			return None
		
		# 确定插件目录
		if plugin_file.is_file():
			plugin_dir = plugin_file.parent
		else:
			plugin_dir = plugin_file
		
		# 要检查的文件列表（优先检查 config.py，然后检查主文件）
		files_to_check = []
		
		# 1. 优先检查 config.py
		config_file = plugin_dir / "config.py"
		if config_file.exists():
			files_to_check.append(config_file)
		
		# 2. 检查主模块文件
		if plugin_file.is_file() and plugin_file not in files_to_check:
			files_to_check.append(plugin_file)
		
		# 3. 检查 __init__.py
		init_file = plugin_dir / "__init__.py"
		if init_file.exists() and init_file not in files_to_check:
			files_to_check.append(init_file)
		
		# 4. 如果都没找到，检查目录下的所有 .py 文件
		if not files_to_check:
			files_to_check = list(plugin_dir.glob("*.py"))
		
		# 遍历所有文件查找 Config 类
		for file_path in files_to_check:
			if not file_path.exists():
				continue
			
			try:
				with open(file_path, "r", encoding="utf-8") as f:
					code = f.read()
				
				tree = ast.parse(code)
				config_fields = {}
				
				for node in ast.walk(tree):
					if isinstance(node, ast.ClassDef):
						# 检查是否是 Config 类（必须是 BaseModel 的子类或包含配置字段）
						is_config_class = False
						
						# 检查类名
						if "Config" in node.name:
							is_config_class = True
						
						# 检查基类（是否继承自 BaseModel）
						for base in node.bases:
							if isinstance(base, ast.Name):
								if base.id in ("BaseModel", "Config"):
									is_config_class = True
									break
						
						if is_config_class:
							for item in node.body:
								if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
									field_name = item.target.id
									
									# 获取类型注解
									type_str = "Any"
									if item.annotation:
										try:
											if hasattr(ast, 'unparse'):
												type_str = ast.unparse(item.annotation)
											else:
												# Python < 3.9 兼容
												if isinstance(item.annotation, ast.Name):
													type_str = item.annotation.id
												elif isinstance(item.annotation, ast.Subscript):
													if isinstance(item.annotation.value, ast.Name):
														type_str = item.annotation.value.id
													# 处理 list[int] 等类型
													if isinstance(item.annotation.slice, ast.Name):
														type_str = f"{type_str}[{item.annotation.slice.id}]"
													elif isinstance(item.annotation.slice, ast.Index):
														if isinstance(item.annotation.slice.value, ast.Name):
															type_str = f"{type_str}[{item.annotation.slice.value.id}]"
										except:
											pass
									
									# 获取默认值
									default_value = None
									if item.value:
										try:
											if isinstance(item.value, ast.Constant):
												default_value = item.value.value
											elif isinstance(item.value, ast.Str):
												default_value = item.value.s
											elif isinstance(item.value, ast.NameConstant):
												default_value = item.value.value
											elif isinstance(item.value, ast.List):
												# 解析列表默认值
												default_value = []
												for elt in item.value.elts:
													if isinstance(elt, ast.Constant):
														default_value.append(elt.value)
													elif isinstance(elt, ast.Str):
														default_value.append(elt.s)
													elif isinstance(elt, ast.NameConstant):
														default_value.append(elt.value)
											elif isinstance(item.value, ast.Dict):
												default_value = {}
										except:
											pass
									
									config_fields[field_name] = {
										"type": type_str,
										"default": default_value
									}
							
							if config_fields:
								logger.info(f"检测到插件 {module_name} 的配置字段 (文件: {file_path.name}): {list(config_fields.keys())}")
								return config_fields
			except Exception as e:
				logger.debug(f"解析文件 {file_path} 时出错: {e}")
				continue
		
		logger.warning(f"插件 {module_name} 未找到 Config 类定义")
		return None
	except Exception as e:
		logger.warning(f"检测插件 {module_name} 配置时出错: {e}")
	
	return None


def get_plugin_config_key(plugin_name: str) -> str:
	"""
	获取插件在 config.yaml 中的配置键名
	
	Args:
		plugin_name: 插件名称（如 nonebot_plugin_pokemonle 或 pokemonle）
		
	Returns:
		配置键名（如 pokemonle）
	"""
	# 移除常见前缀
	name = plugin_name.replace("nonebot_plugin_", "").replace("nonebot-plugin-", "")
	# 转换为下划线格式
	name = name.replace("-", "_")
	return name


def get_plugin_current_config(plugin_name: str) -> Dict[str, Any]:
	"""
	获取插件的当前配置
	
	Args:
		plugin_name: 插件名称
		
	Returns:
		当前配置字典
	"""
	config = load_yaml_config()
	config_key = get_plugin_config_key(plugin_name)
	plugin_config = config.get(config_key, {})
	return plugin_config


def update_plugin_config(plugin_name: str, key: str, value: Any) -> bool:
	"""
	更新插件配置
	
	Args:
		plugin_name: 插件名称
		key: 配置键名
		value: 配置值
		
	Returns:
		是否成功
	"""
	config = load_yaml_config()
	config_key = get_plugin_config_key(plugin_name)
	
	# 确保插件配置节点存在
	if config_key not in config:
		config[config_key] = {}
	
	# 更新配置值
	config[config_key][key] = value
	
	# 保存配置
	return save_yaml_config(config)


def parse_config_value(value_str: str, field_type: str, default_value: Any) -> Tuple[bool, Any, str]:
	"""
	解析配置值字符串
	
	Args:
		value_str: 值字符串
		field_type: 字段类型
		default_value: 默认值（用于推断类型）
		
	Returns:
		(是否成功, 解析后的值, 错误信息)
	"""
	try:
		# 根据类型解析
		if "int" in field_type.lower() or isinstance(default_value, int):
			try:
				value = int(value_str)
				return True, value, ""
			except ValueError:
				return False, None, f"❌ 值必须是整数: {value_str}"
		
		elif "bool" in field_type.lower() or isinstance(default_value, bool):
			value = value_str.lower() in ("true", "1", "yes", "开启", "on", "enable", "enabled")
			return True, value, ""
		
		elif "list" in field_type.lower() or isinstance(default_value, list):
			# 尝试解析为列表（逗号分隔）
			items = [item.strip() for item in value_str.split(",")]
			# 如果默认值是数字列表，尝试转换
			if default_value and isinstance(default_value[0], int) if default_value else False:
				try:
					value = [int(item) for item in items if item]
				except ValueError:
					# 如果转换失败，保持字符串列表
					value = items
			else:
				value = items
			return True, value, ""
		
		elif "str" in field_type.lower() or isinstance(default_value, str):
			return True, value_str, ""
		
		else:
			# 默认尝试 JSON 解析
			try:
				import json
				value = json.loads(value_str)
				return True, value, ""
			except:
				# 如果 JSON 解析失败，作为字符串
				return True, value_str, ""
	except Exception as e:
		return False, None, f"❌ 解析值失败: {str(e)}"


def format_config_value(value: Any) -> str:
	"""格式化配置值用于显示"""
	if isinstance(value, bool):
		return "开启" if value else "关闭"
	elif isinstance(value, list):
		if not value:
			return "[]"
		return ", ".join([str(v) for v in value])
	else:
		return str(value)


# 配置管理命令
config_cmd = on_command("plugin_config", aliases={"插件配置", "配置管理"}, priority=10, block=True)


@config_cmd.handle()
async def handle_config(event: MessageEvent, args: Message = CommandArg()):
	"""处理配置命令"""
	arg_str = str(args).strip()
	
	if not arg_str:
		# 显示所有已加载的插件
		try:
			plugins = get_loaded_plugins()
			plugin_list = [p.name.split(".")[-1] for p in plugins]
			
			help_text = f"""
📋 已加载的插件列表（共 {len(plugin_list)} 个）

{', '.join(plugin_list[:20])}
{"..." if len(plugin_list) > 20 else ""}

💡 使用 /plugin_config <插件名> 查看插件配置
💡 使用 /plugin_config <插件名> set <参数名> <值> 设置配置
			""".strip()
			
			await config_cmd.send(help_text)
		except Exception as e:
			logger.error(f"获取插件列表失败: {e}")
			await config_cmd.send("❌ 获取插件列表失败")
		return
	
	# 解析命令
	parts = arg_str.split(None, 2)
	plugin_name = parts[0]
	
	# 尝试查找插件模块
	module_name = None
	
	# 方法1: 从已加载的插件中查找
	try:
		plugins = get_loaded_plugins()
		for plugin in plugins:
			plugin_full_name = plugin.name
			plugin_simple_name = plugin_full_name.split(".")[-1]
			
			# 精确匹配
			if plugin_full_name == plugin_name or plugin_simple_name == plugin_name:
				module_name = plugin_full_name
				break
			# 包含匹配
			elif plugin_name in plugin_full_name or plugin_name in plugin_simple_name:
				module_name = plugin_full_name
				break
			# 处理下划线和连字符的转换
			elif plugin_name.replace("-", "_") == plugin_simple_name.replace("-", "_"):
				module_name = plugin_full_name
				break
	except Exception as e:
		logger.debug(f"从已加载插件中查找失败: {e}")
	
	# 方法2: 如果没找到，尝试直接使用插件名查找模块
	if not module_name:
		# 尝试常见的模块名格式
		possible_names = [
			plugin_name,
			f"nonebot_plugin_{plugin_name}",
			plugin_name.replace("-", "_"),
			f"src.plugins.{plugin_name}",
		]
		
		# 如果插件名已经是简化形式，尝试添加前缀
		if not plugin_name.startswith("nonebot_plugin_") and not plugin_name.startswith("nonebot-plugin-"):
			possible_names.insert(1, f"nonebot_plugin_{plugin_name.replace('-', '_')}")
		
		for name in possible_names:
			try:
				spec = importlib.util.find_spec(name)
				if spec and spec.origin:
					module_name = name
					logger.info(f"找到插件模块: {name} (路径: {spec.origin})")
					break
			except Exception as e:
				logger.debug(f"查找模块 {name} 失败: {e}")
				continue
	
	if not module_name:
		# 提供更详细的错误信息
		try:
			plugins = get_loaded_plugins()
			plugin_list = [p.name.split(".")[-1] for p in plugins]
			similar = [p for p in plugin_list if plugin_name.lower() in p.lower() or p.lower() in plugin_name.lower()]
			
			error_msg = f"❌ 未找到插件: {plugin_name}"
			if similar:
				error_msg += f"\n💡 相似的插件: {', '.join(similar[:5])}"
			else:
				error_msg += f"\n💡 已加载的插件: {', '.join(plugin_list[:10])}"
			error_msg += "\n💡 提示: 使用 /plugin_config 查看所有插件"
			
			await config_cmd.send(error_msg)
		except:
			await config_cmd.send(f"❌ 未找到插件: {plugin_name}\n💡 请使用已加载的插件名称")
		return
	
	logger.info(f"找到插件模块: {module_name}，开始检测配置字段...")
	
	# 检测配置字段
	config_fields = detect_plugin_config_fields(module_name)
	
	if not config_fields:
		# 提供更详细的错误信息
		error_msg = f"⚠️ 插件 {plugin_name} (模块: {module_name}) 未检测到配置字段"
		error_msg += "\n\n可能的原因："
		error_msg += "\n1. 插件使用不同的配置方式（如环境变量）"
		error_msg += "\n2. Config 类不在标准位置（config.py 或 __init__.py）"
		error_msg += "\n3. 插件不需要额外配置"
		error_msg += "\n\n💡 提示: 可以手动在 config.yaml 中添加配置"
		
		await config_cmd.send(error_msg)
		return
	
	# 获取当前配置
	current_config = get_plugin_current_config(plugin_name)
	
	# 处理子命令
	if len(parts) == 1:
		# 显示当前配置
		config_text = f"📋 插件 {plugin_name} 的配置\n\n"
		
		for field_name, field_info in config_fields.items():
			current_value = current_config.get(field_name, field_info["default"])
			default_str = f" (默认: {format_config_value(field_info['default'])})" if field_info["default"] is not None else ""
			config_text += f"• {field_name}: {format_config_value(current_value)}{default_str}\n"
			config_text += f"  类型: {field_info['type']}\n\n"
		
		config_text += "💡 使用 /plugin_config <插件名> set <参数名> <值> 来修改配置\n"
		config_text += "⚠️ 注意: 修改配置后需要重启机器人才能生效"
		
		await config_cmd.send(config_text)
	
	elif len(parts) >= 2:
		subcommand = parts[1].lower()
		
		if subcommand == "set" and len(parts) >= 3:
			# 设置配置: /plugin_config <插件名> set <参数名> <值>
			params = parts[2].split(None, 1)
			if len(params) < 2:
				await config_cmd.send(f"❌ 用法: /plugin_config {plugin_name} set <参数名> <值>\n示例: /plugin_config {plugin_name} set {list(config_fields.keys())[0]} <值>")
				return
			
			key = params[0]
			value_str = params[1]
			
			# 检查参数是否存在
			if key not in config_fields:
				available_keys = ", ".join(config_fields.keys())
				await config_cmd.send(f"❌ 未知的配置参数: {key}\n可用参数: {available_keys}")
				return
			
			# 解析值
			field_info = config_fields[key]
			success, value, error_msg = parse_config_value(value_str, field_info["type"], field_info["default"])
			
			if not success:
				await config_cmd.send(error_msg)
				return
			
			# 更新配置
			if update_plugin_config(plugin_name, key, value):
				await config_cmd.send(f"✅ 配置已更新: {key} = {format_config_value(value)}\n⚠️ 请重启机器人使配置生效")
			else:
				await config_cmd.send("❌ 配置更新失败，请查看日志")
		
		elif subcommand == "get" and len(parts) >= 3:
			# 获取配置: /plugin_config <插件名> get <参数名>
			key = parts[2]
			
			if key not in config_fields:
				available_keys = ", ".join(config_fields.keys())
				await config_cmd.send(f"❌ 未知的配置参数: {key}\n可用参数: {available_keys}")
				return
			
			current_value = current_config.get(key, config_fields[key]["default"])
			default_str = f" (默认: {format_config_value(config_fields[key]['default'])})" if config_fields[key]["default"] is not None else ""
			
			await config_cmd.send(f"📋 {key}: {format_config_value(current_value)}{default_str}")
		
		else:
			available_keys = ", ".join(config_fields.keys())
			await config_cmd.send(f"""
❌ 未知的子命令: {subcommand}

可用命令：
• /plugin_config {plugin_name} - 查看所有配置
• /plugin_config {plugin_name} set <参数名> <值> - 设置配置
• /plugin_config {plugin_name} get <参数名> - 查看指定参数

可用参数: {available_keys}
			""".strip())

