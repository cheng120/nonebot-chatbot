"""
事件处理服务
处理完整的OneBot事件类型（消息、通知、请求、元事件）
"""
from nonebot import on_notice, on_request
from nonebot.adapters.onebot.v11 import (
	NoticeEvent,
	RequestEvent,
	MetaEvent,
	GroupIncreaseNoticeEvent,
	GroupDecreaseNoticeEvent,
	FriendAddNoticeEvent,
	GroupRecallNoticeEvent,
	FriendRecallNoticeEvent,
	FriendRequestEvent,
	GroupRequestEvent
)
from src.utils.logger import get_logger

logger = get_logger("event_handler")

# 通知事件处理器
notice_matcher = on_notice()

# 请求事件处理器
request_matcher = on_request()


async def handle_group_increase(event: GroupIncreaseNoticeEvent):
	"""处理群成员增加事件"""
	logger.info(f"群{event.group_id}新增成员: {event.user_id}")


async def handle_group_decrease(event: GroupDecreaseNoticeEvent):
	"""处理群成员减少事件"""
	logger.info(f"群{event.group_id}减少成员: {event.user_id}")


async def handle_friend_add(event: FriendAddNoticeEvent):
	"""处理好友添加事件"""
	logger.info(f"新增好友: {event.user_id}")


async def handle_group_recall(event: GroupRecallNoticeEvent):
	"""处理群消息撤回事件"""
	logger.info(f"群{event.group_id}消息撤回: 消息ID={event.message_id}, 用户={event.user_id}")


async def handle_friend_recall(event: FriendRecallNoticeEvent):
	"""处理好友消息撤回事件"""
	logger.info(f"好友{event.user_id}消息撤回: 消息ID={event.message_id}")


@notice_matcher.handle()
async def handle_notice(event: NoticeEvent):
	"""
	处理通知事件
	
	Args:
		event: 通知事件
	"""
	try:
		notice_type = event.notice_type
		logger.info(f"收到通知事件: {notice_type}")
		
		# 根据通知类型处理
		if isinstance(event, GroupIncreaseNoticeEvent):
			await handle_group_increase(event)
		elif isinstance(event, GroupDecreaseNoticeEvent):
			await handle_group_decrease(event)
		elif isinstance(event, FriendAddNoticeEvent):
			await handle_friend_add(event)
		elif isinstance(event, GroupRecallNoticeEvent):
			await handle_group_recall(event)
		elif isinstance(event, FriendRecallNoticeEvent):
			await handle_friend_recall(event)
		else:
			logger.debug(f"未处理的通知类型: {notice_type}")
	except Exception as e:
		logger.error(f"处理通知事件失败: {e}", exc_info=True)


async def handle_friend_request(event: FriendRequestEvent):
	"""处理好友请求事件"""
	logger.info(f"收到好友请求: {event.user_id}, 验证信息: {event.comment}")
	# 这里可以添加自动通过/拒绝逻辑


async def handle_group_request(event: GroupRequestEvent):
	"""处理加群请求事件"""
	logger.info(f"收到加群请求: 群{event.group_id}, 用户{event.user_id}, 验证信息: {event.comment}")
	# 这里可以添加自动通过/拒绝逻辑


@request_matcher.handle()
async def handle_request(event: RequestEvent):
	"""
	处理请求事件
	
	Args:
		event: 请求事件
	"""
	try:
		request_type = event.request_type
		logger.info(f"收到请求事件: {request_type}")
		
		# 根据请求类型处理
		if isinstance(event, FriendRequestEvent):
			await handle_friend_request(event)
		elif isinstance(event, GroupRequestEvent):
			await handle_group_request(event)
		else:
			logger.debug(f"未处理的请求类型: {request_type}")
	except Exception as e:
		logger.error(f"处理请求事件失败: {e}", exc_info=True)

