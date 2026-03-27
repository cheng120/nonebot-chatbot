"""
图片发送插件
提供图片发送功能
"""
from nonebot import on_command
from nonebot.adapters.onebot.v11 import MessageEvent, Message, MessageSegment
from nonebot.params import CommandArg
from nonebot.plugin import PluginMetadata
from src.utils.logger import get_logger

__plugin_meta__ = PluginMetadata(
	name="图片发送插件",
	description="提供图片发送功能",
	usage="""
	可用命令：
	- /image [URL] - 发送图片
	- /图片 [URL] - 发送图片
	""",
	type="application",
	homepage="https://github.com/your-username/nonebot-chatbot",
	supported_adapters={"~onebot.v11"},
)

logger = get_logger("image_plugin")

image_cmd = on_command("image", aliases={"图片"}, priority=10, block=True)

@image_cmd.handle()
async def handle_image(event: MessageEvent, args: Message = CommandArg()):
	"""发送图片示例"""
	arg_str = str(args).strip()
	
	if arg_str and arg_str.startswith("http"):
		# 发送网络图片
		try:
			await image_cmd.send(MessageSegment.image(arg_str))
			logger.info(f"用户 {event.user_id} 请求发送图片: {arg_str}")
		except Exception as e:
			logger.error(f"发送图片失败: {e}")
			await image_cmd.send(f"❌ 发送图片失败: {str(e)}")
	else:
		# 发送示例图片（使用占位图服务）
		placeholder_url = "https://via.placeholder.com/400x300/4CAF50/FFFFFF?text=NoneBot+Plugin"
		await image_cmd.send(MessageSegment.image(placeholder_url))
		await image_cmd.send("💡 提示: 使用 /image <图片URL> 可以发送指定图片")

