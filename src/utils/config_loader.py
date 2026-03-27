"""
配置加载工具
支持从YAML文件和环境变量加载配置
环境变量优先级高于配置文件
"""
import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv
from loguru import logger


def load_yaml_config(config_path: str) -> Dict[str, Any]:
	"""
	加载YAML配置文件
	
	Args:
		config_path: 配置文件路径
		
	Returns:
		配置字典
	"""
	try:
		with open(config_path, "r", encoding="utf-8") as f:
			config = yaml.safe_load(f) or {}
		logger.info(f"成功加载配置文件: {config_path}")
		# 调试：打印插件配置
		if "plugins" in config:
			logger.info(f"YAML 中的插件配置: {config['plugins']}")
			logger.info(f"YAML 中的 enabled: {config['plugins'].get('enabled')}")
			logger.info(f"YAML 中的 enabled 类型: {type(config['plugins'].get('enabled'))}")
		return config
	except FileNotFoundError:
		logger.warning(f"配置文件不存在: {config_path}，使用默认配置")
		return {}
	except Exception as e:
		logger.error(f"加载配置文件失败: {e}")
		return {}


def load_env_config() -> Dict[str, Any]:
	"""
	从环境变量加载配置
	环境变量命名规则：
	- 使用下划线分隔，全大写
	- 嵌套配置使用双下划线分隔，如 DATABASE__TYPE
	
	Returns:
		配置字典
	"""
	# 加载.env文件
	env_file = Path(".env")
	if env_file.exists():
		load_dotenv(env_file)
	
	config = {}
	
	# NoneBot配置
	if os.getenv("NONEBOT_DRIVER"):
		config.setdefault("driver", os.getenv("NONEBOT_DRIVER"))
	if os.getenv("NONEBOT_LOG_LEVEL"):
		config.setdefault("log", {}).setdefault("level", os.getenv("NONEBOT_LOG_LEVEL"))
	if os.getenv("NONEBOT_LOG_CONSOLE"):
		config.setdefault("log", {}).setdefault("console", os.getenv("NONEBOT_LOG_CONSOLE").lower() == "true")
	if os.getenv("NONEBOT_LOG_FILE"):
		config.setdefault("log", {}).setdefault("file", os.getenv("NONEBOT_LOG_FILE").lower() == "true")
	if os.getenv("NONEBOT_LOG_FILE_PATH"):
		config.setdefault("log", {}).setdefault("file_path", os.getenv("NONEBOT_LOG_FILE_PATH"))
	if os.getenv("NONEBOT_LOG_FILE_ROTATION"):
		config.setdefault("log", {}).setdefault("file_rotation", os.getenv("NONEBOT_LOG_FILE_ROTATION"))
	if os.getenv("NONEBOT_LOG_FILE_RETENTION"):
		config.setdefault("log", {}).setdefault("file_retention", os.getenv("NONEBOT_LOG_FILE_RETENTION"))
	
	# OneBot配置
	if os.getenv("ONEBOT_API_ROOT"):
		config.setdefault("adapters", [{}])[0].setdefault("api_root", os.getenv("ONEBOT_API_ROOT"))
	if os.getenv("ONEBOT_ACCESS_TOKEN"):
		config.setdefault("adapters", [{}])[0].setdefault("access_token", os.getenv("ONEBOT_ACCESS_TOKEN"))
	if os.getenv("ONEBOT_WS_URL"):
		config.setdefault("adapters", [{}])[0].setdefault("websocket", {}).setdefault("url", os.getenv("ONEBOT_WS_URL"))
	if os.getenv("ONEBOT_WS_ACCESS_TOKEN"):
		config.setdefault("adapters", [{}])[0].setdefault("websocket", {}).setdefault("access_token", os.getenv("ONEBOT_WS_ACCESS_TOKEN"))
	
	# 数据库配置
	if os.getenv("DATABASE_TYPE"):
		config.setdefault("database", {}).setdefault("type", os.getenv("DATABASE_TYPE"))
	if os.getenv("DATABASE_SQLITE_PATH"):
		config.setdefault("database", {}).setdefault("sqlite", {}).setdefault("path", os.getenv("DATABASE_SQLITE_PATH"))
	if os.getenv("DATABASE_MYSQL_HOST"):
		config.setdefault("database", {}).setdefault("mysql", {}).setdefault("host", os.getenv("DATABASE_MYSQL_HOST"))
	if os.getenv("DATABASE_MYSQL_PORT"):
		config.setdefault("database", {}).setdefault("mysql", {}).setdefault("port", int(os.getenv("DATABASE_MYSQL_PORT")))
	if os.getenv("DATABASE_MYSQL_USER"):
		config.setdefault("database", {}).setdefault("mysql", {}).setdefault("user", os.getenv("DATABASE_MYSQL_USER"))
	if os.getenv("DATABASE_MYSQL_PASSWORD"):
		config.setdefault("database", {}).setdefault("mysql", {}).setdefault("password", os.getenv("DATABASE_MYSQL_PASSWORD"))
	if os.getenv("DATABASE_MYSQL_DATABASE"):
		config.setdefault("database", {}).setdefault("mysql", {}).setdefault("database", os.getenv("DATABASE_MYSQL_DATABASE"))
	if os.getenv("DATABASE_MYSQL_CHARSET"):
		config.setdefault("database", {}).setdefault("mysql", {}).setdefault("charset", os.getenv("DATABASE_MYSQL_CHARSET"))
	
	# 插件配置
	if os.getenv("PLUGINS_DIR"):
		config.setdefault("plugins", {}).setdefault("dir", os.getenv("PLUGINS_DIR"))
	if os.getenv("PLUGINS_AUTO_RELOAD"):
		config.setdefault("plugins", {}).setdefault("auto_reload", os.getenv("PLUGINS_AUTO_RELOAD").lower() == "true")
	
	# 重试配置
	if os.getenv("RETRY_ENABLED"):
		config.setdefault("retry", {}).setdefault("enabled", os.getenv("RETRY_ENABLED").lower() == "true")
	if os.getenv("RETRY_MAX_ATTEMPTS"):
		config.setdefault("retry", {}).setdefault("max_attempts", int(os.getenv("RETRY_MAX_ATTEMPTS")))
	if os.getenv("RETRY_INTERVAL"):
		config.setdefault("retry", {}).setdefault("interval", float(os.getenv("RETRY_INTERVAL")))
	
	# 状态监控配置
	if os.getenv("STATUS_ENABLED"):
		config.setdefault("status", {}).setdefault("enabled", os.getenv("STATUS_ENABLED").lower() == "true")
	if os.getenv("STATUS_CHECK_INTERVAL"):
		config.setdefault("status", {}).setdefault("check_interval", int(os.getenv("STATUS_CHECK_INTERVAL")))
	
	return config


