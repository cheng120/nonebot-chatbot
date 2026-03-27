"""
命令收集器
用于收集所有已加载插件的命令信息
"""
from typing import Dict, List, Tuple, Optional, Any
from nonebot import get_loaded_plugins
from nonebot.plugin import Plugin
from nonebot.matcher import Matcher
from nonebot.log import logger
import inspect
import ast
from pathlib import Path

def get_all_plugin_commands() -> Dict[str, List[Dict[str, Any]]]:
	"""
	获取所有已加载插件的命令信息
	
	Returns:
		字典，键为插件名称，值为命令列表
		每个命令包含: name, aliases, description, plugin_name
	"""
	commands_by_plugin: Dict[str, List[Dict[str, Any]]] = {}
	
	try:
		plugins = get_loaded_plugins()
		logger.debug(f"发现 {len(plugins)} 个已加载的插件")
		
		for plugin in plugins:
			plugin_name = plugin.name
			plugin_commands = []
			
			# 获取插件模块
			try:
				plugin_module = plugin.module
				if not plugin_module:
					continue
				
				# 方法1: 从模块源代码中解析命令（更可靠）
				module_file = getattr(plugin_module, "__file__", None)
				if module_file:
					file_path = Path(module_file)
					if file_path.exists() and file_path.suffix == ".py":
						commands_from_source = _parse_commands_from_source(file_path, plugin_name)
						plugin_commands.extend(commands_from_source)
				
				# 方法2: 从模块属性中查找 Matcher（备用）
				for attr_name in dir(plugin_module):
					# 跳过私有属性和特殊属性
					if attr_name.startswith("_") or attr_name in ["__builtins__", "__cached__", "__file__", "__loader__", "__name__", "__package__", "__spec__"]:
						continue
					
					try:
						attr = getattr(plugin_module, attr_name)
						
						# 检查是否是 Matcher 实例（命令处理器）
						if isinstance(attr, Matcher):
							# 获取命令信息
							cmd_info = _extract_command_info_from_matcher(attr, attr_name, plugin_name)
							if cmd_info and not any(cmd["name"] == cmd_info["name"] for cmd in plugin_commands):
								plugin_commands.append(cmd_info)
					except Exception as e:
						logger.debug(f"检查属性 {attr_name} 时出错: {e}")
						continue
				
				# 方法3: 从插件元数据中获取（如果有）
				if hasattr(plugin_module, "__plugin_meta__"):
					meta = plugin_module.__plugin_meta__
					if hasattr(meta, "usage") and meta.usage:
						# 可以尝试从 usage 中解析命令（简单实现）
						pass
				
				if plugin_commands:
					commands_by_plugin[plugin_name] = plugin_commands
					logger.debug(f"插件 {plugin_name} 有 {len(plugin_commands)} 个命令")
			except Exception as e:
				logger.warning(f"获取插件 {plugin_name} 的命令时出错: {e}")
				continue
		
		logger.info(f"共收集到 {sum(len(cmds) for cmds in commands_by_plugin.values())} 个命令，来自 {len(commands_by_plugin)} 个插件")
	except Exception as e:
		logger.error(f"收集插件命令时出错: {e}", exc_info=True)
	
	return commands_by_plugin

def _parse_commands_from_source(file_path: Path, plugin_name: str) -> List[Dict[str, Any]]:
	"""
	从源代码文件中解析命令信息
	
	Args:
		file_path: 源代码文件路径
		plugin_name: 插件名称
		
	Returns:
		命令信息列表
	"""
	commands = []
	
	try:
		with open(file_path, "r", encoding="utf-8") as f:
			code = f.read()
		
		tree = ast.parse(code)
		
		for node in ast.walk(tree):
			# 查找 on_command 调用
			if isinstance(node, ast.Assign):
				for target in node.targets:
					if isinstance(target, ast.Name):
						var_name = target.id
						
						# 检查赋值右侧是否是 on_command 调用
						if isinstance(node.value, ast.Call):
							func = node.value.func
							func_name = None
							
							# 获取函数名
							if isinstance(func, ast.Name):
								func_name = func.id
							elif isinstance(func, ast.Attribute):
								func_name = func.attr
							
							if func_name == "on_command":
								# 提取命令信息
								cmd_info = _extract_command_from_ast(node.value, var_name, plugin_name, code)
								if cmd_info:
									commands.append(cmd_info)
	except Exception as e:
		logger.debug(f"解析源代码 {file_path} 时出错: {e}")
	
	return commands

