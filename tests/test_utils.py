"""
工具模块测试
"""
import pytest
import asyncio
from src.utils.retry import retry
from src.utils.logger import setup_logger, get_logger
from config import LogConfig


class TestRetry:
	"""重试工具测试"""
	
	@pytest.mark.asyncio
	async def test_retry_success(self):
		"""测试重试成功"""
		call_count = 0
		
		@retry(max_attempts=3, interval=0.01)
		async def test_func():
			nonlocal call_count
			call_count += 1
			return "success"
		
		result = await test_func()
		assert result == "success"
		assert call_count == 1
	
	@pytest.mark.asyncio
	async def test_retry_after_failure(self):
		"""测试失败后重试成功"""
		call_count = 0
		
		@retry(max_attempts=3, interval=0.01)
		async def test_func():
			nonlocal call_count
			call_count += 1
			if call_count < 2:
				raise ValueError("Test error")
			return "success"
		
		result = await test_func()
		assert result == "success"
		assert call_count == 2
	
	@pytest.mark.asyncio
	async def test_retry_max_attempts(self):
		"""测试达到最大重试次数"""
		call_count = 0
		
		@retry(max_attempts=3, interval=0.01)
		async def test_func():
			nonlocal call_count
			call_count += 1
			raise ValueError("Test error")
		
		with pytest.raises(ValueError):
			await test_func()
		
		assert call_count == 3
	
	@pytest.mark.asyncio
	async def test_retry_with_backoff(self):
		"""测试指数退避策略"""
		call_times = []
		
		@retry(max_attempts=3, interval=0.1, backoff=True)
		async def test_func():
			import time
			call_times.append(time.time())
			raise ValueError("Test error")
		
		start_time = call_times[0] if call_times else 0
		with pytest.raises(ValueError):
			await test_func()
		
		# 验证重试间隔递增（允许一定误差）
		if len(call_times) >= 2:
			interval1 = call_times[1] - call_times[0]
			interval2 = call_times[2] - call_times[1] if len(call_times) >= 3 else 0
			# 第二个间隔应该大于第一个（指数退避）
			if interval2 > 0:
				assert interval2 > interval1
	
	@pytest.mark.asyncio
	async def test_retry_exception_filter(self):
		"""测试异常类型过滤"""
		call_count = 0
		
		@retry(max_attempts=3, interval=0.01, exceptions=(ValueError,))
		async def test_func():
			nonlocal call_count
			call_count += 1
			raise TypeError("Should not retry")
		
		# TypeError不在重试列表中，应该直接抛出
		with pytest.raises(TypeError):
			await test_func()
		
		assert call_count == 1


class TestLogger:
	"""日志工具测试"""
	
	def test_setup_logger(self):
		"""测试日志系统设置"""
		log_config = LogConfig(
			level="DEBUG",
			console=True,
			file=False
		)
		setup_logger(log_config)
		# 如果没有异常，说明设置成功
		assert True
	
	def test_get_logger(self):
		"""测试获取日志记录器"""
		logger = get_logger("test_module")
		assert logger is not None
	
	def test_logger_output(self, capsys):
		"""测试日志输出"""
		# 重新设置logger（移除之前的配置）
		from loguru import logger as loguru_logger
		loguru_logger.remove()
		
		log_config = LogConfig(
			level="INFO",
			console=True,
			file=False
		)
		setup_logger(log_config)
		logger = get_logger("test")
		logger.info("Test log message")
		
		# 检查输出（loguru的输出格式可能不同）
		# 注意：loguru可能输出到stderr
		captured = capsys.readouterr()
		output = captured.out + captured.err
		# 由于loguru的格式可能包含颜色代码等，只检查消息内容
		assert "Test log message" in output or "test" in output.lower()

