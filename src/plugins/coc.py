"""
COC 骰子插件
移植自 nonebot-plugin-cocdicer，提供 COC 角色属性生成和技能检定功能
"""
from nonebot import on_command
from nonebot.adapters.onebot.v11 import MessageEvent, Message
from nonebot.params import CommandArg
from nonebot.plugin import PluginMetadata
from src.utils.logger import get_logger
import random
from typing import Dict, Tuple

__plugin_meta__ = PluginMetadata(
	name="COC 骰子插件",
	description="提供 COC 角色属性生成和技能检定功能",
	usage="""
	可用命令：
	- /coc - 生成 COC 角色属性
	- /ra <技能值> [难度] - COC 技能检定
	""",
	type="application",
	homepage="https://github.com/your-username/nonebot-chatbot",
	supported_adapters={"~onebot.v11"},
)

logger = get_logger("coc_plugin")

coc_cmd = on_command("coc", aliases={"coc骰子", "克苏鲁", "cocdice"}, priority=10, block=True)
coc_ra_cmd = on_command("ra", aliases={"检定", "ra检定"}, priority=10, block=True)

def roll_dice(sides: int = 100) -> int:
	"""
	投掷骰子
	
	Args:
		sides: 骰子面数，默认100
		
	Returns:
		骰子结果
	"""
	return random.randint(1, sides)

def coc_roll_attributes() -> Dict[str, int]:
	"""
	生成 COC 角色属性（3d6*5 或 4d6取3高*5）
	
	Returns:
		属性字典
	"""
	attributes = {}
	
	# 力量(STR)、体质(CON)、体型(SIZ)、敏捷(DEX)、外貌(APP)、智力(INT)、意志(POW)、教育(EDU)
	attr_names = ["STR", "CON", "SIZ", "DEX", "APP", "INT", "POW", "EDU"]
	
	for attr in attr_names:
		if attr == "EDU":
			# 教育使用 2d6+6
			rolls = [roll_dice(6) for _ in range(2)]
			value = sum(rolls) + 6
		else:
			# 其他属性使用 3d6
			rolls = [roll_dice(6) for _ in range(3)]
			value = sum(rolls)
		
		# 乘以5得到最终属性值
		attributes[attr] = value * 5
	
	# 计算衍生属性
	attributes["HP"] = (attributes["CON"] + attributes["SIZ"]) // 10
	attributes["MP"] = attributes["POW"] // 5
	attributes["SAN"] = attributes["POW"]
	
	return attributes

def format_coc_attributes(attributes: Dict[str, int]) -> str:
	"""
	格式化 COC 属性显示
	
	Args:
		attributes: 属性字典
		
	Returns:
		格式化后的字符串
	"""
	lines = [
		"📊 COC 角色属性:",
		"",
		"基础属性:",
		f"• 力量(STR): {attributes['STR']}",
		f"• 体质(CON): {attributes['CON']}",
		f"• 体型(SIZ): {attributes['SIZ']}",
		f"• 敏捷(DEX): {attributes['DEX']}",
		f"• 外貌(APP): {attributes['APP']}",
		f"• 智力(INT): {attributes['INT']}",
		f"• 意志(POW): {attributes['POW']}",
		f"• 教育(EDU): {attributes['EDU']}",
		"",
		"衍生属性:",
		f"• 生命值(HP): {attributes['HP']}",
		f"• 魔法值(MP): {attributes['MP']}",
		f"• 理智值(SAN): {attributes['SAN']}",
	]
	return "\n".join(lines)

@coc_cmd.handle()
async def handle_coc(event: MessageEvent):
	"""COC 角色属性生成"""
	attributes = coc_roll_attributes()
	result = format_coc_attributes(attributes)
	
	logger.info(f"用户 {event.user_id} 生成了 COC 角色属性")
	await coc_cmd.send(result)

def coc_skill_check(skill_value: int, difficulty: str = "常规") -> Tuple[int, int, str]:
	"""
	COC 技能检定
	
	Args:
		skill_value: 技能值
		difficulty: 难度等级（常规/困难/极难）
		
	Returns:
		(骰子结果, 难度值, 结果描述)
	"""
	dice_result = roll_dice(100)
	
	# 计算难度值
	if difficulty == "困难":
		target = skill_value // 2
	elif difficulty == "极难":
		target = skill_value // 5
	else:  # 常规
		target = skill_value
	
	# 判断结果
	if dice_result == 1:
		result = "大成功！"
		emoji = "🌟"
	elif dice_result == 100:
		result = "大失败！"
		emoji = "💀"
	elif dice_result <= target // 5:
		result = "极难成功"
		emoji = "✨"
	elif dice_result <= target // 2:
		result = "困难成功"
		emoji = "😊"
	elif dice_result <= target:
		result = "常规成功"
		emoji = "🙂"
	else:
		result = "失败"
		emoji = "😕"
	
	return dice_result, target, f"{emoji} {result}"

@coc_ra_cmd.handle()
async def handle_ra(event: MessageEvent, args: Message = CommandArg()):
	"""COC 技能检定命令"""
	arg_str = str(args).strip()
	
	if not arg_str:
		await coc_ra_cmd.send("""
❌ 用法: /ra <技能值> [难度]

示例:
• /ra 50 - 常规难度检定（技能值50）
• /ra 60 困难 - 困难难度检定（技能值60）
• /ra 70 极难 - 极难难度检定（技能值70）

难度说明:
• 常规: 技能值 = 目标值
• 困难: 技能值 / 2 = 目标值
• 极难: 技能值 / 5 = 目标值
		""".strip())
		return
	
	# 解析参数
	parts = arg_str.split()
	skill_value = None
	difficulty = "常规"
	
	try:
		if len(parts) == 1:
			skill_value = int(parts[0])
		elif len(parts) >= 2:
			skill_value = int(parts[0])
			difficulty = parts[1]
		else:
			await coc_ra_cmd.send("❌ 参数格式错误，请使用: /ra <技能值> [难度]")
			return
	except ValueError:
		await coc_ra_cmd.send("❌ 技能值必须是数字")
		return
	
	if skill_value < 1 or skill_value > 100:
		await coc_ra_cmd.send("❌ 技能值必须在 1-100 之间")
		return
	
	# 执行检定
	dice_result, target, result_text = coc_skill_check(skill_value, difficulty)
	
	reply = f"""
🎲 COC 技能检定

技能值: {skill_value}
难度: {difficulty}
目标值: {target}
骰子结果: {dice_result}

{result_text}
	""".strip()
	
	logger.info(f"用户 {event.user_id} 进行了 COC 检定: 技能值={skill_value}, 难度={difficulty}, 结果={dice_result}")
	await coc_ra_cmd.send(reply)

