"""
服务模块测试
"""
import pytest
import asyncio
from pathlib import Path
from src.services.plugin_manager import PluginManager
from src.services.status_manager import StatusManager


class TestPluginManager:
	"""插件管理器测试"""
	
	@pytest.mark.asyncio
	async def test_plugin_manager_init(self, temp_plugin_dir, db_manager):
		"""测试插件管理器初始化"""
		# 先初始化数据库
		await db_manager.init_db()
		manager = PluginManager(str(temp_plugin_dir), db_manager)
		assert str(manager.plugin_dir) == str(temp_plugin_dir)
		assert manager.db_manager == db_manager
	
	@pytest.mark.asyncio
	async def test_scan_plugin_dir(self, temp_plugin_dir):
		"""测试扫描插件目录"""
		manager = PluginManager(str(temp_plugin_dir))
		
		# 创建测试插件文件
		test_plugin = temp_plugin_dir / "test_plugin.py"
		test_plugin.write_text("# Test plugin")
		
		files = manager._scan_plugin_dir()
		assert len(files) >= 1
		assert any("test_plugin.py" in str(f) for f in files)
	
	@pytest.mark.asyncio
	async def test_get_enabled_plugins(self, db_manager, db_session):
		"""测试获取启用的插件列表"""
		from src.database.plugin_config import PluginConfig
		
		# 确保数据库已初始化
		await db_manager.init_db()
		
		# 创建测试插件配置
		await PluginConfig.create_or_update(db_session, "plugin1", enabled=True)
		await PluginConfig.create_or_update(db_session, "plugin2", enabled=False)
		
		# 提交事务
		await db_session.commit()
		
		manager = PluginManager("./src/plugins", db_manager)
		enabled = await manager._get_enabled_plugins()
		
		assert "plugin1" in enabled
		assert "plugin2" not in enabled
	
	@pytest.mark.asyncio
	async def test_enable_plugin(self, db_manager, db_session):
		"""测试启用插件"""
		# 确保数据库已初始化
		await db_manager.init_db()
		
		manager = PluginManager("./src/plugins", db_manager)
		
		result = await manager.enable_plugin("test_plugin")
		assert result is True
		
		# 验证数据库中的状态（需要新会话）
		async with db_manager.get_session() as new_session:
			from src.database.plugin_config import PluginConfig
			config = await PluginConfig.get_by_name(new_session, "test_plugin")
			assert config is not None
			assert config.enabled is True
	
	@pytest.mark.asyncio
	async def test_disable_plugin(self, db_manager, db_session):
		"""测试禁用插件"""
		# 确保数据库已初始化
		await db_manager.init_db()
		
		manager = PluginManager("./src/plugins", db_manager)
		
		# 先启用
		await manager.enable_plugin("test_plugin")
		
		# 再禁用
		result = await manager.disable_plugin("test_plugin")
		assert result is True
		
		# 验证数据库中的状态（需要新会话）
		async with db_manager.get_session() as new_session:
			from src.database.plugin_config import PluginConfig
			config = await PluginConfig.get_by_name(new_session, "test_plugin")
			assert config is not None
			assert config.enabled is False
	
	@pytest.mark.asyncio
	async def test_get_plugin_config(self, db_manager, db_session):
		"""测试获取插件配置"""
		# 确保数据库已初始化
		await db_manager.init_db()
		
		from src.database.plugin_config import PluginConfig
		
		# 创建配置
		await PluginConfig.create_or_update(
			db_session,
			"test_plugin",
			enabled=True,
			config_data={"key": "value"}
		)
		await db_session.commit()
		
		manager = PluginManager("./src/plugins", db_manager)
		config = await manager.get_plugin_config("test_plugin")
		
		assert config is not None
		assert config["plugin_name"] == "test_plugin"
		assert config["enabled"] is True
	
	@pytest.mark.asyncio
	async def test_update_plugin_config(self, db_manager, db_session):
		"""测试更新插件配置"""
		# 确保数据库已初始化
		await db_manager.init_db()
		
		manager = PluginManager("./src/plugins", db_manager)
		
		new_config = {"new_key": "new_value"}
		result = await manager.update_plugin_config("test_plugin", new_config)
		
		assert result is True
		
		# 验证配置已更新
		config = await manager.get_plugin_config("test_plugin")
		assert config is not None
		assert config["config_data"]["new_key"] == "new_value"


class TestStatusManager:
	"""状态管理器测试"""
	
	def test_status_manager_init(self):
		"""测试状态管理器初始化"""
		manager = StatusManager(check_interval=10)
		assert manager.check_interval == 10
		assert manager.status["running"] is False
	
	@pytest.mark.asyncio
	async def test_get_status(self):
		"""测试获取状态"""
		manager = StatusManager()
		status = manager.get_status()
		
		assert isinstance(status, dict)
		assert "running" in status
		assert "connected" in status
		assert "plugins_loaded" in status
	
	@pytest.mark.asyncio
	async def test_check_status(self):
		"""测试状态检查"""
		manager = StatusManager()
		
		# 由于没有实际的bot，连接检查会失败
		await manager.check_status()
		
		# 状态应该已更新
		assert manager.status["last_check"] is not None
	
	@pytest.mark.asyncio
	async def test_start_stop_monitoring(self):
		"""测试启动和停止监控"""
		manager = StatusManager(check_interval=0.1)
		
		# 启动监控
		task = asyncio.create_task(manager.start_monitoring())
		
		# 等待一小段时间
		await asyncio.sleep(0.2)
		
		# 验证监控已启动
		assert manager.status["running"] is True
		
		# 停止监控
		await manager.stop_monitoring()
		
		# 等待任务结束
		await asyncio.sleep(0.1)
		
		# 验证监控已停止
		assert manager.status["running"] is False
		
		# 取消任务（如果还在运行）
		if not task.done():
			task.cancel()
			try:
				await task
			except asyncio.CancelledError:
				pass

