"""
插件迁移工具
用于将市场插件安装并移植到本地插件中
"""
from nonebot import on_command
from nonebot.adapters.onebot.v11 import MessageEvent, Message
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from nonebot.plugin import PluginMetadata
from src.utils.logger import get_logger
import asyncio
import subprocess
import sys
import importlib
import importlib.util
import inspect
import yaml
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

__plugin_meta__ = PluginMetadata(
	name="插件迁移工具",
	description="用于将市场插件安装并移植到本地插件中",
	usage="""
	可用命令：
	- /migrate_plugin <插件名> - 自动安装、迁移并注册市场插件
	- /迁移插件 <插件名> - 自动安装、迁移并注册市场插件
	- /安装插件 <插件名> - 自动安装、迁移并注册市场插件
	- /安装并重启 <插件名> - 安装、迁移并自动重启机器人（需管理员权限）
	- /重启机器人 - 重启机器人（需管理员权限）
	
	✨ 功能说明:
	• 自动安装插件（pip install）
	• 自动复制到 src/plugins 目录
	• 自动注册到 config.yaml
	• 自动检测并添加配置（如需要）
	""",
	type="application",
	homepage="https://github.com/your-username/nonebot-chatbot",
	supported_adapters={"~onebot.v11"},
)

logger = get_logger("migrate_plugin")

# 注意：
# 本文件既作为 NoneBot 插件使用，也会被离线脚本（scripts/migrate_all_plugins.py）导入。
# 在离线脚本场景下，NoneBot 尚未初始化，直接调用 on_command 会触发
# "NoneBot has not been initialized." 的异常。
# 因此，这里用 try/except 包一层，离线场景下不注册命令，只提供纯函数能力。
# 同时检查环境变量，如果是脚本模式，直接跳过命令注册
import os
if os.environ.get("MIGRATE_SCRIPT_MODE") != "1":
	try:
		migrate_cmd = on_command("migrate_plugin", aliases={"迁移插件", "安装插件"}, priority=10, block=True)
		migrate_restart_cmd = on_command(
			"migrate_plugin_restart",
			aliases={"安装并重启", "迁移并重启"},
			permission=SUPERUSER,
			priority=9,
			block=True,
		)
		restart_cmd = on_command(
			"restart",
			aliases={"重启", "重启机器人"},
			permission=SUPERUSER,
			priority=5,
			block=True,
		)
	except Exception:
		migrate_cmd = None
		migrate_restart_cmd = None
		restart_cmd = None
else:
	migrate_cmd = None
	migrate_restart_cmd = None
	restart_cmd = None

def install_plugin(plugin_name: str) -> Tuple[bool, Optional[str]]:
	"""
	安装插件到当前环境
	
	Args:
		plugin_name: 插件名称（如 nonebot-plugin-jrrp3）
		
	Returns:
		(是否安装成功, 错误信息)
	"""
	try:
		logger.info(f"正在安装插件: {plugin_name}")
		
		# 检查是否在虚拟环境中
		in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
		
		# 构建 pip 命令
		pip_cmd = [sys.executable, "-m", "pip", "install", plugin_name]
		
		# 如果不在虚拟环境中，尝试使用 --user 标志
		if not in_venv:
			logger.warning("未检测到虚拟环境，尝试使用 --user 标志安装")
			pip_cmd.append("--user")
		
		result = subprocess.run(
			pip_cmd,
			capture_output=True,
			text=True,
			timeout=300
		)
		if result.returncode == 0:
			logger.info(f"插件 {plugin_name} 安装成功")
			return True, None
		else:
			error_msg = result.stderr or result.stdout
			logger.error(f"插件 {plugin_name} 安装失败: {error_msg}")
			
			# 分析错误类型
			error_type = "未知错误"
			suggestion = ""
			
			if "PEP 668" in error_msg or "externally-managed-environment" in error_msg or "break-system-packages" in error_msg:
				error_type = "系统包管理限制（PEP 668）"
				suggestion = """
💡 解决方案:
1. 使用虚拟环境安装（推荐）:
   cd /Users/cheng/Desktop/document/cheng/nonebot-chatbot
   source venv/bin/activate
   pip install """ + plugin_name + """
   
2. 或者使用 --user 标志（已自动尝试）
3. 或者使用 --break-system-packages 标志（不推荐）
				""".strip()
			elif "Cargo" in error_msg or "Rust" in error_msg or "rustup" in error_msg:
				error_type = "需要 Rust 编译环境"
				suggestion = """
💡 解决方案:
1. 安装 Rust 工具链:
   - macOS/Linux: curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
   - Windows: 下载并安装 https://rustup.rs/
2. 安装后重启终端，然后重试
3. 或者寻找不需要 Rust 的替代插件
				""".strip()
			elif "Microsoft Visual C++" in error_msg or "cl.exe" in error_msg:
				error_type = "需要 C++ 编译环境"
				suggestion = """
💡 解决方案:
1. Windows: 安装 Visual Studio Build Tools
2. 或使用预编译的 wheel 包
				""".strip()
			elif "No matching distribution" in error_msg or "Could not find a version" in error_msg:
				error_type = "插件不存在或名称错误"
				suggestion = f"""
💡 解决方案:
1. 检查插件名称是否正确: {plugin_name}
2. 确认插件是否在 PyPI 上发布
3. 访问 https://pypi.org/search/?q={plugin_name.replace("-", "+")} 搜索插件
4. 尝试使用正确的插件名称（可能是 nonebot-plugin-xxx 或 nonebot_plugin_xxx）
				""".strip()
			elif "Permission denied" in error_msg or "access denied" in error_msg.lower():
				error_type = "权限不足"
				suggestion = """
💡 解决方案:
1. 使用虚拟环境: python -m venv venv && source venv/bin/activate
2. 或使用 --user 标志（已自动尝试）
				""".strip()
			
			# 截取错误信息（避免消息过长）
			error_preview = error_msg[:800] if len(error_msg) > 800 else error_msg
			if len(error_msg) > 800:
				error_preview += "\n... (错误信息已截断)"
			
			detailed_error = f"""
❌ 安装失败: {error_type}

错误详情:
{error_preview}

{suggestion}
			""".strip()
			
			return False, detailed_error
	except subprocess.TimeoutExpired:
		error_msg = "安装超时（超过5分钟）"
		logger.error(f"插件 {plugin_name} 安装超时")
		return False, error_msg
	except Exception as e:
		error_msg = f"安装过程出错: {str(e)}"
		logger.error(f"安装插件时出错: {e}")
		return False, error_msg

