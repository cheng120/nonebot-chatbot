"""
配置管理模块
提供配置加载、验证和管理功能
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, field_validator
from src.utils.config_loader import load_yaml_config, load_env_config, merge_config


# 全局配置实例
_config_instance: Optional["BotConfig"] = None


class LogConfig(BaseModel):
	"""日志配置"""
	level: str = Field(default="INFO", description="日志级别")
	console: bool = Field(default=True, description="是否输出到控制台")
	file: bool = Field(default=True, description="是否输出到文件")
	file_path: str = Field(default="./logs/bot.log", description="日志文件路径")
	file_rotation: str = Field(default="10 MB", description="日志轮转：按大小如 '10 MB' 或按时间如 '1 day'，到达后新文件、旧文件自动改名保留")
	file_retention: str = Field(default="7 days", description="日志保留时间")
	
	@field_validator("level")
	@classmethod
	def validate_level(cls, v: str) -> str:
		"""验证日志级别"""
		valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
		if v.upper() not in valid_levels:
			raise ValueError(f"日志级别必须是 {valid_levels} 之一")
		return v.upper()


class WebSocketConfig(BaseModel):
	"""WebSocket配置"""
	url: str = Field(default="ws://127.0.0.1:3001", description="WebSocket地址")
	access_token: str = Field(default="", description="WebSocket访问令牌")


class AdapterConfig(BaseModel):
	"""适配器配置"""
	name: str = Field(default="OneBot V11", description="适配器名称")
	api_root: Optional[str] = Field(default=None, description="HTTP API地址（可选，如果使用WebSocket可以留空）")
	access_token: str = Field(default="", description="访问令牌")
	websocket: WebSocketConfig = Field(default_factory=WebSocketConfig, description="WebSocket配置")


class DatabaseConfig(BaseModel):
	"""数据库配置"""
	type: str = Field(default="sqlite", description="数据库类型")
	sqlite: Dict[str, Any] = Field(default_factory=lambda: {
		"path": "./data/bot.db"
	}, description="SQLite配置")
	mysql: Dict[str, Any] = Field(default_factory=lambda: {
		"host": "localhost",
		"port": 3306,
		"user": "root",
		"password": "",
		"database": "nonebot_chatbot",
		"charset": "utf8mb4"
	}, description="MySQL配置")
	
	@field_validator("type")
	@classmethod
	def validate_type(cls, v: str) -> str:
		"""验证数据库类型"""
		valid_types = ["sqlite", "mysql"]
		if v.lower() not in valid_types:
			raise ValueError(f"数据库类型必须是 {valid_types} 之一")
		return v.lower()
	
	@property
	def sqlite_path(self) -> str:
		"""获取SQLite路径"""
		return self.sqlite.get("path", "./data/bot.db")
	
	@property
	def mysql_host(self) -> str:
		"""获取MySQL主机"""
		return self.mysql.get("host", "localhost")
	
	@property
	def mysql_port(self) -> int:
		"""获取MySQL端口"""
		return self.mysql.get("port", 3306)


class MessageLogConfig(BaseModel):
	"""消息日志配置"""
	enabled: bool = Field(default=True, description="是否启用消息日志")
	log_to_file: bool = Field(default=True, description="是否记录到文件")
	log_to_database: bool = Field(default=True, description="是否记录到数据库")
	file_path: str = Field(default="./logs/messages.log", description="消息日志文件路径")
	level: str = Field(default="INFO", description="消息日志级别（DEBUG, INFO, WARNING, ERROR）")
	
	@field_validator("level")
	@classmethod
	def validate_level(cls, v: str) -> str:
		"""验证日志级别"""
		valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
		if v.upper() not in valid_levels:
			raise ValueError(f"日志级别必须是 {valid_levels} 之一")
		return v.upper()


class PluginsConfig(BaseModel):
	"""插件配置"""
	dir: str = Field(default="./src/plugins", description="插件目录")
	auto_reload: bool = Field(default=False, description="是否自动重载")
	enabled: List[str] = Field(default_factory=list, description="启用的插件列表（从配置文件）")
	disabled: List[str] = Field(default_factory=list, description="禁用的插件列表（从配置文件）")
	use_config_file: bool = Field(default=True, description="是否使用配置文件管理插件（True: 配置文件优先, False: 仅使用数据库）")


class RetryConfig(BaseModel):
	"""重试配置"""
	enabled: bool = Field(default=True, description="是否启用重试")
	max_attempts: int = Field(default=3, description="最大重试次数")
	interval: float = Field(default=1.0, description="重试间隔（秒）")


class StatusConfig(BaseModel):
	"""状态监控配置"""
	enabled: bool = Field(default=True, description="是否启用状态监控")
	check_interval: int = Field(default=60, description="状态检查间隔（秒）")


class BotConfig(BaseModel):
	"""机器人配置"""
	driver: str = Field(default="~fastapi", description="驱动类型")
	log: LogConfig = Field(default_factory=LogConfig, description="日志配置")
	message_log: MessageLogConfig = Field(default_factory=MessageLogConfig, description="消息日志配置")
	adapters: List[AdapterConfig] = Field(default_factory=lambda: [AdapterConfig()], description="适配器配置列表")
	database: DatabaseConfig = Field(default_factory=DatabaseConfig, description="数据库配置")
	plugins: PluginsConfig = Field(default_factory=PluginsConfig, description="插件配置")
	retry: RetryConfig = Field(default_factory=RetryConfig, description="重试配置")
	status: StatusConfig = Field(default_factory=StatusConfig, description="状态监控配置")
	
	@field_validator("driver")
	@classmethod
	def validate_driver(cls, v: str) -> str:
		"""验证驱动格式"""
		if not v.startswith("~"):
			raise ValueError("驱动类型必须以 ~ 开头，例如: ~fastapi")
		return v
	
	class Config:
		"""Pydantic配置"""
		extra = "allow"  # 允许额外字段


def load_config(config_path: Optional[str] = None, force_reload: bool = False) -> BotConfig:
	"""
	加载配置
	
	Args:
		config_path: 配置文件路径（默认: configs/config.yaml）
		force_reload: 是否强制重新加载
		
	Returns:
		配置对象
	"""
	global _config_instance
	
	# 如果已加载且不强制重载，返回现有配置
	if _config_instance is not None and not force_reload:
		return _config_instance
	
	# 确定配置文件路径
	if config_path is None:
		# 默认使用项目根目录下的 configs/config.yaml
		project_root = Path(__file__).parent
		config_path = str(project_root / "configs" / "config.yaml")
	
	# 加载YAML配置
	yaml_config = load_yaml_config(config_path)
	
	# 加载环境变量配置
	env_config = load_env_config()
	
	# 合并配置（环境变量优先）
	merged_config = merge_config(yaml_config, env_config)
	
	# 调试：打印驱动配置
	if "driver" in merged_config:
		from loguru import logger
		logger.info(f"从配置文件加载的驱动: {merged_config['driver']}")
	
	# 调试：打印插件配置
	if "plugins" in merged_config:
		from loguru import logger
		logger.debug(f"合并后的插件配置: {merged_config['plugins']}")
		logger.debug(f"enabled 列表: {merged_config['plugins'].get('enabled', [])}")
		logger.debug(f"enabled 类型: {type(merged_config['plugins'].get('enabled', []))}")
	
	# 确保 adapters 是列表格式
	if "adapters" in merged_config and isinstance(merged_config["adapters"], list):
		# 处理每个适配器配置
		for adapter in merged_config["adapters"]:
			if isinstance(adapter, dict):
				# 处理 api_root：如果为空字符串或 None，转换为 None
				if "api_root" in adapter:
					if adapter["api_root"] == "" or adapter["api_root"] is None:
						adapter["api_root"] = None
				
				# 处理 websocket：确保是字典格式（Pydantic会自动转换）
				if "websocket" in adapter:
					if isinstance(adapter["websocket"], dict):
						# websocket 已经是字典，Pydantic会自动转换为 WebSocketConfig
						pass
					elif not isinstance(adapter["websocket"], dict):
						# 如果不是字典，尝试转换
						adapter["websocket"] = {"url": "", "access_token": ""}
	
	# 创建配置对象
	try:
		# 调试：打印插件配置
		if "plugins" in merged_config:
			from loguru import logger
			logger.info(f"创建 BotConfig 前的插件配置: {merged_config['plugins']}")
			logger.info(f"enabled 值: {merged_config['plugins'].get('enabled')}")
			logger.info(f"enabled 类型: {type(merged_config['plugins'].get('enabled'))}")
			
			# 确保 enabled 和 disabled 是列表
			if isinstance(merged_config["plugins"], dict):
				# 处理 enabled 字段
				if "enabled" not in merged_config["plugins"]:
					merged_config["plugins"]["enabled"] = []
				else:
					enabled = merged_config["plugins"]["enabled"]
					if enabled is None:
						merged_config["plugins"]["enabled"] = []
					elif not isinstance(enabled, list):
						merged_config["plugins"]["enabled"] = [enabled] if enabled else []
					logger.info(f"处理后的 enabled: {merged_config['plugins']['enabled']}")
				
				# 处理 disabled 字段
				if "disabled" not in merged_config["plugins"]:
					merged_config["plugins"]["disabled"] = []
				else:
					disabled = merged_config["plugins"]["disabled"]
					if disabled is None:
						merged_config["plugins"]["disabled"] = []
					elif not isinstance(disabled, list):
						merged_config["plugins"]["disabled"] = [disabled] if disabled else []
					logger.info(f"处理后的 disabled: {merged_config['plugins']['disabled']}")
		
		_config_instance = BotConfig(**merged_config)
		
		# 调试：打印创建后的插件配置
		if _config_instance.plugins:
			from loguru import logger
			logger.info(f"创建 BotConfig 后的插件配置: enabled={_config_instance.plugins.enabled}, disabled={_config_instance.plugins.disabled}")
		
		return _config_instance
	except Exception as e:
		# 如果配置加载失败，使用默认配置
		from loguru import logger
		logger.error(f"配置加载失败，使用默认配置: {e}", exc_info=True)
		_config_instance = BotConfig()
		return _config_instance


def get_config() -> BotConfig:
	"""
	获取配置单例
	
	Returns:
		配置对象
	"""
	global _config_instance
	
	if _config_instance is None:
		_config_instance = load_config()
	
	return _config_instance


def reset_config():
	"""重置配置（主要用于测试）"""
	global _config_instance
	_config_instance = None

