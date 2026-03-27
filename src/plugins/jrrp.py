"""
今日人品插件
移植自 nonebot-plugin-jrrp3，提供今日人品查询功能
"""
from nonebot import on_command
from nonebot.adapters.onebot.v11 import MessageEvent
from nonebot.plugin import PluginMetadata
from src.utils.logger import get_logger
import hashlib
from datetime import datetime

__plugin_meta__ = PluginMetadata(
	name="今日人品插件",
	description="提供今日人品查询功能，基于用户ID和日期生成",
	usage="""
	可用命令：
	- /jrrp 或 /今日人品 - 查看今日人品值
	- /人品 或 /rp - 查看今日人品值
	""",
	type="application",
	homepage="https://github.com/your-username/nonebot-chatbot",
	supported_adapters={"~onebot.v11"},
)

logger = get_logger("jrrp_plugin")

jrrp_cmd = on_command("jrrp", aliases={"今日人品", "人品", "rp"}, priority=10, block=True)

def get_jrrp(user_id: int) -> int:
	"""
	获取用户今日人品值（0-100）
	基于用户ID和日期生成，确保同一天同一用户的人品值相同
	
	Args:
		user_id: 用户ID
		
	Returns:
		人品值（0-100）
	"""
	# 获取今天的日期字符串（格式：YYYY-MM-DD）
	today = datetime.now().strftime("%Y-%m-%d")
	
	# 使用用户ID和日期生成唯一字符串
	seed = f"{user_id}_{today}"
	
	# 使用MD5哈希生成随机数
	hash_obj = hashlib.md5(seed.encode())
	hash_hex = hash_obj.hexdigest()
	
	# 将哈希值转换为0-100的整数
	jrrp_value = int(hash_hex[:8], 16) % 101
	
	return jrrp_value

def get_jrrp_emoji(jrrp_value: int) -> str:
	"""
	根据人品值返回对应的表情符号
	
	Args:
		jrrp_value: 人品值（0-100）
		
	Returns:
		表情符号
	"""
	if jrrp_value >= 90:
		return "🌟"
	elif jrrp_value >= 80:
		return "✨"
	elif jrrp_value >= 70:
		return "😊"
	elif jrrp_value >= 60:
		return "🙂"
	elif jrrp_value >= 50:
		return "😐"
	elif jrrp_value >= 40:
		return "😕"
	elif jrrp_value >= 30:
		return "😟"
	elif jrrp_value >= 20:
		return "😰"
	elif jrrp_value >= 10:
		return "😱"
	else:
		return "💀"

def get_jrrp_text(jrrp_value: int) -> str:
	"""
	根据人品值返回对应的文字描述
	
	Args:
		jrrp_value: 人品值（0-100）
		
	Returns:
		文字描述
	"""
	if jrrp_value >= 90:
		return "大吉大利！"
	elif jrrp_value >= 80:
		return "运气不错！"
	elif jrrp_value >= 70:
		return "还算可以"
	elif jrrp_value >= 60:
		return "平平淡淡"
	elif jrrp_value >= 50:
		return "一般般"
	elif jrrp_value >= 40:
		return "有点倒霉"
	elif jrrp_value >= 30:
		return "不太顺利"
	elif jrrp_value >= 20:
		return "运气很差"
	elif jrrp_value >= 10:
		return "非常糟糕"
	else:
		return "极度不幸"

@jrrp_cmd.handle()
async def handle_jrrp(event: MessageEvent):
	"""今日人品命令"""
	user_id = event.user_id
	
	# 获取今日人品值
	jrrp_value = get_jrrp(user_id)
	emoji = get_jrrp_emoji(jrrp_value)
	text = get_jrrp_text(jrrp_value)
	
	# 获取用户昵称
	user_name = "你"
	if hasattr(event, 'sender'):
		if hasattr(event.sender, 'nickname') and event.sender.nickname:
			user_name = event.sender.nickname
		elif hasattr(event.sender, 'card') and event.sender.card:
			user_name = event.sender.card
	
	# 构建回复消息
	reply = f"""
{emoji} {user_name} 的今日人品：{jrrp_value}/100

{text}

💡 提示：人品值每天都会更新，同一天内保持不变
	""".strip()
	
	logger.info(f"用户 {user_id} 查询今日人品: {jrrp_value}")
	await jrrp_cmd.send(reply)