def find_plugin_module(plugin_name: str) -> Optional[str]:
	"""
	查找已安装插件的模块路径
	
	Args:
		plugin_name: 插件名称（如 nonebot-plugin-jrrp3）
		
	Returns:
		模块路径（如 nonebot_plugin_jrrp3）或 None
	"""
	# 常见的命名转换规则
	name_mapping = {
		"nonebot-plugin-jrrp3": "nonebot_plugin_jrrp3",
		"nonebot-plugin-epicfree": "nonebot_plugin_epicfree",
		"nonebot-plugin-anans-sketchbook": "nonebot_plugin_anans_sketchbook",
		"nonebot-plugin-manosaba-memes": "nonebot_plugin_manosaba_memes",
		"nonebot-plugin-xiuxian-2": "nonebot_plugin_xiuxian_2",
		"nonebot_plugin_xiuxian_2": "nonebot_plugin_xiuxian_2",
	}
	
	# 先尝试映射
	if plugin_name in name_mapping:
		module_name = name_mapping[plugin_name]
	else:
		# 尝试将插件名转换为模块名（- 替换为 _）
		module_name = plugin_name.replace("-", "_")
	
	# 先尝试使用 find_spec 查找模块（不实际导入，避免依赖错误）
	try:
		spec = importlib.util.find_spec(module_name)
		if spec and spec.origin:
			logger.info(f"找到插件模块路径: {module_name} (路径: {spec.origin})")
			# 即使导入失败，也返回模块名，让后续步骤尝试读取源代码
			return module_name
	except Exception as e:
		logger.debug(f"使用 find_spec 查找模块 {module_name} 失败: {e}")
	
	# 尝试导入模块（可能因为依赖问题失败）
	try:
		module = importlib.import_module(module_name)
		logger.info(f"成功导入插件模块: {module_name}")
		return module_name
	except (ImportError, AttributeError, KeyError, ValueError) as e:
		# ImportError: 模块不存在或依赖缺失
		# AttributeError/KeyError: 配置缺失（如 'Config' object has no attribute 'anan'）
		# ValueError: 配置验证失败
		error_msg = str(e)
		
		# 如果是依赖导入错误（如 cannot import name 'xxx' from 'yyy'），仍然尝试继续
		if "cannot import name" in error_msg or "No module named" in error_msg:
			logger.warning(f"插件 {module_name} 导入时出现依赖错误（可能缺少依赖或版本不兼容）: {error_msg}")
			logger.warning(f"将尝试使用 find_spec 查找模块路径并读取源代码")
			# 仍然返回模块名，让后续步骤尝试读取源代码
			return module_name
		
		# 如果是配置相关错误，记录但不立即失败
		if "attribute" in error_msg.lower() or "config" in error_msg.lower() or "Field required" in error_msg:
			logger.warning(f"插件 {module_name} 导入时出现配置错误（可能缺少配置项）: {error_msg}")
			# 仍然返回模块名，让后续步骤尝试读取源代码
			return module_name
		
		# 尝试其他可能的命名
		variants = [
			module_name.replace("nonebot_plugin_", ""),
			module_name.replace("_", ""),
			plugin_name.replace("-", ""),
		]
		for variant in variants:
			try:
				importlib.import_module(variant)
				logger.info(f"找到插件模块: {variant}")
				return variant
			except (ImportError, AttributeError, KeyError, ValueError):
				continue
		
		# 如果所有尝试都失败，但 find_spec 能找到模块，仍然返回模块名
		try:
			spec = importlib.util.find_spec(module_name)
			if spec and spec.origin:
				logger.warning(f"插件 {module_name} 导入失败，但找到了模块路径: {spec.origin}")
				logger.warning(f"将尝试直接读取源代码文件")
				return module_name
		except:
			pass
		
		logger.error(f"未找到插件模块: {plugin_name}, 错误: {error_msg}")
		return None
	except Exception as e:
		# 捕获其他所有异常
		error_msg = str(e)
		logger.error(f"导入插件模块 {module_name} 时出错: {error_msg}")
		
		# 如果是依赖或配置错误，仍然尝试使用 find_spec
		if "cannot import" in error_msg.lower() or "config" in error_msg.lower() or "attribute" in error_msg.lower():
			try:
				spec = importlib.util.find_spec(module_name)
				if spec and spec.origin:
					logger.warning(f"插件 {module_name} 导入失败，但找到了模块路径: {spec.origin}")
					logger.warning(f"将尝试直接读取源代码文件")
					return module_name
			except:
				pass
		
		return None

