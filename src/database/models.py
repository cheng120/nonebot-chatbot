"""
数据库模型基类
"""
from datetime import datetime
from sqlalchemy import Column, DateTime
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
	"""数据库模型基类"""
	pass


class TimestampMixin:
	"""时间戳混入类"""
	created_at = Column(DateTime, default=datetime.now, nullable=False)
	updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

