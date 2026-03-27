"""
重试工具模块
支持自动重试机制，可配置重试次数和间隔
"""
import asyncio
from functools import wraps
from typing import Callable, Type, Tuple, Any
from src.utils.logger import get_logger

logger = get_logger("retry")


def retry(
	max_attempts: int = 3,
	interval: float = 1.0,
	exceptions: Tuple[Type[Exception], ...] = (Exception,),
	backoff: bool = False
):
	"""
	重试装饰器
	
	Args:
		max_attempts: 最大重试次数
		interval: 重试间隔（秒）
		exceptions: 需要重试的异常类型
		backoff: 是否使用指数退避策略
		
	Returns:
		装饰器函数
	"""
	def decorator(func: Callable) -> Callable:
		@wraps(func)
		async def async_wrapper(*args, **kwargs) -> Any:
			last_exception = None
			
			for attempt in range(1, max_attempts + 1):
				try:
					return await func(*args, **kwargs)
				except exceptions as e:
					last_exception = e
					
					if attempt == max_attempts:
						logger.error(f"函数 {func.__name__} 重试{max_attempts}次后仍失败: {e}")
						raise
					
					# 计算等待时间
					if backoff:
						wait_time = interval * (2 ** (attempt - 1))
					else:
						wait_time = interval
					
					logger.warning(
						f"函数 {func.__name__} 第{attempt}次尝试失败，{wait_time:.2f}秒后重试: {e}"
					)
					await asyncio.sleep(wait_time)
			
			# 理论上不会执行到这里
			if last_exception:
				raise last_exception
		
		@wraps(func)
		def sync_wrapper(*args, **kwargs) -> Any:
			last_exception = None
			
			for attempt in range(1, max_attempts + 1):
				try:
					return func(*args, **kwargs)
				except exceptions as e:
					last_exception = e
					
					if attempt == max_attempts:
						logger.error(f"函数 {func.__name__} 重试{max_attempts}次后仍失败: {e}")
						raise
					
					# 计算等待时间
					if backoff:
						wait_time = interval * (2 ** (attempt - 1))
					else:
						wait_time = interval
					
					logger.warning(
						f"函数 {func.__name__} 第{attempt}次尝试失败，{wait_time:.2f}秒后重试: {e}"
					)
					import time
					time.sleep(wait_time)
			
			# 理论上不会执行到这里
			if last_exception:
				raise last_exception
		
		# 判断是异步函数还是同步函数
		if asyncio.iscoroutinefunction(func):
			return async_wrapper
		else:
			return sync_wrapper
	
	return decorator