def get_plugin_source_file(module_name: str) -> Optional[Path]:
	"""
	获取插件源代码文件路径
	
	Args:
		module_name: 模块名称
		
	Returns:
		源代码文件路径或 None
	"""
	# 优先使用 importlib.util.find_spec，避免导入模块时的配置错误
	try:
		spec = importlib.util.find_spec(module_name)
		if spec and spec.origin:
			file_path = Path(spec.origin)
			# 如果是 __init__.py，尝试查找主文件
			if file_path.name == "__init__.py":
				# 查找同目录下的其他 .py 文件
				parent_dir = file_path.parent
				py_files = list(parent_dir.glob("*.py"))
				if py_files:
					# 返回第一个非 __init__.py 的文件
					for py_file in py_files:
						if py_file.name != "__init__.py":
							return py_file
			return file_path
	except Exception as e:
		logger.warning(f"使用 find_spec 查找模块 {module_name} 失败: {e}")
	
	# 备用方案：尝试从已导入的模块获取
	try:
		if module_name in sys.modules:
			module = sys.modules[module_name]
			if hasattr(module, "__file__") and module.__file__:
				file_path = Path(module.__file__)
				if file_path.exists():
					return file_path
	except Exception as e:
		logger.warning(f"从 sys.modules 获取模块 {module_name} 路径失败: {e}")
	
	# 最后尝试：直接导入（可能失败，但至少尝试）
	try:
		module = importlib.import_module(module_name)
		if hasattr(module, "__file__") and module.__file__:
			file_path = Path(module.__file__)
			if file_path.exists():
				return file_path
	except Exception as e:
		logger.error(f"导入模块 {module_name} 获取路径失败: {e}")
	
	return None

def read_plugin_code(module_name: str) -> Optional[str]:
	"""
	读取插件的源代码
	
	Args:
		module_name: 模块名称
		
	Returns:
		源代码内容或 None
	"""
	source_file = get_plugin_source_file(module_name)
	if source_file and source_file.exists():
		try:
			with open(source_file, "r", encoding="utf-8") as f:
				code = f.read()
			logger.info(f"成功读取插件源代码: {source_file}")
			return code
		except Exception as e:
			logger.error(f"读取插件源代码时出错: {e}")
	return None

def extract_plugin_functions(code: str) -> Dict[str, Any]:
	"""
	从源代码中提取函数和命令处理器
	
	Args:
		code: 源代码内容
		
	Returns:
		提取的信息字典
	"""
	import ast
	
	info = {
		"commands": [],
		"functions": [],
		"imports": [],
	}
	
	try:
		tree = ast.parse(code)
		
		for node in ast.walk(tree):
			# 提取命令定义（on_command 调用）
			if isinstance(node, ast.Assign):
				for target in node.targets:
					if isinstance(target, ast.Name):
						if isinstance(node.value, ast.Call):
							func_name = getattr(node.value.func, "id", None) or getattr(node.value.func, "attr", None)
							if func_name == "on_command":
								# 提取命令名称和别名
								args = node.value.args
								cmd_name = None
								aliases = []
								
								if args:
									if isinstance(args[0], ast.Constant):
										cmd_name = args[0].value
									elif isinstance(args[0], ast.Str):  # Python < 3.8
										cmd_name = args[0].s
								
								# 提取关键字参数
								for kw in node.value.keywords:
									if kw.arg == "aliases":
										if isinstance(kw.value, (ast.List, ast.Tuple)):
											aliases = [
												item.value if isinstance(item, ast.Constant) else item.s
												for item in kw.value.elts
											]
								
								info["commands"].append({
									"var_name": target.id,
									"cmd_name": cmd_name,
									"aliases": aliases,
								})
			
			# 提取函数定义
			if isinstance(node, ast.FunctionDef):
				# 检查是否是命令处理函数（通常有 @xxx.handle() 装饰器）
				func_code = ""
				try:
					# Python 3.8+ 支持 get_source_segment
					if hasattr(ast, "get_source_segment"):
						func_code = ast.get_source_segment(code, node) or ""
					else:
						# Python < 3.8 的兼容处理
						lines = code.split("\n")
						if node.lineno and node.end_lineno:
							func_code = "\n".join(lines[node.lineno - 1:node.end_lineno])
				except:
					pass
				
				info["functions"].append({
					"name": node.name,
					"code": func_code,
				})
			
			# 提取导入语句
			if isinstance(node, (ast.Import, ast.ImportFrom)):
				import_str = ""
				try:
					# Python 3.8+ 支持 get_source_segment
					if hasattr(ast, "get_source_segment"):
						import_str = ast.get_source_segment(code, node) or ""
					else:
						# Python < 3.8 的兼容处理
						lines = code.split("\n")
						if node.lineno:
							import_str = lines[node.lineno - 1]
				except:
					pass
				
				if import_str:
					info["imports"].append(import_str)
		
		logger.info(f"提取到 {len(info['commands'])} 个命令, {len(info['functions'])} 个函数")
	except Exception as e:
		logger.error(f"解析插件代码时出错: {e}")
	
	return info


