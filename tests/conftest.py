"""
pytest配置文件
提供测试用的fixtures和配置
"""
import pytest
import os
import tempfile
import shutil
from pathlib import Path
from config import BotConfig, load_config
from src.database.connection import DatabaseManager
from src.utils.logger import setup_logger


@pytest.fixture(scope="session")
def test_config():
	"""测试配置"""
	# 创建临时目录
	temp_dir = tempfile.mkdtemp()
	
	# 测试配置
	config_dict = {
		"driver": "~fastapi",
		"log": {
			"level": "DEBUG",
			"console": True,
			"file": False,
			"file_path": os.path.join(temp_dir, "test.log"),
			"file_rotation": "1 day",
			"file_retention": "7 days"
		},
		"adapters": [{
			"name": "OneBot V11",
			"api_root": "http://localhost:5700",
			"access_token": "",
			"websocket": {
				"url": "ws://localhost:6700",
				"access_token": ""
			}
		}],
		"database": {
			"type": "sqlite",
			"sqlite": {
				"path": os.path.join(temp_dir, "test.db")
			},
			"mysql": {
				"host": "localhost",
				"port": 3306,
				"user": "root",
				"password": "",
				"database": "test_nonebot",
				"charset": "utf8mb4"
			}
		},
		"plugins": {
			"dir": os.path.join(temp_dir, "plugins"),
			"auto_reload": False
		},
		"retry": {
			"enabled": True,
			"max_attempts": 3,
			"interval": 0.1
		},
		"status": {
			"enabled": True,
			"check_interval": 5
		}
	}
	
	config = BotConfig(**config_dict)
	
	yield config
	
	# 清理临时目录
	shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture(scope="function")
def db_manager(test_config):
	"""数据库管理器fixture"""
	manager = DatabaseManager(test_config.database)
	yield manager
	# 清理
	import asyncio
	try:
		asyncio.run(manager.close())
	except:
		pass


@pytest.fixture(scope="function")
async def db_session(db_manager):
	"""数据库会话fixture"""
	# 先初始化数据库
	await db_manager.init_db()
	async with db_manager.get_session() as session:
		yield session


@pytest.fixture(scope="session", autouse=True)
def setup_test_logging(test_config):
	"""设置测试日志"""
	try:
		setup_logger(test_config.log)
	except Exception:
		# 如果日志设置失败，不影响测试
		pass


@pytest.fixture
def temp_plugin_dir():
	"""临时插件目录"""
	temp_dir = tempfile.mkdtemp()
	plugin_dir = Path(temp_dir) / "plugins"
	plugin_dir.mkdir(parents=True, exist_ok=True)
	yield plugin_dir
	shutil.rmtree(temp_dir, ignore_errors=True)

