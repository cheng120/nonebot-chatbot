"""
消息日志记录服务
记录所有接收到的机器人消息，支持文件日志和数据库存储
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from nonebot.adapters.onebot.v11 import MessageEvent, PrivateMessageEvent, GroupMessageEvent, Message
from src.utils.logger import get_logger
from src.database.connection import DatabaseManager
from src.database.plugin_config import MessageLog

logger = get_logger("message_logger")


class MessageLogger:
	"""消息日志记录器"""
	
	def __init__(self, db_manager: Optional[DatabaseManager] = None, log_to_file: bool = True, log_file_path: str = "./logs/messages.log"):
		"""
		初始化消息日志记录器
		
		Args:
			db_manager: 数据库管理器（可选，用于数据库存储）
			log_to_file: 是否记录到文件
			log_file_path: 日志文件路径
		"""
		self.db_manager = db_manager
		self.log_to_file = log_to_file
		self.log_file_path = Path(log_file_path)
		
		# 确保日志目录存在
		if self.log_to_file:
			self.log_file_path.parent.mkdir(parents=True, exist_ok=True)
	
	def format_message_content(self, message: Message) -> str:
		"""
		格式化消息内容为字符串
		
		Args:
			message: 消息对象
			
		Returns:
			格式化后的消息内容字符串
		"""
		parts = []
		for segment in message:
			if segment.type == "text":
				parts.append(segment.data.get("text", ""))
			elif segment.type == "image":
				file = segment.data.get("file", "")
				url = segment.data.get("url", "")
				if url:
					parts.append(f"[图片: {url}]")
				elif file:
					parts.append(f"[图片: {file}]")
				else:
					parts.append("[图片]")
			elif segment.type == "face":
				face_id = segment.data.get("id", "")
				parts.append(f"[表情: {face_id}]")
			elif segment.type == "at":
				qq = segment.data.get("qq", "")
				parts.append(f"@{qq}" if qq else "@")
			elif segment.type == "reply":
				reply_id = segment.data.get("id", "")
				parts.append(f"[回复: {reply_id}]")
			elif segment.type == "file":
				name = segment.data.get("name", "")
				parts.append(f"[文件: {name}]")
			elif segment.type == "video":
				parts.append("[视频]")
			elif segment.type == "audio":
				parts.append("[语音]")
			elif segment.type == "record":
				parts.append("[语音消息]")
			else:
				parts.append(f"[{segment.type}]")
		
		return "".join(parts)
	
	def extract_message_info(self, event: MessageEvent) -> Dict[str, Any]:
		"""
		提取消息信息
		
		Args:
			event: 消息事件
			
		Returns:
			消息信息字典
		"""
		message_type = "private" if isinstance(event, PrivateMessageEvent) else "group"
		
		info = {
			"message_id": event.message_id,
			"message_type": message_type,
			"user_id": event.user_id,
			"time": datetime.fromtimestamp(event.time).isoformat() if hasattr(event, 'time') else datetime.now().isoformat(),
			"message_content": self.format_message_content(event.message),
			"raw_message": str(event.message),
		}
		
		# 群消息额外信息
		if isinstance(event, GroupMessageEvent):
			info["group_id"] = event.group_id
			info["group_name"] = getattr(event, 'group_name', None)
			info["sender"] = {
				"user_id": event.user_id,
				"nickname": getattr(event.sender, 'nickname', None) if hasattr(event, 'sender') else None,
				"card": getattr(event.sender, 'card', None) if hasattr(event, 'sender') else None,
			}
		else:
			# 私聊消息额外信息
			info["sender"] = {
				"user_id": event.user_id,
				"nickname": getattr(event.sender, 'nickname', None) if hasattr(event, 'sender') else None,
			}
		
		return info
	
	async def log_message(self, event: MessageEvent) -> None:
		"""
		记录消息日志
		
		Args:
			event: 消息事件
		"""
		try:
			# 提取消息信息
			message_info = self.extract_message_info(event)
			
			# 记录到文件
			if self.log_to_file:
				self._log_to_file(message_info)
			
			# 记录到数据库
			if self.db_manager:
				await self._log_to_database(event, message_info)
			
			# 记录到控制台（详细日志）
			logger.debug(f"消息日志已记录: {message_info['message_type']} | 用户{message_info['user_id']} | {message_info['message_content'][:50]}")
			
		except Exception as e:
			logger.error(f"记录消息日志失败: {e}", exc_info=True)
	
	def _log_to_file(self, message_info: Dict[str, Any]) -> None:
		"""
		记录消息到文件
		
		Args:
			message_info: 消息信息字典
		"""
		try:
			# 格式化日志行
			timestamp = message_info.get("time", datetime.now().isoformat())
			msg_type = message_info.get("message_type", "unknown")
			user_id = message_info.get("user_id", "unknown")
			content = message_info.get("message_content", "")
			
			# 群消息格式
			if msg_type == "group":
				group_id = message_info.get("group_id", "unknown")
				log_line = f"[{timestamp}] GROUP | 群{group_id} | 用户{user_id} | {content}\n"
			else:
				# 私聊消息格式
				log_line = f"[{timestamp}] PRIVATE | 用户{user_id} | {content}\n"
			
			# 追加到文件
			with open(self.log_file_path, "a", encoding="utf-8") as f:
				f.write(log_line)
				
		except Exception as e:
			logger.error(f"写入消息日志文件失败: {e}")
	
	async def _log_to_database(self, event: MessageEvent, message_info: Dict[str, Any]) -> None:
		"""
		记录消息到数据库
		
		Args:
			event: 消息事件
			message_info: 消息信息字典
		"""
		try:
			if not self.db_manager:
				return
			
			async with self.db_manager.get_session() as session:
				# 准备消息内容（JSON格式）
				message_content = json.dumps({
					"content": message_info.get("message_content", ""),
					"raw": message_info.get("raw_message", ""),
					"sender": message_info.get("sender", {}),
				}, ensure_ascii=False)
				
				# 创建消息日志
				await MessageLog.create_log(
					session=session,
					message_id=message_info.get("message_id"),
					message_type=message_info.get("message_type", "unknown"),
					user_id=message_info.get("user_id"),
					group_id=message_info.get("group_id") if isinstance(event, GroupMessageEvent) else None,
					message_content=message_content
				)
				
		except Exception as e:
			logger.error(f"写入消息日志到数据库失败: {e}")


# 全局消息日志记录器实例
_message_logger: Optional[MessageLogger] = None


def init_message_logger(db_manager: Optional[DatabaseManager] = None, log_to_file: bool = True, log_file_path: str = "./logs/messages.log") -> MessageLogger:
	"""
	初始化消息日志记录器
	
	Args:
		db_manager: 数据库管理器（可选）
		log_to_file: 是否记录到文件
		log_file_path: 日志文件路径
		
	Returns:
		消息日志记录器实例
	"""
	global _message_logger
	_message_logger = MessageLogger(db_manager, log_to_file, log_file_path)
	logger.info(f"消息日志记录器已初始化 (文件: {log_to_file}, 数据库: {db_manager is not None})")
	return _message_logger


def get_message_logger() -> Optional[MessageLogger]:
	"""
	获取消息日志记录器实例
	
	Returns:
		消息日志记录器实例，如果未初始化返回None
	"""
	return _message_logger