def list_local_migrated_plugins() -> Dict[str, str]:
	"""
	列出当前 src/plugins 目录下「疑似由迁移脚本生成」的第三方插件副本
	
	仅做静态扫描，不做任何删除操作，返回:
	- key: 本地插件包名（如 anans_sketchbook）
	- value: 目录绝对路径
	
	判定规则（尽量保守）：
	- 目录位于 src/plugins 下，且包含 __init__.py
	- __init__.py / 目录下任一 .py 顶部包含「移植自 nonebot-plugin-」或「迁移自 nonebot-plugin-」等注释
	"""
	project_root = Path(__file__).parent.parent.parent
	plugins_root = project_root / "src" / "plugins"
	result: Dict[str, str] = {}
	
	if not plugins_root.exists():
		return result
	
	for item in plugins_root.iterdir():
		if not item.is_dir():
			continue
		if item.name.startswith("_"):
			continue
		
		init_file = item / "__init__.py"
		if not init_file.exists():
			continue
		
		marked = False
		candidates = [init_file] + list(item.glob("*.py"))
		for py in candidates:
			try:
				with open(py, "r", encoding="utf-8") as f:
					head = "".join([next(f) for _ in range(5)])
				if "移植自 nonebot-plugin" in head or "迁移自 nonebot-plugin" in head:
					marked = True
					break
			except StopIteration:
				# 文件行数不足 5 行
				continue
			except Exception:
				continue
		
		if marked:
			result[item.name] = str(item.resolve())
	
	return result

def detect_plugin_config(module_name: str) -> Optional[Dict[str, Any]]:
	"""
	检测插件需要的配置项
	
	Args:
		module_name: 模块名称
		
	Returns:
		配置字典或 None
	"""
	try:
		# 尝试从插件的 Config 类获取配置信息
		spec = importlib.util.find_spec(module_name)
		if spec and spec.origin:
			# 读取插件源代码
			plugin_file = Path(spec.origin)
			if plugin_file.exists():
				with open(plugin_file, "r", encoding="utf-8") as f:
					code = f.read()
				
				# 查找 Config 类定义
				import ast
				tree = ast.parse(code)
				
				for node in ast.walk(tree):
					if isinstance(node, ast.ClassDef):
						# 检查是否是 Config 类
						if "Config" in node.name or "config" in node.name.lower():
							# 提取类的字段
							config_fields = {}
							for item in node.body:
								if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
									field_name = item.target.id
									# 尝试获取默认值
									default_value = None
									if item.value:
										if isinstance(item.value, ast.Constant):
											default_value = item.value.value
										elif isinstance(item.value, ast.Str):
											default_value = item.value.s
										elif isinstance(item.value, ast.NameConstant):
											default_value = item.value.value
									
									config_fields[field_name] = default_value
							
							if config_fields:
								logger.info(f"检测到插件 {module_name} 的配置字段: {list(config_fields.keys())}")
								return config_fields
	except Exception as e:
		logger.warning(f"检测插件配置时出错: {e}")
	
	return None

def get_plugin_config_template(plugin_name: str) -> Dict[str, Any]:
	"""
	获取常见插件的配置模板
	
	Args:
		plugin_name: 插件名称
		
	Returns:
		配置模板字典
	"""
	# 常见插件的配置模板
	templates = {
		"nonebot-plugin-anans-sketchbook": {
			# 此插件不需要额外配置
		},
		"nonebot-plugin-epicfree": {
			"epicfree": {
				"enabled": True,
			}
		},
	}
	
	# 检查是否有模板
	for key, template in templates.items():
		if key in plugin_name.lower():
			return template
	
	# 默认模板
	plugin_key = plugin_name.replace("nonebot-plugin-", "").replace("-", "_")
	return {
		plugin_key: {
			"enabled": True,
		}
	}

