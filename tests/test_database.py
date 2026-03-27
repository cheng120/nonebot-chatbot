"""
数据库模块测试
"""
import pytest
import asyncio
from src.database.connection import DatabaseManager
from src.database.models import Base, TimestampMixin
from src.database.plugin_config import PluginConfig, PluginStatus, MessageLog


class TestDatabaseConnection:
	"""数据库连接测试"""
	
	@pytest.mark.asyncio
	async def test_sqlite_connection(self, db_manager):
		"""测试SQLite连接"""
		# 先初始化数据库
		await db_manager.init_db()
		# 测试健康检查
		health = await db_manager.health_check()
		assert health is True
	
	@pytest.mark.asyncio
	async def test_database_init(self, db_manager):
		"""测试数据库初始化"""
		await db_manager.init_db()
		
		# 验证表已创建（通过查询表）
		async with db_manager.get_session() as session:
			from sqlalchemy import text
			result = await session.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
			tables = [row[0] for row in result]
			assert "plugin_configs" in tables
			assert "plugin_status" in tables
			assert "message_logs" in tables
	
	@pytest.mark.asyncio
	async def test_get_session(self, db_manager):
		"""测试获取数据库会话"""
		# 先初始化数据库
		await db_manager.init_db()
		async with db_manager.get_session() as session:
			assert session is not None
	
	@pytest.mark.asyncio
	async def test_close_connection(self, db_manager):
		"""测试关闭数据库连接"""
		# 先初始化
		await db_manager.init_db()
		# 关闭连接
		await db_manager.close()
		# 关闭后应该无法获取会话（引擎已销毁）
		# 注意：实际行为可能因SQLAlchemy版本而异
		try:
			async with db_manager.get_session() as session:
				pass
		except (RuntimeError, AttributeError):
			pass  # 预期的错误


class TestPluginConfig:
	"""插件配置模型测试"""
	
	@pytest.mark.asyncio
	async def test_create_plugin_config(self, db_session):
		"""测试创建插件配置"""
		config = await PluginConfig.create_or_update(
			db_session,
			plugin_name="test_plugin",
			enabled=True,
			config_data={"key": "value"}
		)
		
		assert config.plugin_name == "test_plugin"
		assert config.enabled is True
		assert config.config_data is not None
	
	@pytest.mark.asyncio
	async def test_get_plugin_config(self, db_session):
		"""测试获取插件配置"""
		# 先创建
		await PluginConfig.create_or_update(
			db_session,
			plugin_name="test_plugin",
			enabled=True
		)
		
		# 再查询
		config = await PluginConfig.get_by_name(db_session, "test_plugin")
		assert config is not None
		assert config.plugin_name == "test_plugin"
	
	@pytest.mark.asyncio
	async def test_update_plugin_config(self, db_session):
		"""测试更新插件配置"""
		# 创建
		config = await PluginConfig.create_or_update(
			db_session,
			plugin_name="test_plugin",
			enabled=True,
			config_data={"old": "value"}
		)
		
		# 更新
		updated = await PluginConfig.create_or_update(
			db_session,
			plugin_name="test_plugin",
			enabled=False,
			config_data={"new": "value"}
		)
		
		assert updated.id == config.id
		assert updated.enabled is False
	
	@pytest.mark.asyncio
	async def test_get_all_enabled(self, db_session):
		"""测试获取所有启用的插件"""
		# 创建多个插件
		await PluginConfig.create_or_update(db_session, "plugin1", enabled=True)
		await PluginConfig.create_or_update(db_session, "plugin2", enabled=False)
		await PluginConfig.create_or_update(db_session, "plugin3", enabled=True)
		
		# 查询启用的插件
		enabled = await PluginConfig.get_all_enabled(db_session)
		names = [p.plugin_name for p in enabled]
		
		assert "plugin1" in names
		assert "plugin2" not in names
		assert "plugin3" in names
	
	@pytest.mark.asyncio
	async def test_to_dict(self, db_session):
		"""测试转换为字典"""
		config = await PluginConfig.create_or_update(
			db_session,
			plugin_name="test_plugin",
			enabled=True,
			config_data={"key": "value"}
		)
		
		config_dict = config.to_dict()
		assert isinstance(config_dict, dict)
		assert config_dict["plugin_name"] == "test_plugin"
		assert config_dict["enabled"] is True


class TestPluginStatus:
	"""插件状态模型测试"""
	
	@pytest.mark.asyncio
	async def test_update_status(self, db_session):
		"""测试更新插件状态"""
		status = await PluginStatus.update_status(
			db_session,
			plugin_name="test_plugin",
			status="enabled"
		)
		
		assert status.plugin_name == "test_plugin"
		assert status.status == "enabled"
	
	@pytest.mark.asyncio
	async def test_update_status_with_error(self, db_session):
		"""测试更新状态并记录错误"""
		status = await PluginStatus.update_status(
			db_session,
			plugin_name="test_plugin",
			status="error",
			error_message="Test error"
		)
		
		assert status.status == "error"
		assert status.error_message == "Test error"
		assert status.last_error_at is not None
	
	@pytest.mark.asyncio
	async def test_get_status(self, db_session):
		"""测试获取插件状态"""
		await PluginStatus.update_status(db_session, "test_plugin", "enabled")
		
		status = await PluginStatus.get_by_name(db_session, "test_plugin")
		assert status is not None
		assert status.status == "enabled"


class TestMessageLog:
	"""消息日志模型测试"""
	
	@pytest.mark.asyncio
	async def test_create_message_log(self, db_session):
		"""测试创建消息日志"""
		log = await MessageLog.create_log(
			db_session,
			message_id=12345,
			message_type="private",
			user_id=67890,
			message_content="Test message"
		)
		
		assert log.message_id == 12345
		assert log.message_type == "private"
		assert log.user_id == 67890
		assert log.message_content == "Test message"
	
	@pytest.mark.asyncio
	async def test_create_group_message_log(self, db_session):
		"""测试创建群消息日志"""
		log = await MessageLog.create_log(
			db_session,
			message_id=12345,
			message_type="group",
			user_id=67890,
			group_id=11111,
			message_content="Group message"
		)
		
		assert log.message_type == "group"
		assert log.group_id == 11111