def merge_config(yaml_config: Dict[str, Any], env_config: Dict[str, Any]) -> Dict[str, Any]:
	"""
	合并配置
	环境变量优先级高于配置文件
	
	Args:
		yaml_config: YAML配置
		env_config: 环境变量配置
		
	Returns:
		合并后的配置
	"""
	def deep_merge(base: Dict, override: Dict) -> Dict:
		"""深度合并字典"""
		result = base.copy()
		for key, value in override.items():
			if key in result and isinstance(result[key], dict) and isinstance(value, dict):
				# 深度合并字典
				result[key] = deep_merge(result[key], value)
			elif key in result and isinstance(result[key], list) and isinstance(value, list):
				# 对于列表，环境变量覆盖（而不是合并）
				result[key] = value
			else:
				# 其他情况，环境变量覆盖
				result[key] = value
		return result
	
	# 先合并YAML配置，再用环境变量覆盖
	merged = deep_merge(yaml_config, env_config)
	
	# 调试：打印合并后的插件配置
	if "plugins" in merged:
		logger.info(f"合并后的插件配置: {merged['plugins']}")
		logger.info(f"合并后的 enabled: {merged['plugins'].get('enabled')}")
		logger.info(f"合并后的 enabled 类型: {type(merged['plugins'].get('enabled'))}")
		# 确保 enabled 和 disabled 是列表
		if isinstance(merged["plugins"], dict):
			if "enabled" in merged["plugins"] and not isinstance(merged["plugins"]["enabled"], list):
				if merged["plugins"]["enabled"] is None:
					merged["plugins"]["enabled"] = []
				else:
					merged["plugins"]["enabled"] = [merged["plugins"]["enabled"]]
			if "disabled" in merged["plugins"] and not isinstance(merged["plugins"]["disabled"], list):
				if merged["plugins"]["disabled"] is None:
					merged["plugins"]["disabled"] = []
				else:
					merged["plugins"]["disabled"] = [merged["plugins"]["disabled"]]
	
	return merged

