"""
OneBot V11适配器配置模块
"""
import os
from nonebot import get_driver, on
from nonebot.adapters.onebot.v11 import Adapter as OneBotV11Adapter, Event, MessageEvent
from loguru import logger
from typing import Optional


def setup_onebot_adapter(config) -> Optional[OneBotV11Adapter]:
	"""
	设置OneBot V11适配器

	Args:
		config: 配置对象（BotConfig）

	Returns:
		OneBot V11适配器实例
	"""
	try:
		# 获取OneBot适配器配置（取第一个适配器配置）
		if not config.adapters:
			logger.warning("未配置OneBot适配器")
			return None

		adapter_config = config.adapters[0]

		# 设置环境变量（必须在注册适配器之前设置）
		# OneBot V11 适配器使用环境变量配置连接

		# 正向 WebSocket 配置（Bot 连接到 NapCat）
		# NoneBot 适配器优先级：如果设置了 ONEBOT_WS_URL，优先使用 WebSocket
		# 如果同时设置了 ONEBOT_API_ROOT，适配器会同时支持两种方式，但 WebSocket 用于接收事件
		
		# 首先，确保移除可能存在的 ONEBOT_API_ROOT（如果配置了 WebSocket）
		if "ONEBOT_API_ROOT" in os.environ:
			old_api_root = os.environ["ONEBOT_API_ROOT"]
			del os.environ["ONEBOT_API_ROOT"]
			logger.info(f"已移除环境变量 ONEBOT_API_ROOT={old_api_root}")
		
		if adapter_config.websocket and adapter_config.websocket.url:
			# 适配器的 Config 类使用 alias="onebot_v11_ws_urls"
			# 环境变量应该是 JSON 数组格式（因为 onebot_ws_urls 是 set[WSUrl] 类型）
			# NoneBot 的配置系统会尝试将环境变量解析为 JSON
			ws_url = adapter_config.websocket.url
			
			# 设置环境变量为 JSON 数组格式（适配器会解析为集合）
			import json
			ws_urls_json = json.dumps([ws_url])  # 转换为 JSON 数组
			os.environ["ONEBOT_V11_WS_URLS"] = ws_urls_json
			logger.info(f"设置环境变量 ONEBOT_V11_WS_URLS={ws_urls_json} (JSON格式)")
			
			# 也设置简写形式（某些版本可能支持，但可能不会自动转换）
			# 注意：不要设置 ONEBOT_WS_URL，因为适配器可能不支持这个简写形式
			# os.environ["ONEBOT_WS_URL"] = ws_url
			
			# WebSocket Access Token 配置
			if adapter_config.websocket.access_token:
				os.environ["ONEBOT_WS_ACCESS_TOKEN"] = adapter_config.websocket.access_token
				os.environ["ONEBOT_V11_ACCESS_TOKEN"] = adapter_config.websocket.access_token
				logger.info("已设置 ONEBOT_WS_ACCESS_TOKEN 和 ONEBOT_V11_ACCESS_TOKEN")
			
			# 重要：如果配置了 WebSocket，不要设置 ONEBOT_API_ROOT
			# 因为同时设置会导致适配器同时尝试两种连接，可能优先使用 HTTP API
			# 如果需要 HTTP API 主动调用，可以通过 Bot 实例的 API 方法调用
			# 再次确认 ONEBOT_API_ROOT 已被移除
			if "ONEBOT_API_ROOT" in os.environ:
				del os.environ["ONEBOT_API_ROOT"]
				logger.warning("检测到 ONEBOT_API_ROOT 仍然存在，已再次移除")
			if "ONEBOT_V11_API_ROOTS" in os.environ:
				del os.environ["ONEBOT_V11_API_ROOTS"]
				logger.warning("检测到 ONEBOT_V11_API_ROOTS 仍然存在，已移除")
			
			# 验证环境变量设置
			logger.info(f"环境变量验证: ONEBOT_WS_URL={os.environ.get('ONEBOT_WS_URL', 'NOT SET')}")
			logger.info(f"环境变量验证: ONEBOT_V11_WS_URLS={os.environ.get('ONEBOT_V11_WS_URLS', 'NOT SET')}")
			logger.info(f"环境变量验证: ONEBOT_API_ROOT={os.environ.get('ONEBOT_API_ROOT', 'NOT SET (正确)')}")
		else:
			# 如果没有配置 WebSocket，使用 HTTP API 作为连接方式
			if adapter_config.api_root:
				os.environ["ONEBOT_API_ROOT"] = adapter_config.api_root
				logger.info(f"设置环境变量 ONEBOT_API_ROOT={adapter_config.api_root}（使用 HTTP API 连接）")

		# HTTP API Access Token 配置（用于 HTTP API 调用，即使使用 WebSocket 连接也可能需要）
		if adapter_config.access_token:
			os.environ["ONEBOT_ACCESS_TOKEN"] = adapter_config.access_token
			logger.info("已设置 ONEBOT_ACCESS_TOKEN")

		# 获取驱动并注册适配器
		driver = get_driver()
		
		# 检查驱动是否支持 WebSocket 客户端连接
		from nonebot.drivers import WebSocketClientMixin
		driver_type = type(driver).__name__
		driver_module = type(driver).__module__
		logger.info(f"当前驱动: {driver_type} (模块: {driver_module})")
		
		if isinstance(driver, WebSocketClientMixin):
			logger.info(f"驱动 {driver_type} 支持 WebSocket 客户端连接")
		else:
			logger.error(f"驱动 {driver_type} 不支持 WebSocket 客户端连接！")
			logger.error("这将导致无法使用 WebSocket 连接。")
			logger.error("解决方案：使用组合驱动，例如：driver: ~fastapi+~httpx")
			logger.error(f"当前配置的驱动: {config.driver if hasattr(config, 'driver') else 'unknown'}")

		# 注册 OneBot V11 适配器
		# 适配器会自动读取环境变量并连接到 NapCat
		driver.register_adapter(OneBotV11Adapter)

		logger.info("OneBot V11适配器已注册")
		logger.info(f"  HTTP API: {adapter_config.api_root}")
		logger.info(f"  WebSocket: {adapter_config.websocket.url}")
		if adapter_config.access_token:
			logger.info(f"  Access Token: {'*' * len(adapter_config.access_token)}")
		logger.info("  连接模式: 正向 WebSocket（Bot 连接到 NapCat）")
		
		# 在适配器注册后，再次验证环境变量（适配器可能在注册时读取）
		import asyncio
		async def verify_adapter_config():
			"""验证适配器配置"""
			await asyncio.sleep(1)  # 等待适配器初始化
			try:
				# 尝试获取适配器实例
				adapters = driver._adapters if hasattr(driver, '_adapters') else []
				for adapter in adapters:
					if isinstance(adapter, OneBotV11Adapter):
						# 检查适配器的配置
						if hasattr(adapter, 'onebot_config'):
							config = adapter.onebot_config
							if hasattr(config, 'onebot_ws_urls'):
								ws_urls = config.onebot_ws_urls
								if ws_urls:
									logger.info(f"适配器检测到 WebSocket URLs: {ws_urls}")
								else:
									logger.warning("适配器配置中 onebot_ws_urls 为空！")
							else:
								logger.warning("适配器配置中没有 onebot_ws_urls 属性")
						break
			except Exception as e:
				logger.error(f"验证适配器配置失败: {e}", exc_info=True)
		
		# 在启动时验证配置
		@driver.on_startup
		async def verify_on_startup():
			await verify_adapter_config()
		
		# 通过 monkey patch Bot.handle_event 来记录所有事件（在事件到达事件总线之前）
		try:
			from nonebot.adapters.onebot.v11 import Bot as OneBotBot
			
			# 保存原始的 handle_event 方法
			original_handle_event = OneBotBot.handle_event
			
			async def patched_handle_event(self, event: Event):
				"""包装的 handle_event，在调用原始方法前记录事件"""
				try:
					# 获取事件类型
					post_type = getattr(event, 'post_type', 'unknown')
					event_class = event.__class__.__name__
					
					# 记录所有事件（包括心跳）- 使用 INFO 级别确保能看到
					if post_type == 'meta_event':
						meta_type = getattr(event, 'meta_event_type', 'unknown')
						logger.info(f"[Bot.handle_event] {post_type} | {event_class} | {meta_type} | Bot ID: {self.self_id}")
					else:
						logger.info(f"[Bot.handle_event] {post_type} | {event_class} | Bot ID: {self.self_id}")
					
					# 如果是消息事件，记录详细信息
					if post_type == 'message':
						if hasattr(event, 'user_id'):
							logger.info(f"  用户ID: {event.user_id}")
						if hasattr(event, 'group_id'):
							logger.info(f"  群ID: {event.group_id}")
						if hasattr(event, 'message_id'):
							logger.info(f"  消息ID: {event.message_id}")
					
					# 尝试记录到 WebSocket 事件日志
					try:
						from src.services.websocket_event_logger import get_websocket_event_logger
						websocket_logger = get_websocket_event_logger()
						if websocket_logger:
							raw_data = None
							if hasattr(event, 'model_dump'):
								try:
									raw_data = event.model_dump()
								except Exception:
									pass
							elif hasattr(event, 'dict'):
								try:
									raw_data = event.dict()
								except Exception:
									pass
							websocket_logger.log_event(event, raw_data)
					except Exception as e:
						logger.debug(f"记录WebSocket事件失败: {e}")
				except Exception as e:
					logger.error(f"记录事件失败: {e}", exc_info=True)
				
				# 调用原始的 handle_event 方法
				return await original_handle_event(self, event)
			
			# 替换 handle_event 方法
			OneBotBot.handle_event = patched_handle_event
			logger.info("已通过 monkey patch 拦截 Bot.handle_event，将记录所有事件")
			
			# 验证 monkey patch 是否成功
			if hasattr(OneBotBot, 'handle_event') and OneBotBot.handle_event == patched_handle_event:
				logger.info("Monkey patch 验证成功：Bot.handle_event 已被替换")
			else:
				logger.warning("Monkey patch 验证失败：Bot.handle_event 可能未被正确替换")
		except Exception as e:
			logger.warning(f"Monkey patch Bot.handle_event 失败: {e}", exc_info=True)
		
		# 在适配器层面直接监听所有事件（确保能捕获到）
		try:
			# 监听 Bot 连接事件
			@driver.on_bot_connect
			async def on_adapter_bot_connect(bot):
				"""Bot 连接时的回调"""
				logger.info(f"[适配器] Bot {bot.self_id} 已连接（on_bot_connect 回调触发）")
				# 验证 Bot 实例
				logger.info(f"[适配器] Bot 实例类型: {type(bot)}")
				logger.info(f"[适配器] Bot.handle_event 方法: {bot.handle_event}")
			
			# 也监听 Bot 断开连接事件
			@driver.on_bot_disconnect
			async def on_adapter_bot_disconnect(bot):
				"""Bot 断开连接时的回调"""
				logger.info(f"[适配器] Bot {bot.self_id} 已断开连接")
			
			# 定期检查 Bot 连接状态（用于调试）
			import asyncio
			async def check_bot_status():
				"""定期检查 Bot 连接状态"""
				await asyncio.sleep(5)  # 等待5秒后检查
				try:
					from nonebot import get_bots
					bots = get_bots()
					if bots:
						for bot_id, bot in bots.items():
							logger.info(f"[调试] 检测到 Bot: {bot_id} (类型: {type(bot)})")
							logger.info(f"[调试] Bot.handle_event 方法: {bot.handle_event}")
					else:
						logger.warning("[调试] 未检测到任何 Bot 实例")
				except Exception as e:
					logger.error(f"[调试] 检查 Bot 状态失败: {e}", exc_info=True)
			
			# 在启动后检查 Bot 状态
			@driver.on_startup
			async def check_bot_on_startup():
				"""启动时检查 Bot 状态"""
				asyncio.create_task(check_bot_status())
			
			# 监听所有 OneBot 事件
			event_matcher = on(Event, priority=1, block=False)
			
			@event_matcher.handle()
			async def log_all_events(event: Event):
				"""在适配器层面记录所有事件"""
				try:
					# 获取事件类型
					post_type = getattr(event, 'post_type', 'unknown')
					event_class = event.__class__.__name__
					
					# 记录所有事件（包括心跳）
					# 对于心跳事件，使用 INFO 级别（确保能看到）
					if post_type == 'meta_event':
						meta_type = getattr(event, 'meta_event_type', 'unknown')
						logger.info(f"[适配器事件监听] {post_type} | {event_class} | {meta_type}")
					else:
						logger.info(f"[适配器事件监听] {post_type} | {event_class}")
					
					# 如果是消息事件，记录详细信息
					if post_type == 'message':
						if hasattr(event, 'user_id'):
							logger.info(f"  用户ID: {event.user_id}")
						if hasattr(event, 'group_id'):
							logger.info(f"  群ID: {event.group_id}")
						if hasattr(event, 'message_id'):
							logger.info(f"  消息ID: {event.message_id}")
					
					# 尝试记录到 WebSocket 事件日志
					try:
						from src.services.websocket_event_logger import get_websocket_event_logger
						websocket_logger = get_websocket_event_logger()
						if websocket_logger:
							raw_data = None
							if hasattr(event, 'model_dump'):
								try:
									raw_data = event.model_dump()
								except Exception:
									pass
							elif hasattr(event, 'dict'):
								try:
									raw_data = event.dict()
								except Exception:
									pass
							websocket_logger.log_event(event, raw_data)
					except Exception as e:
						logger.debug(f"记录WebSocket事件失败: {e}")
				except Exception as e:
					logger.error(f"适配器事件监听失败: {e}", exc_info=True)
			
			logger.info("适配器层面事件监听器已注册")
		except Exception as e:
			logger.warning(f"注册适配器层面事件监听器失败: {e}", exc_info=True)

		return OneBotV11Adapter
	except Exception as e:
		logger.error(f"OneBot V11适配器注册失败: {e}", exc_info=True)
		raise

