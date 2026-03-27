"""
日志工具模块
支持控制台输出和文件存储，支持日志轮转和日志级别控制
"""
import sys
from pathlib import Path
from loguru import logger
from typing import Optional


def setup_logger(config) -> None:
	"""
	设置日志系统
	
	Args:
		config: 日志配置对象（LogConfig）
	"""
	# 移除默认处理器
	logger.remove()
	
	# 添加控制台输出
	if config.console:
		logger.add(
			sys.stdout,
			level=config.level,
			format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
			colorize=True
		)
	
	# 添加文件输出（达到 rotation 时新文件、旧文件自动改名为 .1.zip / 按时间戳等）
	if config.file:
		# 确保日志目录存在
		log_file_path = Path(config.file_path)
		log_file_path.parent.mkdir(parents=True, exist_ok=True)
		# rotation 支持按大小如 "10 MB" 或按时间如 "1 day"，到达后新文件、旧文件自动改名
		logger.add(
			config.file_path,
			level=config.level,
			rotation=config.file_rotation,
			retention=config.file_retention,
			format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
			encoding="utf-8",
			compression="zip"  # 旧文件改名后压缩为 .zip
		)
	
	logger.info("日志系统初始化完成")


def get_logger(name: Optional[str] = None):
	"""
	获取日志记录器
	
	Args:
		name: 日志记录器名称，默认为调用模块名
		
	Returns:
		日志记录器
	"""
	if name:
		return logger.bind(name=name)
	return logger