def copy_plugin_to_local(module_name: str, plugin_name: str) -> Tuple[bool, Optional[str], Optional[str]]:
	"""
	将外部插件「最小改动」复制到本地插件目录
	
	设计原则（重新设计后）：
	- 只做「文件层面」的迁移：把 site-packages 里的插件代码/资源原样拷贝到 `src/plugins/<local_name>`。
	- 不再解析/重写第三方源码中的 import、require、inherit_supported_adapters 等调用，避免引入逻辑偏差。
	- 目录命名规则仍为：`nonebot-plugin-xxx` -> `src/plugins/xxx`，内部相对导入保持可用。
	- 依赖链仍然依赖原第三方包（nonebot_plugin_xxx），如确有需要再手动按插件文档处理。
	
	注意：
	- 之前版本尝试自动重写外部依赖引用，已经在 pokemonle 等插件上暴露出兼容性问题。
	- 现在的策略是「最小改动 + 明确边界」，把迁移重点放在：
	  - 代码/资源归档到项目仓库
	  - 配置启用由第三方名切换到 `src.plugins.xxx`
	  - 具体适配逻辑如有需要再针对单个插件编写补丁
	
	Args:
		module_name: 插件模块名称（如 nonebot_plugin_anans_sketchbook）
		plugin_name: 插件名称（如 nonebot-plugin-anans-sketchbook）
		
	Returns:
		(是否成功, 本地插件路径, 错误信息)
	"""
	try:
		# 获取插件源代码位置
		# 注意：如果插件是“单文件模块”（spec.origin 指向 xxx.py），直接取 parent 会变成整个 site-packages，
		# 会误复制大量无关文件。这里区分“包插件”和“单文件插件”。
		spec = importlib.util.find_spec(module_name)
		if not spec or not spec.origin:
			return False, None, "无法找到插件模块路径"
		
		origin_path = Path(spec.origin)
		is_package_plugin = origin_path.name == "__init__.py" or bool(getattr(spec, "submodule_search_locations", None))
		
		# 包插件：复制包目录；单文件插件：仅复制该文件本身
		if is_package_plugin:
			plugin_source_dir = origin_path.parent
			single_file_source: Optional[Path] = None
		else:
			plugin_source_dir = origin_path.parent
			single_file_source = origin_path
		
		if is_package_plugin and not plugin_source_dir.exists():
			return False, None, f"插件源目录不存在: {plugin_source_dir}"
		if (not is_package_plugin) and (single_file_source is None or not single_file_source.exists()):
			return False, None, f"插件源文件不存在: {single_file_source}"
		
		# 确定目标目录（src/plugins/插件名）
		project_root = Path(__file__).parent.parent.parent
		local_plugin_name = plugin_name.replace("nonebot-plugin-", "").replace("-", "_")
		target_dir = project_root / "src" / "plugins" / local_plugin_name
		
		# 如果目标目录已存在，先备份
		if target_dir.exists():
			backup_dir = target_dir.with_suffix(f".bak.{int(__import__('time').time())}")
			logger.warning(f"目标目录已存在，备份到: {backup_dir}")
			shutil.move(str(target_dir), str(backup_dir))
		
		# 创建目标目录
		target_dir.mkdir(parents=True, exist_ok=True)
		
		# 复制 Python 文件（仅做「原样复制」，不再改写源码）
		# - 包插件：复制包目录内所有 .py
		# - 单文件插件：仅复制该文件，并写入目标包的 __init__.py（保证 src.plugins.xxx 可导入）
		copied_files = []
		source_py_files = plugin_source_dir.rglob("*.py") if is_package_plugin else [single_file_source]
		for source_file in source_py_files:
			if source_file is None:
				continue
			# 计算相对路径
			if (not is_package_plugin) and single_file_source and source_file == single_file_source:
				relative_path = Path("__init__.py")
			else:
				relative_path = source_file.relative_to(plugin_source_dir)
			target_file = target_dir / relative_path
			
			# 创建目标目录结构
			target_file.parent.mkdir(parents=True, exist_ok=True)
			
			# 读取源文件内容
			with open(source_file, "r", encoding="utf-8") as f:
				content = f.read()
			
			# 写入内容（不改写）
			with open(target_file, "w", encoding="utf-8") as f:
				f.write(content)
			
			copied_files.append(str(relative_path))
		
		# 复制其他资源文件（如 .json, .yaml, .txt, .html, .css, .js 等）
		# 单文件插件的 parent 可能是 site-packages，不能递归复制资源（会误拷大量文件）
		if is_package_plugin:
			# 扩展资源文件类型，包括模板、样式、脚本等
			resource_extensions = [
				"*.json", "*.yaml", "*.yml", "*.txt", "*.md", "*.toml",
				"*.html", "*.css", "*.js", "*.png", "*.jpg", "*.jpeg", 
				"*.gif", "*.svg", "*.webp", "*.ico", "*.woff", "*.woff2",
				"*.ttf", "*.eot", "*.xml", "*.csv"
			]
			for ext in resource_extensions:
				for source_file in plugin_source_dir.rglob(ext):
					relative_path = source_file.relative_to(plugin_source_dir)
					target_file = target_dir / relative_path
					target_file.parent.mkdir(parents=True, exist_ok=True)
					shutil.copy2(source_file, target_file)
					if str(relative_path) not in copied_files:
						copied_files.append(str(relative_path))
		
		# 确保目标目录是一个可导入的包（至少需要 __init__.py）
		# 为了尽量少改第三方源码，我们保持包结构，不再把 __init__.py 改名为其他文件。
		init_file = target_dir / "__init__.py"
		if not init_file.exists():
			# 检查是否有主文件（通常是模块名.py）
			local_plugin_simple_name = local_plugin_name.split("_")[-1] if "_" in local_plugin_name else local_plugin_name
			main_files = [
				target_dir / f"{local_plugin_name}.py",
				target_dir / f"{local_plugin_simple_name}.py",
			]
			
			main_file = None
			for mf in main_files:
				if mf.exists():
					main_file = mf.stem  # 不带扩展名的文件名
					break
			
			# 创建 __init__.py，确保插件可以被正确导入
			if main_file:
				init_content = f'''"""
{plugin_name} 插件
迁移自第三方插件，已复制到本地项目
"""
# 导入主模块，确保插件功能可用
from .{main_file} import *
'''
			else:
				# 如果没有找到主文件，创建空的 __init__.py
				# NoneBot 会自动加载此包下的所有模块
				init_content = f'''"""
{plugin_name} 插件
迁移自第三方插件，已复制到本地项目
"""
# 插件已迁移到本地，NoneBot 会自动加载此包下的所有模块
'''
			
			with open(init_file, "w", encoding="utf-8") as f:
				f.write(init_content)
			logger.info(f"已创建 __init__.py 文件: {init_file}")
		
		logger.info(f"成功将插件 {plugin_name} 复制到 {target_dir}")
		logger.info(f"复制了 {len(copied_files)} 个文件")
		
		# 返回本地插件路径（用于配置）
		local_plugin_path = f"src.plugins.{local_plugin_name}"
		return True, local_plugin_path, None
		
	except Exception as e:
		error_msg = f"复制插件到本地失败: {str(e)}"
		logger.error(error_msg, exc_info=True)
		return False, None, error_msg

