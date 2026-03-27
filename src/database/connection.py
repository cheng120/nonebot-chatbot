"""
数据库连接管理模块
支持SQLite和MySQL两种数据库类型
"""
import os
from typing import Optional
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text
from loguru import logger


class DatabaseManager:
	"""数据库管理器"""
	
	def __init__(self, config):
		"""
		初始化数据库管理器
		
		Args:
			config: 数据库配置对象
		"""
		self.config = config
		self.engine = None
		self.async_session_maker: Optional[async_sessionmaker] = None
		self._init_engine()
	
	def _init_engine(self):
		"""根据配置创建数据库引擎"""
		db_type = self.config.type.lower()
		
		if db_type == "sqlite":
			# SQLite连接
			db_path = self.config.sqlite_path or "./data/bot.db"
			# 确保目录存在
			os.makedirs(os.path.dirname(db_path), exist_ok=True)
			# SQLite使用aiosqlite驱动
			database_url = f"sqlite+aiosqlite:///{db_path}"
			logger.info(f"初始化SQLite数据库: {db_path}")
		elif db_type == "mysql":
			# MySQL连接
			host = self.config.mysql_host or "localhost"
			port = self.config.mysql_port or 3306
			user = self.config.mysql_user or "root"
			password = self.config.mysql_password or ""
			database = self.config.mysql_database or "nonebot_chatbot"
			charset = self.config.mysql_charset or "utf8mb4"
			# MySQL使用pymysql驱动（同步版本，SQLAlchemy会自动处理）
			# 注意：SQLAlchemy 2.0+ 支持异步pymysql
			database_url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}?charset={charset}"
			logger.info(f"初始化MySQL数据库: {host}:{port}/{database}")
		else:
			raise ValueError(f"不支持的数据库类型: {db_type}，支持的类型: sqlite, mysql")
		
		# 创建异步引擎
		self.engine = create_async_engine(
			database_url,
			echo=False,  # 是否打印SQL语句
			future=True,
			pool_pre_ping=True,  # 连接健康检查
			pool_recycle=3600,  # 连接回收时间（秒）
		)
		
		# 创建异步会话工厂
		self.async_session_maker = async_sessionmaker(
			self.engine,
			class_=AsyncSession,
			expire_on_commit=False
		)
	
	async def init_db(self):
		"""
		初始化数据库（创建表结构）
		使用ORM模型创建表，如果失败则使用SQL迁移脚本
		"""
		try:
			# 首先尝试使用ORM模型创建表
			from .models import Base
			from .plugin_config import PluginConfig, PluginStatus, MessageLog
			
			async with self.engine.begin() as conn:
				# 使用ORM创建所有表
				await conn.run_sync(Base.metadata.create_all)
			
			logger.info("数据库初始化完成（使用ORM模型）")
		except Exception as orm_error:
			logger.warning(f"ORM方式创建表失败: {orm_error}，尝试使用SQL迁移脚本")
			
			# 如果ORM方式失败，回退到SQL脚本
			try:
				# 读取迁移脚本
				migration_file = os.path.join(
					os.path.dirname(__file__),
					"migrations",
					"001_init_tables.sql"
				)
				
				if not os.path.exists(migration_file):
					logger.warning(f"迁移脚本不存在: {migration_file}")
					raise orm_error  # 抛出原始错误
				
				with open(migration_file, "r", encoding="utf-8") as f:
					sql_content = f.read()
				
				# 分割SQL语句（按分号分割，但要注意SQLite和MySQL的差异）
				# 简单处理：按分号分割，过滤空语句
				sql_statements = [
					stmt.strip()
					for stmt in sql_content.split(";")
					if stmt.strip() and not stmt.strip().startswith("--")
				]
				
				async with self.engine.begin() as conn:
					for sql in sql_statements:
						if sql:
							# 处理SQLite和MySQL的语法差异
							# SQLite不支持AUTO_INCREMENT，使用AUTOINCREMENT
							# MySQL不支持AUTOINCREMENT，使用AUTO_INCREMENT
							if self.config.type.lower() == "sqlite":
								# SQLite语法调整
								sql = sql.replace("AUTO_INCREMENT", "AUTOINCREMENT")
								sql = sql.replace("ENGINE=InnoDB", "")
								sql = sql.replace("DEFAULT CHARSET=utf8mb4", "")
								# 处理COMMENT（SQLite不支持COMMENT，转换为注释）
								import re
								sql = re.sub(r"COMMENT\s+'([^']+)'", r"-- \1", sql)
							else:
								# MySQL语法（保持原样）
								pass
						
						await conn.execute(text(sql))
				
				logger.info("数据库初始化完成（使用SQL迁移脚本）")
			except Exception as sql_error:
				logger.error(f"数据库初始化失败: {sql_error}")
				raise
	
	def get_session(self):
		"""
		获取数据库会话生成器
		
		Returns:
			异步上下文管理器
		"""
		if not self.async_session_maker:
			raise RuntimeError("数据库未初始化")
		
		return self.async_session_maker()
	
	async def close(self):
		"""关闭数据库连接"""
		if self.engine:
			await self.engine.dispose()
			logger.info("数据库连接已关闭")
	
	async def health_check(self) -> bool:
		"""
		数据库健康检查
		
		Returns:
			bool: 连接是否正常
		"""
		try:
			async with self.engine.begin() as conn:
				await conn.execute(text("SELECT 1"))
			return True
		except Exception as e:
			logger.error(f"数据库健康检查失败: {e}")
			return False

