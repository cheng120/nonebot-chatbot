"""
消息处理服务
处理接收到的私聊和群聊消息，支持完整的OneBot消息类型
"""
from nonebot import on_message
from nonebot.adapters.onebot.v11 import (
	MessageEvent,
	PrivateMessageEvent,
	GroupMessageEvent,
	Message
)
from src.utils.logger import get_logger
from src.services.message_logger import get_message_logger
from src.services.websocket_event_logger import get_websocket_event_logger
from typing import Optional, Dict, Any

logger = get_logger("message_handler")

# 消息处理器：低优先级，让命令类插件（如 bilichat）先匹配
# 数字越小越先执行；设为 100 避免抢在 /bilichat、.check 等命令前触发
message_matcher = on_message(priority=100, block=False)
logger.info("消息处理器已注册 (on_message, priority=100, block=False)")


def extract_message_content(message: Message) -> Dict[str, Any]:
	"""
	提取消息内容
	
	Args:
		message: OneBot消息对象
		
	Returns:
		消息内容字典
	"""
	content = {
		"text": "",
		"images": [],
		"files": [],
		"at": [],
		"reply": None
	}
	
	for segment in message:
		if segment.type == "text":
			content["text"] += segment.data.get("text", "")
		elif segment.type == "image":
			content["images"].append({
				"file": segment.data.get("file", ""),
				"url": segment.data.get("url", "")
			})
		elif segment.type == "file":
			content["files"].append({
				"name": segment.data.get("name", ""),
				"file": segment.data.get("file", "")
			})
		elif segment.type == "at":
			qq = segment.data.get("qq", "")
			content["at"].append(str(qq) if qq else "")
		elif segment.type == "reply":
			reply_id = segment.data.get("id", "")
			content["reply"] = str(reply_id) if reply_id else ""
	
	return content


async def handle_private_message(event: PrivateMessageEvent):
	"""
	处理私聊消息
	
	Args:
		event: 私聊消息事件
	"""
	# 记录消息日志
	message_logger = get_message_logger()
	if message_logger:
		await message_logger.log_message(event)
	
	# 提取消息内容
	content = extract_message_content(event.message)
	
	# 记录到控制台
	logger.info(f"收到私聊消息: 用户{event.user_id} | {content.get('text', '')[:50]}")
	logger.debug(f"消息详情: {content}")
	
	# 这里可以添加额外的处理逻辑
	# 例如：消息过滤、关键词检测等


async def handle_group_message(event: GroupMessageEvent):
	"""
	处理群聊消息
	
	Args:
		event: 群聊消息事件
	"""
	# 记录消息日志
	message_logger = get_message_logger()
	if message_logger:
		await message_logger.log_message(event)
	
	# 提取消息内容
	content = extract_message_content(event.message)
	
	# 记录到控制台
	logger.info(f"收到群聊消息: 群{event.group_id} | 用户{event.user_id} | {content.get('text', '')[:50]}")
	logger.debug(f"消息详情: {content}")
	
	# 这里可以添加额外的处理逻辑
	# 例如：消息过滤、@机器人检测、关键词检测等


@message_matcher.handle()
async def handle_message(event: MessageEvent):
	"""
	处理消息事件
	
	Args:
		event: 消息事件
	"""
	try:
		# 立即记录，确保能看到消息被接收
		logger.info(f"[消息处理器] 收到消息事件: {event.__class__.__name__} | 用户{event.user_id}")
		
		# 记录 WebSocket 事件日志（直接在这里记录，确保能捕获到）
		websocket_logger = get_websocket_event_logger()
		if websocket_logger:
			try:
				# 尝试获取原始事件数据（优先 Pydantic v2 model_dump）
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
				
				# 记录到 WebSocket 事件日志
				websocket_logger.log_event(event, raw_data)
				logger.debug(f"已记录WebSocket事件: {event.__class__.__name__}")
			except Exception as e:
				logger.error(f"记录WebSocket事件失败: {e}", exc_info=True)
		else:
			logger.warning("WebSocket事件日志记录器未初始化")
		
		# 判断消息类型并处理
		if isinstance(event, PrivateMessageEvent):
			await handle_private_message(event)
		elif isinstance(event, GroupMessageEvent):
			await handle_group_message(event)
		else:
			logger.warning(f"未知的消息类型: {type(event)}")
	except Exception as e:
		logger.error(f"处理消息失败: {e}", exc_info=True)