def update_plugin_config_in_yaml(old_plugin_name: str, new_plugin_path: str, config_path: Optional[str] = None) -> bool:
	"""
	更新配置文件中的插件路径（从外部插件改为内部插件）
	
	Args:
		old_plugin_name: 旧插件名称（如 nonebot-plugin-anans-sketchbook）
		new_plugin_path: 新插件路径（如 src.plugins.anans_sketchbook）
		config_path: 配置文件路径（默认: configs/config.yaml）
		
	Returns:
		是否成功
	"""
	try:
		# 确定配置文件路径
		if config_path is None:
			project_root = Path(__file__).parent.parent.parent
			config_path = str(project_root / "configs" / "config.yaml")
		
		config_file = Path(config_path)
		if not config_file.exists():
			logger.error(f"配置文件不存在: {config_path}")
			return False
		
		# 读取现有配置
		with open(config_file, "r", encoding="utf-8") as f:
			config = yaml.safe_load(f) or {}
		
		# 确保 plugins 配置存在
		if "plugins" not in config:
			config["plugins"] = {}
		if "enabled" not in config["plugins"]:
			config["plugins"]["enabled"] = []
		
		enabled_list = config["plugins"]["enabled"]
		if not isinstance(enabled_list, list):
			enabled_list = list(enabled_list) if enabled_list else []
			config["plugins"]["enabled"] = enabled_list
		
		# 获取模块名（用于清理旧引用）
		module_name = old_plugin_name.replace("nonebot-plugin-", "").replace("-", "_")
		full_module_name = f"nonebot_plugin_{module_name}"
		
		# 替换外部插件名称为内部插件路径
		replaced = False
		old_variants = [
			old_plugin_name,  # nonebot-plugin-xxx
			old_plugin_name.replace("-", "_"),  # nonebot_plugin_xxx
			full_module_name,  # nonebot_plugin_xxx
			module_name,  # xxx
		]
		
		# 查找并替换所有可能的旧引用
		for i, item in enumerate(enabled_list):
			if item in old_variants and item != new_plugin_path:
				enabled_list[i] = new_plugin_path
				logger.info(f"已将插件 {item} 更新为 {new_plugin_path}")
				replaced = True
				break
		
		# 如果没有找到旧引用，添加新插件
		if not replaced and new_plugin_path not in enabled_list:
			enabled_list.append(new_plugin_path)
			logger.info(f"已添加插件 {new_plugin_path} 到启用列表")
		
		# 去重（确保同一个插件不会出现多次）
		enabled_list[:] = list(dict.fromkeys(enabled_list))
		
		# 写回配置文件
		with open(config_file, "w", encoding="utf-8") as f:
			yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
		
		logger.info(f"成功更新配置文件中的插件路径")
		return True
	except Exception as e:
		logger.error(f"更新配置文件中的插件路径失败: {e}")
		return False

def add_plugin_config_to_yaml(plugin_name: str, config_data: Dict[str, Any], config_path: Optional[str] = None) -> bool:
	"""
	将插件配置追加到 config.yaml
	
	Args:
		plugin_name: 插件名称
		config_data: 配置数据
		config_path: 配置文件路径（默认: configs/config.yaml）
		
	Returns:
		是否成功
	"""
	try:
		# 确定配置文件路径
		if config_path is None:
			project_root = Path(__file__).parent.parent.parent
			config_path = str(project_root / "configs" / "config.yaml")
		
		config_file = Path(config_path)
		if not config_file.exists():
			logger.error(f"配置文件不存在: {config_path}")
			return False
		
		# 读取现有配置
		with open(config_file, "r", encoding="utf-8") as f:
			config = yaml.safe_load(f) or {}
		
		# 合并配置（深度合并）
		def deep_merge(base: Dict, override: Dict) -> Dict:
			"""深度合并字典"""
			result = base.copy()
			for key, value in override.items():
				if key in result and isinstance(result[key], dict) and isinstance(value, dict):
					result[key] = deep_merge(result[key], value)
				else:
					result[key] = value
			return result
		
		config = deep_merge(config, config_data)
		
		# 写回配置文件
		with open(config_file, "w", encoding="utf-8") as f:
			yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
		
		logger.info(f"成功将插件 {plugin_name} 的配置追加到 {config_path}")
		return True
	except Exception as e:
		logger.error(f"追加插件配置到 YAML 时出错: {e}")
		return False

