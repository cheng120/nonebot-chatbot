"""
状态管理服务
监控机器人运行状态、连接状态等
"""
import asyncio
import httpx
from typing import Dict, Any, Optional
from datetime import datetime
from nonebot import get_bot, get_driver
from nonebot.adapters.onebot.v11 import Bot
from src.utils.logger import get_logger

logger = get_logger("status_manager")


class StatusManager:
	"""状态管理器"""
	
	def __init__(self, check_interval: int = 30):
		"""
		初始化状态管理器
		
		Args:
			check_interval: 检查间隔（秒）
		"""
		self.check_interval = check_interval
		self.status: Dict[str, Any] = {
			"running": False,
			"connected": False,
			"plugins_loaded": 0,
			"last_check": None,
			"start_time": None,
			"last_error": None,
			"connection_method": None  # WebSocket 或 HTTP API
		}
		self._monitoring = False
	
	async def start_monitoring(self):
		"""开始监控"""
		if self._monitoring:
			logger.warning("状态监控已在运行")
			return
		
		self._monitoring = True
		self.status["running"] = True
		self.status["start_time"] = datetime.now()
		logger.info(f"状态监控已启动，检查间隔: {self.check_interval}秒")
		
		while self._monitoring:
			try:
				await self.check_status()
				await asyncio.sleep(self.check_interval)
			except Exception as e:
				logger.error(f"状态检查失败: {e}", exc_info=True)
				await asyncio.sleep(self.check_interval)
	
	async def stop_monitoring(self):
		"""停止监控"""
		self._monitoring = False
		self.status["running"] = False
		logger.info("状态监控已停止")
	
	async def check_status(self):
		"""
		检查状态
		使用多种方法检查连接：1) WebSocket bot实例 2) HTTP API直接测试
		"""
		try:
			# 检查连接状态
			connected = False
			last_connected = self.status.get("connected", False)
			error_msg = None
			connection_method = None
			
			# 方法1: 尝试通过WebSocket bot实例检查（优先）
			try:
				# 尝试获取bot实例
				try:
					bot = get_bot()
					bot_available = bot is not None
				except ValueError:
					# 如果没有bot，尝试获取所有bots
					try:
						from nonebot import get_bots
						bots = get_bots()
						bot_available = len(bots) > 0
						if bot_available:
							bot = list(bots.values())[0]
						else:
							bot = None
					except Exception:
						bot_available = False
						bot = None
				
				if bot and bot_available:
					# 尝试获取机器人信息来验证连接
					try:
						await asyncio.wait_for(bot.get_login_info(), timeout=5.0)
						connected = True
						error_msg = None
						connection_method = "WebSocket"
					except asyncio.TimeoutError:
						error_msg = "WebSocket API调用超时"
						connection_method = "WebSocket"
					except Exception as api_error:
						error_msg = f"WebSocket API调用失败: {str(api_error)}"
						connection_method = "WebSocket"
						logger.debug(f"WebSocket API调用失败详情: {api_error}", exc_info=True)
			except ValueError as e:
				logger.debug(f"get_bot()抛出ValueError: {e}")
			except Exception as e:
				logger.debug(f"WebSocket检查失败: {e}")
			
			# 方法2: 如果WebSocket检查失败，尝试通过HTTP API检查（备选）
			if not connected:
				try:
					from config import get_config

					config = get_config()
					if config.adapters and config.adapters[0].api_root:
						api_root = config.adapters[0].api_root
						access_token = config.adapters[0].access_token or ""
						
						headers = {}
						if access_token:
							headers["Authorization"] = f"Bearer {access_token}"
						
						# 尝试调用一个简单的API来验证连接
						async with httpx.AsyncClient(timeout=3.0) as client:
							# 尝试调用get_status或get_version_info
							test_urls = [
								f"{api_root}/get_status",
								f"{api_root}/get_version_info",
								f"{api_root}/",
							]
							
							for url in test_urls:
								try:
									resp = await asyncio.wait_for(
										client.get(url, headers=headers),
										timeout=3.0
									)
									if resp.status_code in [200, 400, 401]:  # 400/401也说明服务可达
										connected = True
										error_msg = None
										connection_method = "HTTP API"
										logger.debug(f"HTTP API检查成功: {url} (状态码: {resp.status_code})")
										break
								except (httpx.RequestError, asyncio.TimeoutError):
									continue
								except Exception as e:
									logger.debug(f"HTTP API检查失败 ({url}): {e}")
									continue
					
					if not connected and connection_method != "HTTP API":
						error_msg = "无法获取bot实例且HTTP API检查失败（适配器可能未连接）"
				except Exception as e:
					logger.debug(f"HTTP API备选检查失败: {e}")
					if not error_msg:
						error_msg = f"连接检查异常: {str(e)}"
			
			# 检查插件状态
			plugins_loaded = 0
			try:
				from nonebot import get_loaded_plugins
				plugins = get_loaded_plugins()
				plugins_loaded = len(list(plugins))
			except Exception as e:
				logger.debug(f"插件检查失败: {e}")
			
			# 更新状态
			self.status["connected"] = connected
			self.status["plugins_loaded"] = plugins_loaded
			self.status["last_check"] = datetime.now()
			if connection_method:
				self.status["connection_method"] = connection_method
			if error_msg:
				self.status["last_error"] = error_msg
			else:
				self.status["last_error"] = None  # 清除错误信息
			
			# 记录状态日志（仅在状态变化时）
			if not connected and last_connected:
				# 从连接变为断开
				logger.warning(f"机器人连接断开: {error_msg}")
			elif not connected and not last_connected:
				# 持续未连接（只在第一次或错误信息变化时记录）
				if error_msg != self.status.get("last_error"):
					logger.warning(f"机器人连接状态异常: {error_msg}")
			elif connected and not last_connected:
				# 从断开变为连接
				logger.info("机器人连接已恢复")
			
		except Exception as e:
			logger.error(f"状态检查异常: {e}", exc_info=True)
	
	def get_status(self) -> Dict[str, Any]:
		"""
		获取当前状态
		
		Returns:
			状态字典
		"""
		status = self.status.copy()
		if status.get("start_time"):
			status["start_time"] = status["start_time"].isoformat()
		if status.get("last_check"):
			status["last_check"] = status["last_check"].isoformat()
		return status