def _extract_command_from_ast(call_node: ast.Call, var_name: str, plugin_name: str, source_code: str) -> Optional[Dict[str, Any]]:
	"""
	从 AST 节点中提取命令信息
	
	Args:
		call_node: on_command 调用的 AST 节点
		var_name: 变量名
		plugin_name: 插件名称
		source_code: 源代码（用于获取文档字符串）
		
	Returns:
		命令信息字典或 None
	"""
	try:
		cmd_name = None
		aliases = []
		description = ""
		
		# 获取第一个参数（命令名）
		if call_node.args:
			arg = call_node.args[0]
			if isinstance(arg, (ast.Constant, ast.Str)):
				cmd_name = arg.value if isinstance(arg, ast.Constant) else arg.s
		
		# 获取关键字参数
		for kw in call_node.keywords:
			if kw.arg == "aliases":
				if isinstance(kw.value, (ast.List, ast.Tuple, ast.Set)):
					for elt in kw.value.elts:
						if isinstance(elt, (ast.Constant, ast.Str)):
							aliases.append(elt.value if isinstance(elt, ast.Constant) else elt.s)
		
		# 如果无法从 on_command 获取命令名，使用变量名推断
		if not cmd_name:
			if var_name.endswith("_cmd"):
				cmd_name = var_name[:-4]
			elif var_name.endswith("_command"):
				cmd_name = var_name[:-8]
			else:
				cmd_name = var_name
		
		# 尝试从处理函数获取描述
		# 查找使用 @var_name.handle() 装饰的函数
		for node in ast.walk(ast.parse(source_code)):
			if isinstance(node, ast.FunctionDef):
				for decorator in node.decorator_list:
					if isinstance(decorator, ast.Attribute):
						if decorator.attr == "handle" and isinstance(decorator.value, ast.Name):
							if decorator.value.id == var_name:
								if node.docstring:
									description = node.docstring.strip()
								break
		
		return {
			"name": cmd_name,
			"aliases": aliases,
			"description": description or f"{cmd_name} 命令",
			"plugin_name": plugin_name,
			"var_name": var_name,
		}
	except Exception as e:
		logger.debug(f"从 AST 提取命令信息时出错: {e}")
		return None

def _extract_command_info_from_matcher(matcher: Matcher, attr_name: str, plugin_name: str) -> Optional[Dict[str, Any]]:
	"""
	从 Matcher 实例中提取命令信息（备用方法）
	
	Args:
		matcher: Matcher 实例
		attr_name: 属性名称
		plugin_name: 插件名称
		
	Returns:
		命令信息字典或 None
	"""
	try:
		cmd_name = None
		aliases = []
		description = ""
		
		# 尝试从 Matcher 的规则中获取命令信息
		if hasattr(matcher, "rule"):
			rule = matcher.rule
			if rule:
				if hasattr(rule, "cmd"):
					cmd_name = rule.cmd
				elif hasattr(rule, "command"):
					cmd_name = rule.command
		
		# 从属性名推断命令名
		if not cmd_name:
			if attr_name.endswith("_cmd"):
				cmd_name = attr_name[:-4]
			elif attr_name.endswith("_command"):
				cmd_name = attr_name[:-8]
			else:
				cmd_name = attr_name
		
		# 获取命令描述（从处理函数的文档字符串）
		if hasattr(matcher, "handlers"):
			for handler in matcher.handlers:
				if hasattr(handler, "__doc__") and handler.__doc__:
					description = handler.__doc__.strip()
					break
		
		return {
			"name": cmd_name,
			"aliases": aliases,
			"description": description or f"{cmd_name} 命令",
			"plugin_name": plugin_name,
			"attr_name": attr_name,
		}
	except Exception as e:
		logger.debug(f"从 Matcher 提取命令信息时出错: {e}")
		return None

