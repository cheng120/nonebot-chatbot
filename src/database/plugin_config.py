"""
插件配置相关数据库模型
"""
import json
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, BigInteger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from .models import Base, TimestampMixin
from loguru import logger


class PluginConfig(Base, TimestampMixin):
	"""插件配置模型"""
	__tablename__ = "plugin_configs"
	
	id = Column(Integer, primary_key=True, autoincrement=True)
	plugin_name = Column(String(255), unique=True, nullable=False)
	enabled = Column(Boolean, default=True, nullable=False)
	config_data = Column(Text)
	
	def to_dict(self) -> Dict[str, Any]:
		"""转换为字典"""
		return {
			"id": self.id,
			"plugin_name": self.plugin_name,
			"enabled": self.enabled,
			"config_data": json.loads(self.config_data) if self.config_data else {},
			"created_at": self.created_at.isoformat() if self.created_at else None,
			"updated_at": self.updated_at.isoformat() if self.updated_at else None,
		}
	
	@classmethod
	async def get_by_name(cls, session: AsyncSession, plugin_name: str) -> Optional["PluginConfig"]:
		"""根据插件名称获取配置"""
		try:
			result = await session.execute(
				select(cls).where(cls.plugin_name == plugin_name)
			)
			return result.scalar_one_or_none()
		except Exception as e:
			logger.error(f"查询插件配置失败: {e}")
			return None
	
	@classmethod
	async def create_or_update(
		cls,
		session: AsyncSession,
		plugin_name: str,
		enabled: bool = True,
		config_data: Optional[Dict[str, Any]] = None
	) -> "PluginConfig":
		"""创建或更新插件配置"""
		try:
			# 查询是否存在
			existing = await cls.get_by_name(session, plugin_name)
			
			if existing:
				# 更新
				existing.enabled = enabled
				if config_data is not None:
					existing.config_data = json.dumps(config_data, ensure_ascii=False)
				await session.commit()
				await session.refresh(existing)
				return existing
			else:
				# 创建
				new_config = cls(
					plugin_name=plugin_name,
					enabled=enabled,
					config_data=json.dumps(config_data or {}, ensure_ascii=False)
				)
				session.add(new_config)
				await session.commit()
				await session.refresh(new_config)
				return new_config
		except Exception as e:
			await session.rollback()
			logger.error(f"创建或更新插件配置失败: {e}")
			raise
	
	@classmethod
	async def get_all_enabled(cls, session: AsyncSession) -> list["PluginConfig"]:
		"""获取所有启用的插件配置"""
		try:
			result = await session.execute(
				select(cls).where(cls.enabled == True)
			)
			return list(result.scalars().all())
		except Exception as e:
			logger.error(f"查询启用的插件配置失败: {e}")
			return []


class PluginStatus(Base, TimestampMixin):
	"""插件状态模型"""
	__tablename__ = "plugin_status"
	
	id = Column(Integer, primary_key=True, autoincrement=True)
	plugin_name = Column(String(255), unique=True, nullable=False)
	status = Column(String(50), default="loaded", nullable=False)
	error_message = Column(Text)
	last_error_at = Column(DateTime)
	
	def to_dict(self) -> Dict[str, Any]:
		"""转换为字典"""
		return {
			"id": self.id,
			"plugin_name": self.plugin_name,
			"status": self.status,
			"error_message": self.error_message,
			"last_error_at": self.last_error_at.isoformat() if self.last_error_at else None,
			"created_at": self.created_at.isoformat() if self.created_at else None,
			"updated_at": self.updated_at.isoformat() if self.updated_at else None,
		}
	
	@classmethod
	async def get_by_name(cls, session: AsyncSession, plugin_name: str) -> Optional["PluginStatus"]:
		"""根据插件名称获取状态"""
		try:
			result = await session.execute(
				select(cls).where(cls.plugin_name == plugin_name)
			)
			return result.scalar_one_or_none()
		except Exception as e:
			logger.error(f"查询插件状态失败: {e}")
			return None
	
	@classmethod
	async def update_status(
		cls,
		session: AsyncSession,
		plugin_name: str,
		status: str,
		error_message: Optional[str] = None
	) -> "PluginStatus":
		"""更新插件状态"""
		try:
			existing = await cls.get_by_name(session, plugin_name)
			
			if existing:
				existing.status = status
				if error_message:
					existing.error_message = error_message
					existing.last_error_at = datetime.now()
				await session.commit()
				await session.refresh(existing)
				return existing
			else:
				new_status = cls(
					plugin_name=plugin_name,
					status=status,
					error_message=error_message,
					last_error_at=datetime.now() if error_message else None
				)
				session.add(new_status)
				await session.commit()
				await session.refresh(new_status)
				return new_status
		except Exception as e:
			await session.rollback()
			logger.error(f"更新插件状态失败: {e}")
			raise


class MessageLog(Base, TimestampMixin):
	"""消息日志模型（可选，用于调试）"""
	__tablename__ = "message_logs"
	
	id = Column(Integer, primary_key=True, autoincrement=True)
	message_id = Column(BigInteger)
	message_type = Column(String(50), nullable=False)
	user_id = Column(BigInteger)
	group_id = Column(BigInteger)
	message_content = Column(Text)
	
	def to_dict(self) -> Dict[str, Any]:
		"""转换为字典"""
		return {
			"id": self.id,
			"message_id": self.message_id,
			"message_type": self.message_type,
			"user_id": self.user_id,
			"group_id": self.group_id,
			"message_content": self.message_content,
			"created_at": self.created_at.isoformat() if self.created_at else None,
		}
	
	@classmethod
	async def create_log(
		cls,
		session: AsyncSession,
		message_id: Optional[int],
		message_type: str,
		user_id: Optional[int] = None,
		group_id: Optional[int] = None,
		message_content: Optional[str] = None
	) -> "MessageLog":
		"""创建消息日志"""
		try:
			new_log = cls(
				message_id=message_id,
				message_type=message_type,
				user_id=user_id,
				group_id=group_id,
				message_content=message_content
			)
			session.add(new_log)
			await session.commit()
			await session.refresh(new_log)
			return new_log
		except Exception as e:
			await session.rollback()
			logger.error(f"创建消息日志失败: {e}")
			raise

