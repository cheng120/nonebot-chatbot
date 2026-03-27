"""
WebSocket 事件日志记录服务
记录所有通过 WebSocket 接收的原始事件数据
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
	from nonebot.adapters.onebot.v11 import Event

from src.utils.logger import get_logger
from config import get_config

logger = get_logger("websocket_event_logger")


class WebSocketEventLogger:
	"""WebSocket 事件日志记录器"""
	
	def __init__(self, log_to_file: bool = True, log_file_path: str = "./logs/websocket_events.log"):
		"""
		初始化 WebSocket 事件日志记录器
		
		Args:
			log_to_file: 是否记录到文件
			log_file_path: 日志文件路径
		"""
		self.log_to_file = log_to_file
		self.log_file_path = Path(log_file_path)
		
		# 确保日志目录存在
		if self.log_to_file:
			self.log_file_path.parent.mkdir(parents=True, exist_ok=True)
	
	def log_event(self, event: "Event", raw_data: Optional[Dict[str, Any]] = None) -> None:
		"""
		记录 WebSocket 事件
		
		Args:
			event: 事件对象
			raw_data: 原始事件数据（可选）
		"""
		try:
			# 提取事件信息
			event_info = self._extract_event_info(event, raw_data)
			
			# 记录到文件
			if self.log_to_file:
				self._log_to_file(event_info)
			
			# 记录到控制台（INFO级别，确保能看到）
			post_type = event_info.get('post_type', 'unknown')
			event_type = event_info.get('event_type', 'unknown')
			user_id = event_info.get('user_id', '')
			group_id = event_info.get('group_id', '')
			message_id = event_info.get('message_id', '')
			
			# 对于心跳事件，使用 DEBUG 级别（避免日志过多）
			# 对于消息事件，使用 INFO 级别
			if post_type == 'meta_event' and event_type == 'meta_heartbeat':
				logger.debug(f"WebSocket心跳事件: {post_type} | {event_type}")
			else:
				log_msg = f"WebSocket事件已记录: {post_type} | {event_type}"
				if user_id:
					log_msg += f" | 用户{user_id}"
				if group_id:
					log_msg += f" | 群{group_id}"
				if message_id:
					log_msg += f" | 消息ID={message_id}"
				logger.info(log_msg)
			
		except Exception as e:
			logger.error(f"记录WebSocket事件日志失败: {e}", exc_info=True)
	
	def _extract_event_info(self, event: "Event", raw_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
		"""
		提取事件信息
		
		Args:
			event: 事件对象
			raw_data: 原始事件数据
		
		Returns:
			事件信息字典
		"""
		# 获取事件类型
		post_type = getattr(event, 'post_type', 'unknown')
		event_type = None
		
		# 根据事件类型提取特定信息
		if hasattr(event, 'message_type'):
			event_type = f"message_{event.message_type}"
		elif hasattr(event, 'notice_type'):
			event_type = f"notice_{event.notice_type}"
		elif hasattr(event, 'request_type'):
			event_type = f"request_{event.request_type}"
		elif hasattr(event, 'meta_event_type'):
			event_type = f"meta_{event.meta_event_type}"
		
		info = {
			"timestamp": datetime.now().isoformat(),
			"post_type": post_type,
			"event_type": event_type,
			"event_class": event.__class__.__name__,
		}
		
		# 提取事件特定字段
		if hasattr(event, 'time'):
			info["event_time"] = datetime.fromtimestamp(event.time).isoformat() if event.time else None
		
		if hasattr(event, 'self_id'):
			info["self_id"] = event.self_id
		
		# 消息事件
		if hasattr(event, 'message_id'):
			info["message_id"] = event.message_id
		if hasattr(event, 'user_id'):
			info["user_id"] = event.user_id
		if hasattr(event, 'group_id'):
			info["group_id"] = event.group_id
		if hasattr(event, 'message'):
			info["message"] = str(event.message)
		
		# 通知事件
		if hasattr(event, 'operator_id'):
			info["operator_id"] = event.operator_id
		
		# 请求事件
		if hasattr(event, 'comment'):
			info["comment"] = event.comment
		if hasattr(event, 'flag'):
			info["flag"] = event.flag
		
		# 添加原始数据（如果提供）
		if raw_data:
			info["raw_data"] = raw_data
		else:
			# 尝试从事件对象获取原始数据
			if hasattr(event, 'dict'):
				try:
					info["raw_data"] = event.dict()
				except Exception:
					pass
		
		return info
	
	def _log_to_file(self, event_info: Dict[str, Any]) -> None:
		"""
		记录事件到文件
		
		Args:
			event_info: 事件信息字典
		"""
		try:
			# 确保日志目录存在
			self.log_file_path.parent.mkdir(parents=True, exist_ok=True)
			
			# 格式化日志行
			timestamp = event_info.get("timestamp", datetime.now().isoformat())
			post_type = event_info.get("post_type", "unknown")
			event_type = event_info.get("event_type", "unknown")
			
			# 构建基本信息
			base_info = f"[{timestamp}] {post_type.upper()} | {event_type}"
			
			# 添加特定信息
			details = []
			if event_info.get("user_id"):
				details.append(f"用户{event_info['user_id']}")
			if event_info.get("group_id"):
				details.append(f"群{event_info['group_id']}")
			if event_info.get("message_id"):
				details.append(f"消息ID={event_info['message_id']}")
			
			if details:
				base_info += f" | {' | '.join(details)}"
			
			# 添加消息内容（如果有）
			if event_info.get("message"):
				message = event_info["message"]
				if len(message) > 100:
					message = message[:100] + "..."
				base_info += f" | {message}"
			
			# 添加原始数据（JSON格式，完整记录）
			if event_info.get("raw_data"):
				try:
					raw_json = json.dumps(event_info["raw_data"], ensure_ascii=False, indent=2)
					base_info += f"\n原始数据:\n{raw_json}"
				except Exception as e:
					logger.debug(f"序列化原始数据失败: {e}")
			
			log_line = base_info + "\n" + "-" * 80 + "\n"
			
			# 追加到文件
			try:
				with open(self.log_file_path, "a", encoding="utf-8") as f:
					f.write(log_line)
				logger.debug(f"已写入WebSocket事件日志: {self.log_file_path}")
			except Exception as e:
				logger.error(f"写入文件失败: {e}，文件路径: {self.log_file_path}")
				raise
			
			# 同时输出到控制台（INFO级别）
			logger.info(f"WebSocket事件: {post_type.upper()} | {event_type} | {' | '.join(details) if details else ''}")
				
		except Exception as e:
			logger.error(f"写入WebSocket事件日志文件失败: {e}", exc_info=True)


# 全局 WebSocket 事件日志记录器实例
_websocket_event_logger: Optional[WebSocketEventLogger] = None


def init_websocket_event_logger(log_to_file: bool = True, log_file_path: str = "./logs/websocket_events.log") -> WebSocketEventLogger:
	"""
	初始化 WebSocket 事件日志记录器
	
	Args:
		log_to_file: 是否记录到文件
		log_file_path: 日志文件路径
		
	Returns:
		WebSocket 事件日志记录器实例
	"""
	global _websocket_event_logger
	_websocket_event_logger = WebSocketEventLogger(log_to_file, log_file_path)
	logger.info(f"WebSocket事件日志记录器已初始化 (文件: {log_to_file})")
	return _websocket_event_logger


def get_websocket_event_logger() -> Optional[WebSocketEventLogger]:
	"""
	获取 WebSocket 事件日志记录器实例
	
	Returns:
		WebSocket 事件日志记录器实例，如果未初始化返回None
	"""
	return _websocket_event_logger


def setup_websocket_event_logging():
	"""
	设置 WebSocket 事件日志记录
	通过 NoneBot 的事件总线监听所有事件
	"""
	try:
		from nonebot import get_driver, on
		from nonebot.adapters.onebot.v11 import Event as OneBotEvent
		
		driver = get_driver()
		config = get_config()
		
		# 检查是否启用消息日志
		if not config.message_log.enabled:
			logger.debug("消息日志未启用，跳过 WebSocket 事件日志设置")
			return
		
		# 初始化日志记录器
		init_websocket_event_logger(
			log_to_file=config.message_log.log_to_file,
			log_file_path=config.message_log.file_path.replace("messages.log", "websocket_events.log")
		)
		
		@driver.on_bot_connect
		async def on_bot_connect(bot):
			"""Bot 连接时"""
			logger.info(f"[WebSocket事件日志] Bot {bot.self_id} 已连接，开始记录 WebSocket 事件")
		
		@driver.on_bot_disconnect
		async def on_bot_disconnect(bot):
			"""Bot 断开连接时"""
			logger.info(f"Bot {bot.self_id} 已断开连接")
		
		# 监听所有 OneBot 事件
		# 使用多种方式确保事件能被捕获
		from nonebot.adapters.onebot.v11 import Event, MessageEvent
		
		# 方法1: 使用 on() 函数监听所有事件
		try:
			# 尝试使用 on(Event) 直接传入事件类型
			event_matcher = on(Event, priority=999, block=False)
			logger.info("使用 on(Event) 创建事件监听器成功")
		except Exception as e1:
			logger.warning(f"使用 on(Event) 失败: {e1}，尝试使用 on(type=Event)")
			try:
				event_matcher = on(type=Event, priority=999, block=False)
				logger.info("使用 on(type=Event) 创建事件监听器成功")
			except Exception as e2:
				logger.error(f"创建事件监听器失败: {e2}", exc_info=True)
				# 如果都失败，尝试使用消息事件监听器
				event_matcher = on_message(priority=999, block=False)
				logger.warning("回退到使用 on_message() 监听消息事件")
		
		@event_matcher.handle()
		async def log_websocket_event(event: Event):
			"""
			记录所有通过 WebSocket 接收的事件
			
			Args:
				event: OneBot 事件对象
			"""
			try:
				# 立即记录，确保能看到
				logger.info(f"[WebSocket事件监听器] 事件类型: {event.__class__.__name__}")
				
				websocket_logger = get_websocket_event_logger()
				if websocket_logger:
					# 尝试获取原始事件数据
					raw_data = None
					if hasattr(event, 'dict'):
						try:
							raw_data = event.dict()
						except Exception as e:
							logger.debug(f"使用 dict() 获取原始数据失败: {e}")
					elif hasattr(event, 'model_dump'):
						try:
							raw_data = event.model_dump()
						except Exception as e:
							logger.debug(f"使用 model_dump() 获取原始数据失败: {e}")
					
					# 记录事件
					websocket_logger.log_event(event, raw_data)
					
					# 调试日志：确认事件被接收（INFO级别，确保能看到）
					post_type = getattr(event, 'post_type', 'unknown')
					event_class = event.__class__.__name__
					
					# 提取更多信息用于日志
					event_info = []
					if hasattr(event, 'user_id'):
						event_info.append(f"用户{event.user_id}")
					if hasattr(event, 'group_id'):
						event_info.append(f"群{event.group_id}")
					if hasattr(event, 'message_id'):
						event_info.append(f"消息ID={event.message_id}")
					
					info_str = " | ".join(event_info) if event_info else ""
					logger.info(f"[WebSocket事件] {post_type} | {event_class} | {info_str}")
				else:
					logger.warning("WebSocket事件日志记录器未初始化")
			except Exception as e:
				logger.error(f"记录WebSocket事件失败: {e}", exc_info=True)
		
		# 方法2: 同时使用消息事件监听器作为备用（确保消息事件能被捕获）
		from nonebot import on_message
		message_matcher = on_message(priority=998, block=False)
		
		@message_matcher.handle()
		async def log_message_event(event: MessageEvent):
			"""备用消息事件监听器"""
			try:
				logger.info(f"[备用消息监听器] 收到消息: {event.__class__.__name__} | 用户{event.user_id} | 群{event.group_id if hasattr(event, 'group_id') else 'N/A'}")
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
				logger.error(f"备用消息监听器失败: {e}", exc_info=True)
		
		logger.info("WebSocket 事件日志记录已设置")
	except Exception as e:
		logger.error(f"设置 WebSocket 事件日志记录失败: {e}", exc_info=True)

