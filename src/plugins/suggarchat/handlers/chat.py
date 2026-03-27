"""聊天处理器模块"""

from nonebot import get_driver
from nonebot.adapters.onebot.v11 import Bot, Message, MessageSegment
from nonebot.adapters.onebot.v11.event import MessageEvent
from nonebot.matcher import Matcher

from ..chatmanager import ChatObject
from ..check_rule import _is_chat_command

command_prefix = get_driver().config.command_start or "/"


class _ChatCommandEvent:
	"""包装事件：将 /chat xxx 的正文作为消息内容，其余委托给原 event。
	实现 __contains__/__getitem__/__setitem__ 以通过 OneBot MessageEvent 的 model_validator(check_message)。
	"""

	__slots__ = ("_event", "_stripped", "_message", "_original_message")

	def __init__(self, event: MessageEvent, stripped_text: str):
		self._event = event
		self._stripped = stripped_text
		self._message = Message(MessageSegment.text(stripped_text))
		self._original_message = None

	def __getattr__(self, name: str):
		return getattr(self._event, name)

	def __contains__(self, key: str) -> bool:
		return key in ("message", "original_message")

	def __getitem__(self, key: str):
		if key == "message":
			return self._message
		if key == "original_message":
			return self._original_message if self._original_message is not None else self._message
		raise KeyError(key)

	def __setitem__(self, key: str, value) -> None:
		if key == "original_message":
			object.__setattr__(self, "_original_message", value)
			return
		raise KeyError(key)

	@property
	def message(self) -> Message:
		return self._message

	def get_plaintext(self) -> str:
		return self._stripped


async def chat_command_handler(event: MessageEvent, matcher: Matcher, bot: Bot):
	"""仅处理 /chat 或 /chat xxx 命令，将正文交给聊天流程。供 on_command('chat') 使用。"""
	text = event.message.extract_plain_text().strip()
	prefixes = get_driver().config.command_start or ["/"]
	rest = text
	for p in prefixes:
		if p and rest.startswith(p):
			rest = rest[len(p):].strip()
			break
	content = (rest[5:].strip() if rest.startswith("chat ") else ("" if rest == "chat" else rest))
	wrapped = _ChatCommandEvent(event, content)
	return await (ChatObject().caller())(wrapped, matcher, bot)


async def entry(event: MessageEvent, matcher: Matcher, bot: Bot):
    """聊天处理器入口函数

    该函数作为消息事件的入口点，处理命令前缀检查并启动聊天对象。
    """
    text = event.message.extract_plain_text().strip()
    if any(
        text.startswith(prefix)
        for prefix in command_prefix
        if prefix.strip()
    ):
        if _is_chat_command(text):
            # /chat 或 /chat xxx：剥掉前缀后只保留正文再交给聊天流程
            prefixes = get_driver().config.command_start or ["/"]
            rest = text
            for p in prefixes:
                if p and rest.startswith(p):
                    rest = rest[len(p):].strip()
                    break
            content = (rest[5:].strip() if rest.startswith("chat ") else ("" if rest == "chat" else rest))
            event = _ChatCommandEvent(event, content or rest)
        else:
            matcher.skip()
            return
    return await (ChatObject().caller())(event, matcher, bot)
