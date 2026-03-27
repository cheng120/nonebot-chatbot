"""
集成测试
测试模块之间的集成
"""
import pytest
import asyncio
from config import load_config
from src.database.connection import DatabaseManager
from src.services.plugin_manager import PluginManager
from src.services.status_manager import StatusManager


class TestDatabaseIntegration:
	"""数据库集成测试"""
	
	@pytest.mark.asyncio
	async def test_database_and_plugin_manager(self, test_config):
		"""测试数据库和插件管理器的集成"""
		# 初始化数据库
		db_manager = DatabaseManager(test_config.database)
		await db_manager.init_db()
		
		try:
			# 创建插件管理器
			plugin_manager = PluginManager(test_config.plugins.dir, db_manager)
			
			# 测试获取启用的插件（应该为空）
			enabled = await plugin_manager._get_enabled_plugins()
			assert isinstance(enabled, list)
		finally:
			# 清理
			await db_manager.close()
	
	@pytest.mark.asyncio
	async def test_full_workflow(self, test_config):
		"""测试完整工作流程"""
		# 1. 初始化数据库
		db_manager = DatabaseManager(test_config.database)
		await db_manager.init_db()
		
		try:
			# 2. 创建插件配置
			async with db_manager.get_session() as session:
				from src.database.plugin_config import PluginConfig, PluginStatus
				
				await PluginConfig.create_or_update(
					session,
					"test_plugin",
					enabled=True,
					config_data={"test": "value"}
				)
				await session.commit()
				
				await PluginStatus.update_status(session, "test_plugin", "enabled")
				await session.commit()
			
			# 3. 使用插件管理器
			plugin_manager = PluginManager(test_config.plugins.dir, db_manager)
			
			# 4. 获取插件配置
			config = await plugin_manager.get_plugin_config("test_plugin")
			assert config is not None
			assert config["enabled"] is True
			
			# 5. 更新插件配置
			new_config = {"new_key": "new_value"}
			result = await plugin_manager.update_plugin_config("test_plugin", new_config)
			assert result is True
			
			# 6. 验证更新
			updated_config = await plugin_manager.get_plugin_config("test_plugin")
			assert updated_config["config_data"]["new_key"] == "new_value"
		finally:
			# 清理
			await db_manager.close()


class TestConfigIntegration:
	"""配置集成测试"""
	
	def test_config_and_database(self, test_config):
		"""测试配置和数据库的集成"""
		# 验证配置中的数据库设置
		assert test_config.database.type == "sqlite"
		assert test_config.database.sqlite_path is not None
		
		# 创建数据库管理器
		db_manager = DatabaseManager(test_config.database)
		assert db_manager.config.type == "sqlite"
	
	def test_config_and_plugin_manager(self, test_config):
		"""测试配置和插件管理器的集成"""
		plugin_manager = PluginManager(test_config.plugins.dir)
		assert str(plugin_manager.plugin_dir) == test_config.plugins.dir
	
	def test_config_and_status_manager(self, test_config):
		"""测试配置和状态管理器的集成"""
		status_manager = StatusManager(test_config.status.check_interval)
		assert status_manager.check_interval == test_config.status.check_interval