if migrate_cmd is not None:
	@migrate_cmd.handle()
	async def handle_migrate(event: MessageEvent, args: Message = CommandArg()):
		"""迁移插件命令 - 将市场插件安装并移植到本地插件中"""
		arg_str = str(args).strip()
		
		if not arg_str:
			await migrate_cmd.send("""
❌ 用法: /migrate_plugin <插件名称>

示例:
• /migrate_plugin nonebot-plugin-jrrp3
• /migrate_plugin nonebot-plugin-epicfree

✨ 功能说明:
1. 自动安装插件到当前环境（pip install）
2. 自动复制插件到 src/plugins 目录
3. 自动注册插件到 config.yaml（添加到 plugins.enabled）
4. 自动检测并添加插件配置（如需要）

💡 提示: 迁移完成后，重启机器人即可使用（可发送 /重启机器人）
			""".strip())
			return
		
		plugin_name = arg_str
		
		await migrate_cmd.send(f"🔄 开始迁移插件: {plugin_name}\n请稍候...")
		
		# 步骤1: 安装插件
		install_success, error_detail = install_plugin(plugin_name)
		if not install_success:
			error_message = f"""
❌ 插件 {plugin_name} 安装失败

{error_detail if error_detail else "请检查插件名称是否正确或网络连接是否正常"}

💡 提示: 
• 检查插件名称拼写
• 确认网络连接正常
• 查看上方错误信息获取详细解决方案
			""".strip()
			await migrate_cmd.send(error_message)
			return
		
		# 步骤2: 查找插件模块
		module_name = find_plugin_module(plugin_name)
		if not module_name:
			await migrate_cmd.send(f"""
❌ 无法找到插件 {plugin_name} 的模块，迁移失败

💡 可能的原因:
• 插件安装不完整
• 插件名称转换错误
• 插件需要特定配置才能导入
			""".strip())
			return
		
		# 步骤2.5: 检测插件配置需求并自动追加
		plugin_config = detect_plugin_config(module_name)
		config_added = False
		config_message = ""
		
		if plugin_config:
			# 使用检测到的配置
			plugin_key = module_name.replace("nonebot_plugin_", "").replace("_", "-")
			config_template = {plugin_key: plugin_config}
			config_added = add_plugin_config_to_yaml(plugin_name, config_template)
			if config_added:
				config_message = f"\n✅ 已自动检测并添加插件配置到 config.yaml"
		else:
			# 尝试使用模板配置
			config_template = get_plugin_config_template(plugin_name)
			if config_template:
				config_added = add_plugin_config_to_yaml(plugin_name, config_template)
				if config_added:
					config_message = f"\n✅ 已自动添加插件配置模板到 config.yaml\n💡 提示: 请检查并完善配置项（可能需要填写 API Key 等）"
		
		# 步骤3: 读取插件源代码
		plugin_code = read_plugin_code(module_name)
		if not plugin_code:
			# 如果无法读取源代码，可能是配置问题
			await migrate_cmd.send(f"""
⚠️ 无法读取插件 {plugin_name} 的源代码

💡 可能的原因:
• 插件需要特定配置才能正常工作
• 插件源代码位置异常
• 插件在导入时依赖配置项

💡 建议:
• 检查插件是否需要额外配置
• 查看插件文档了解配置要求
• 尝试手动查看插件源代码位置
			""".strip())
			return
		
		# 步骤4: 自动复制插件到本地插件目录
		await migrate_cmd.send("📦 正在将插件复制到本地插件目录...")
		copy_success, local_plugin_path, copy_error = copy_plugin_to_local(module_name, plugin_name)
		
		if not copy_success:
			error_message = f"""
⚠️ 复制插件到本地失败: {copy_error}

💡 提示: 插件已安装，但未复制到本地目录
💡 建议: 可以手动复制插件文件，或继续使用外部插件模式
			""".strip()
			await migrate_cmd.send(error_message)
			return  # 复制失败则中断流程，确保只有成功复制才会注册
		
		# 步骤5: 自动更新配置文件（将外部插件路径改为内部插件路径，并注册到 plugins.enabled）
		if copy_success and local_plugin_path:
			await migrate_cmd.send("📝 正在更新配置文件并注册插件...")
			update_success = update_plugin_config_in_yaml(plugin_name, local_plugin_path)
			if update_success:
				config_message += f"\n✅ 已自动注册插件到 config.yaml: {local_plugin_path}"
				logger.info(f"插件 {plugin_name} 已成功注册到配置文件")
			else:
				config_message += f"\n⚠️ 配置文件更新失败，请手动将 {local_plugin_path} 添加到 plugins.enabled"
				logger.warning(f"插件 {plugin_name} 注册到配置文件失败")
		
		# 步骤6: 提取插件功能（用于报告）
		plugin_info = extract_plugin_functions(plugin_code)
		
		# 步骤7: 生成迁移报告
		source_file = get_plugin_source_file(module_name)
		source_path = str(source_file) if source_file else "无法获取"
		
		if copy_success and local_plugin_path:
			report = f"""
✅ 插件迁移完成: {plugin_name}

📦 迁移信息:
• 命令数量: {len(plugin_info['commands'])}
• 函数数量: {len(plugin_info['functions'])}
• 导入语句: {len(plugin_info['imports'])} 条

✅ 插件已复制到本地: {local_plugin_path}
📝 原始位置: {source_path}
{config_message}

💡 提示: 插件已转换为内部插件，重启机器人后即可使用（可发送 /重启机器人）
			""".strip()
		else:
			report = f"""
✅ 插件分析完成: {plugin_name}

📦 提取的信息:
• 命令数量: {len(plugin_info['commands'])}
• 函数数量: {len(plugin_info['functions'])}
• 导入语句: {len(plugin_info['imports'])} 条

⚠️ 注意: 插件未复制到本地，仍使用外部插件模式
📝 插件位置: {source_path}
{config_message}

💡 提示: 可以手动复制插件文件到 src/plugins 目录
			""".strip()
		
		await migrate_cmd.send(report)
		
		# 记录日志
		logger.info(f"用户 {event.user_id} 迁移插件: {plugin_name}")
		logger.info(f"提取到 {len(plugin_info['commands'])} 个命令, {len(plugin_info['functions'])} 个函数")


