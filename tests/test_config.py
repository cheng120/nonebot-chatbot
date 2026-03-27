"""
配置管理模块测试
"""
import pytest
import os
import tempfile
import yaml
from pathlib import Path
from config import BotConfig, load_config, get_config
from src.utils.config_loader import load_yaml_config, load_env_config, merge_config


class TestConfigLoader:
	"""配置加载器测试"""
	
	def test_load_yaml_config(self):
		"""测试YAML配置加载"""
		# 创建临时YAML文件
		temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
		try:
			yaml.dump({
				"driver": "~fastapi",
				"log": {"level": "INFO"}
			}, temp_file)
			temp_file.close()
			
			config = load_yaml_config(temp_file.name)
			assert config["driver"] == "~fastapi"
			assert config["log"]["level"] == "INFO"
		finally:
			os.unlink(temp_file.name)
	
	def test_load_yaml_config_not_found(self):
		"""测试YAML文件不存在"""
		config = load_yaml_config("/nonexistent/file.yaml")
		assert config == {}
	
	def test_load_env_config(self, monkeypatch):
		"""测试环境变量配置加载"""
		monkeypatch.setenv("NONEBOT_DRIVER", "~fastapi")
		monkeypatch.setenv("NONEBOT_LOG_LEVEL", "DEBUG")
		monkeypatch.setenv("DATABASE_TYPE", "sqlite")
		
		config = load_env_config()
		assert config.get("driver") == "~fastapi"
		assert config.get("log", {}).get("level") == "DEBUG"
		assert config.get("database", {}).get("type") == "sqlite"
	
	def test_merge_config(self):
		"""测试配置合并"""
		yaml_config = {
			"driver": "~fastapi",
			"log": {"level": "INFO"}
		}
		env_config = {
			"log": {"level": "DEBUG"}
		}
		
		merged = merge_config(yaml_config, env_config)
		assert merged["driver"] == "~fastapi"
		assert merged["log"]["level"] == "DEBUG"  # 环境变量优先


class TestBotConfig:
	"""机器人配置测试"""
	
	def test_config_default_values(self):
		"""测试默认配置值"""
		config = BotConfig()
		assert config.driver == "~fastapi"
		assert config.log.level == "INFO"
		assert config.database.type == "sqlite"
	
	def test_config_validation(self):
		"""测试配置验证"""
		# 测试无效的日志级别
		with pytest.raises(ValueError):
			BotConfig(log={"level": "INVALID"})
		
		# 测试无效的数据库类型
		with pytest.raises(ValueError):
			BotConfig(database={"type": "invalid"})
		
		# 测试无效的驱动格式
		with pytest.raises(ValueError):
			BotConfig(driver="fastapi")  # 缺少~前缀
	
	def test_database_config_properties(self):
		"""测试数据库配置属性"""
		config = BotConfig()
		assert config.database.sqlite_path == "./data/bot.db"
		assert config.database.mysql_host == "localhost"
		assert config.database.mysql_port == 3306
	
	def test_config_load(self, monkeypatch, tmp_path):
		"""测试配置加载"""
		# 重置全局配置
		from config import reset_config
		reset_config()
		
		# 创建临时配置文件
		config_file = tmp_path / "config.yaml"
		import yaml
		config_data = {
			"driver": "~fastapi",
			"log": {"level": "DEBUG"},
			"database": {"type": "sqlite"}
		}
		with open(config_file, "w", encoding="utf-8") as f:
			yaml.dump(config_data, f)
		
		# 设置环境变量（应该优先于配置文件）
		monkeypatch.setenv("NONEBOT_LOG_LEVEL", "INFO")
		
		# 加载配置（强制重新加载）
		config = load_config(str(config_file), force_reload=True)
		assert config.driver == "~fastapi"
		assert config.log.level == "INFO"  # 环境变量优先
		assert config.database.type == "sqlite"
	
	def test_get_config_singleton(self):
		"""测试配置单例"""
		# 重置全局配置以测试单例
		from config import reset_config
		reset_config()
		
		config1 = get_config()
		config2 = get_config()
		assert config1 is config2

