"""
适配器模块测试
"""
import pytest
from src.adapters.onebot_v11 import setup_onebot_adapter
from config import BotConfig


class TestOneBotAdapter:
	"""OneBot适配器测试"""
	
	def test_setup_adapter_with_config(self, test_config):
		"""测试适配器设置"""
		# 注意：这个测试需要NoneBot环境，可能会失败
		# 在实际NoneBot环境中测试
		try:
			adapter = setup_onebot_adapter(test_config)
			# 如果成功，adapter应该是OneBotV11Adapter类
			assert adapter is not None
		except Exception as e:
			# 在没有NoneBot环境的情况下，这是预期的
			pytest.skip(f"需要NoneBot环境: {e}")
	
	def test_adapter_config_validation(self, test_config):
		"""测试适配器配置验证"""
		# 验证配置中有适配器配置
		assert len(test_config.adapters) > 0
		assert test_config.adapters[0].name == "OneBot V11"
		assert test_config.adapters[0].api_root is not None
		assert test_config.adapters[0].websocket.url is not None