def _schedule_restart(delay: float = 1.0):
	"""在 delay 秒后用相同参数重启当前进程。"""
	def _do_restart():
		os.execl(sys.executable, sys.executable, *sys.argv)
	try:
		loop = asyncio.get_running_loop()
		loop.call_later(delay, _do_restart)
	except RuntimeError:
		_do_restart()


if restart_cmd is not None:
	@restart_cmd.handle()
	async def handle_restart():
		await restart_cmd.send("♻️ 正在重启机器人（约1秒）...")
		_schedule_restart(1.0)


if migrate_restart_cmd is not None:
	@migrate_restart_cmd.handle()
	async def handle_migrate_restart(args: Message = CommandArg()):
		plugin_name = str(args).strip()
		if not plugin_name:
			await migrate_restart_cmd.finish("❌ 用法: /安装并重启 <插件名称>\n例如: /安装并重启 nonebot-plugin-jrrp3")
		
		await migrate_restart_cmd.send(f"🔄 开始安装并迁移插件: {plugin_name}\n完成后将自动重启...")
		
		install_success, error_detail = install_plugin(plugin_name)
		if not install_success:
			await migrate_restart_cmd.finish(f"❌ 安装失败:\n{error_detail if error_detail else ''}".strip())
		
		module_name = find_plugin_module(plugin_name)
		if not module_name:
			await migrate_restart_cmd.finish(f"❌ 无法找到插件模块: {plugin_name}")
		
		# 检测并追加配置（可选）
		try:
			plugin_config = detect_plugin_config(module_name)
			if plugin_config:
				plugin_key = module_name.replace("nonebot_plugin_", "").replace("_", "-")
				add_plugin_config_to_yaml(plugin_name, {plugin_key: plugin_config})
			else:
				config_template = get_plugin_config_template(plugin_name)
				if config_template:
					add_plugin_config_to_yaml(plugin_name, config_template)
		except Exception as e:
			logger.warning(f"安装并重启：追加配置失败（可忽略）: {e}")
		
		copy_success, local_plugin_path, copy_error = copy_plugin_to_local(module_name, plugin_name)
		if not copy_success or not local_plugin_path:
			await migrate_restart_cmd.finish(f"❌ 复制到本地失败: {copy_error}")
		
		update_plugin_config_in_yaml(plugin_name, local_plugin_path)
		await migrate_restart_cmd.send(f"✅ 已迁移为本地插件: {local_plugin_path}\n♻️ 即将重启机器人...")
		_schedule_restart(1.0)


# 额外提供一个命令：列出历史迁移插件（仅提示，不删除）
try:
	list_cmd = on_command("migrate_list_local", aliases={"列出迁移插件"}, priority=10, block=True)
except Exception:
	list_cmd = None

if list_cmd is not None:
	@list_cmd.handle()
	async def handle_list_local():
		"""
		列出当前项目内疑似由迁移脚本生成的第三方插件副本。
		
		仅输出路径与包名，不做任何删除操作，方便你手动清理/重迁。
		"""
		migrated = list_local_migrated_plugins()
		if not migrated:
			await list_cmd.finish("当前未发现带有「移植自 nonebot-plugin」标记的本地迁移插件。")
		
		lines = ["以下是疑似由迁移脚本生成的本地插件（仅供参考，请自行确认后手动删除）:"]
		for name, path in migrated.items():
			lines.append(f"- {name}: {path}")
		lines.append("\n💡 建议：确认无用后，可手动删除对应目录，并使用新的迁移脚本重新迁移。")
		
		await list_cmd.finish("\n".join(lines))

