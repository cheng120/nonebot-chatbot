"""
基础命令插件
提供 hello、echo、calc、info 等基础命令功能
"""
from nonebot import on_command, on_message
from nonebot.adapters.onebot.v11 import MessageEvent, Message
from nonebot.params import CommandArg
from nonebot.plugin import PluginMetadata
from nonebot.rule import to_me
from src.utils.logger import get_logger
from src.utils.command_collector import get_all_plugin_commands, format_commands_for_help
from datetime import datetime

__plugin_meta__ = PluginMetadata(
	name="基础命令插件",
	description="提供基础命令功能：hello、echo、calc、info",
	usage="""
	可用命令：
	- hello - 打招呼
	- /echo <内容> - 回显内容
	- /calc <表达式> - 简单计算器
	- /info - 显示机器人信息
	@机器人 - 显示帮助信息
	""",
	type="application",
	homepage="https://github.com/your-username/nonebot-chatbot",
	supported_adapters={"~onebot.v11"},
)

logger = get_logger("hello_plugin")

# 1. 简单命令
hello_cmd = on_command("hello", aliases={"你好", "hi"}, priority=10, block=True)

@hello_cmd.handle()
async def handle_hello(event: MessageEvent):
	"""打招呼命令"""
	user_id = event.user_id
	logger.info(f"[hello_plugin] 用户 {user_id} 使用了 hello 命令")
	await hello_cmd.send(f"你好，用户 {user_id}！欢迎使用 NoneBot 机器人！")

# 2. 带参数的命令
echo_cmd = on_command("echo", priority=10, block=True)

@echo_cmd.handle()
async def handle_echo(event: MessageEvent, args: Message = CommandArg()):
	"""回显命令 - 显示用户输入的内容"""
	arg_str = str(args).strip()
	if arg_str:
		logger.info(f"用户 {event.user_id} 使用 echo 命令，参数: {arg_str}")
		await echo_cmd.send(f"📢 回显: {arg_str}")
	else:
		await echo_cmd.send("❌ 用法: /echo <内容>\n示例: /echo 你好世界")

# 3. 计算器命令
calc_cmd = on_command("calc", aliases={"计算", "计算器"}, priority=10, block=True)

@calc_cmd.handle()
async def handle_calc(event: MessageEvent, args: Message = CommandArg()):
	"""简单计算器"""
	try:
		expr = str(args).strip()
		if not expr:
			await calc_cmd.send("❌ 用法: /calc <表达式>\n示例: /calc 1+2*3")
			return
		
		# 简单的安全计算（仅支持基本运算）
		result = eval(expr)
		logger.info(f"用户 {event.user_id} 计算: {expr} = {result}")
		await calc_cmd.send(f"📊 计算结果: {expr} = {result}")
	except Exception as e:
		logger.error(f"计算错误: {e}")
		await calc_cmd.send(f"❌ 计算错误: {str(e)}")

# 4. 信息查询命令
info_cmd = on_command("info", aliases={"信息", "状态"}, priority=10, block=True)

@info_cmd.handle()
async def handle_info(event: MessageEvent):
	"""显示机器人信息"""
	# 获取已加载的插件数量
	try:
		from nonebot import get_loaded_plugins
		plugins = get_loaded_plugins()
		plugin_count = len(plugins)
		plugin_names = [p.name.split(".")[-1] for p in plugins]
	except:
		plugin_count = 0
		plugin_names = []
	
	info_text = f"""
🤖 机器人信息

• 插件名称: 基础命令插件 (hello)
• 当前时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
• 用户ID: {event.user_id}
• 消息类型: {event.message_type}
• 已加载插件: {plugin_count} 个
	""".strip()
	
	if plugin_names:
		info_text += f"\n• 插件列表: {', '.join(plugin_names[:10])}"
		if len(plugin_names) > 10:
			info_text += f" 等 {len(plugin_names)} 个"
	
	info_text += "\n\n💡 使用 /help 或 @我并发送「帮助」查看所有命令"
	
	await info_cmd.send(info_text)

# 5. @机器人时触发
at_me = on_message(priority=10, block=True, rule=to_me())

@at_me.handle()
async def handle_at_me(event: MessageEvent):
	"""处理@机器人的消息"""
	message = str(event.message).strip()
	logger.info(f"用户 {event.user_id} @了机器人，消息: {message}")
	
	# 简单的关键词回复
	if "帮助" in message or "help" in message.lower():
		# 获取所有已安装插件的命令
		try:
			commands_by_plugin = get_all_plugin_commands()
			help_text = format_commands_for_help(commands_by_plugin)
		except Exception as e:
			logger.error(f"获取插件命令时出错: {e}", exc_info=True)
			# 回退到基础帮助
			help_text = """
🤖 基础命令插件帮助

可用命令：
• hello - 打招呼
• /echo <内容> - 回显内容
• /calc <表达式> - 简单计算器
• /info - 显示机器人信息

直接@我也可以和我对话哦！
			""".strip()
		await at_me.send(help_text)
	else:
		await at_me.send(f"👋 你@我了！我收到了你的消息：{message}\n\n输入「帮助」查看可用命令")

# 6. 帮助命令
help_cmd = on_command("help", aliases={"帮助", "命令"}, priority=10, block=True)

@help_cmd.handle()
async def handle_help(event: MessageEvent, args: Message = CommandArg()):
	"""显示帮助信息"""
	arg_str = str(args).strip()
	
	if arg_str:
		# 显示特定命令的帮助（未来可以扩展）
		await help_cmd.send(f"💡 命令「{arg_str}」的详细帮助功能开发中...\n\n使用 /help 查看所有命令")
	else:
		# 显示所有命令
		try:
			commands_by_plugin = get_all_plugin_commands()
			help_text = format_commands_for_help(commands_by_plugin)
		except Exception as e:
			logger.error(f"获取插件命令时出错: {e}", exc_info=True)
			help_text = """
🤖 机器人帮助

基础命令：
• hello - 打招呼
• /echo <内容> - 回显内容
• /calc <表达式> - 简单计算器
• /info - 显示机器人信息
• /help - 显示此帮助信息

💡 提示: 直接@我并发送「帮助」也可以查看帮助
			""".strip()
		await help_cmd.send(help_text)