def _extract_command_info(matcher: Matcher, attr_name: str, plugin_name: str) -> Optional[Dict[str, any]]:
	"""
	从 Matcher 中提取命令信息
	
	Args:
		matcher: Matcher 实例
		attr_name: 属性名称
		plugin_name: 插件名称
		
	Returns:
		命令信息字典或 None
	"""
	try:
		# 获取命令类型和规则
		cmd_type = None
		cmd_name = None
		aliases = []
		
		# 尝试从 Matcher 的类型信息中获取命令名
		if hasattr(matcher, "type"):
			cmd_type = matcher.type
		
		# 尝试从 Matcher 的规则中获取命令信息
		if hasattr(matcher, "rule"):
			rule = matcher.rule
			if rule:
				# 检查规则中是否有命令信息
				if hasattr(rule, "cmd"):
					cmd_name = rule.cmd
				elif hasattr(rule, "command"):
					cmd_name = rule.command
		
		# 尝试从属性名推断命令名（如果属性名看起来像命令名）
		if not cmd_name:
			# 如果属性名以 _cmd 结尾，去掉后缀
			if attr_name.endswith("_cmd"):
				cmd_name = attr_name[:-4]
			elif attr_name.endswith("_command"):
				cmd_name = attr_name[:-8]
			else:
				cmd_name = attr_name
		
		# 尝试从插件的元数据中获取命令信息
		try:
			plugin_module = matcher.plugin.module if hasattr(matcher, "plugin") and matcher.plugin else None
			if plugin_module and hasattr(plugin_module, "__plugin_meta__"):
				meta = plugin_module.__plugin_meta__
				if hasattr(meta, "usage"):
					# 可以从 usage 中解析命令信息（简单实现）
					pass
		except:
			pass
		
		# 如果无法确定命令名，使用属性名
		if not cmd_name:
			cmd_name = attr_name
		
		# 获取命令描述（从处理函数的文档字符串）
		description = ""
		if hasattr(matcher, "handlers"):
			for handler in matcher.handlers:
				if hasattr(handler, "__doc__") and handler.__doc__:
					description = handler.__doc__.strip()
					break
		
		return {
			"name": cmd_name,
			"aliases": aliases,
			"description": description or f"{cmd_name} 命令",
			"plugin_name": plugin_name,
			"attr_name": attr_name,
		}
	except Exception as e:
		logger.debug(f"提取命令信息时出错: {e}")
		return None

def format_commands_for_help(commands_by_plugin: Dict[str, List[Dict[str, any]]]) -> str:
	"""
	格式化命令信息为帮助文本
	
	Args:
		commands_by_plugin: 插件命令字典
		
	Returns:
		格式化的帮助文本
	"""
	if not commands_by_plugin:
		return "📋 当前没有已加载的插件命令"
	
	help_lines = ["📋 已安装的插件命令\n"]
	
	# 按插件分组显示
	for plugin_name, commands in commands_by_plugin.items():
		# 简化插件名称显示
		display_name = plugin_name.split(".")[-1] if "." in plugin_name else plugin_name
		
		help_lines.append(f"\n🔹 {display_name}")
		
		for cmd in commands:
			cmd_name = cmd.get("name", "未知命令")
			aliases = cmd.get("aliases", [])
			description = cmd.get("description", "")
			
			# 构建命令显示
			cmd_display = f"• {cmd_name}"
			if aliases:
				cmd_display += f" ({', '.join(aliases)})"
			
			help_lines.append(f"  {cmd_display}")
			if description and description != f"{cmd_name} 命令":
				help_lines.append(f"    {description}")
	
	help_lines.append("\n💡 提示: 使用 /help <命令名> 查看详细帮助")
	
	return "\n".join(help_lines)

def get_simple_command_list() -> List[str]:
	"""
	获取简单的命令列表（仅命令名）
	
	Returns:
		命令名列表
	"""
	commands_by_plugin = get_all_plugin_commands()
	all_commands = []
	
	for commands in commands_by_plugin.values():
		for cmd in commands:
			cmd_name = cmd.get("name", "")
			if cmd_name:
				all_commands.append(cmd_name)
			# 添加别名
			aliases = cmd.get("aliases", [])
			all_commands.extend(aliases)
	
	return sorted(set(all_commands))

