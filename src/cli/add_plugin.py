"""
添加 NoneBot 插件命令
快速创建插件文件模板
"""
import argparse
import sys
from pathlib import Path
from typing import Optional


def get_plugin_template(
	plugin_name: str,
	description: str = "",
	usage: str = "",
	author: str = "NoneBot Chatbot Team",
	homepage: str = "https://github.com/your-username/nonebot-chatbot",
) -> str:
	"""
	生成插件模板代码
	
	Args:
		plugin_name: 插件名称
		description: 插件描述
		usage: 使用说明
		author: 作者
		homepage: 主页链接
		
	Returns:
		插件模板代码
	"""
	# 生成插件类名（首字母大写，下划线转驼峰）
	class_name = "".join(word.capitalize() for word in plugin_name.split("_"))
	
	# 默认描述
	if not description:
		description = f"{plugin_name} 插件"
	
	# 默认使用说明
	if not usage:
		usage = f"""
	可用命令：
	- /{plugin_name} - {description}
	
	使用方法：
	/{plugin_name}
	"""
	
	template = f'''"""
{description}
"""
from nonebot import on_command, on_message
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, Message, MessageSegment
from nonebot.params import CommandArg
from nonebot.plugin import PluginMetadata
from nonebot.rule import to_me
from src.utils.logger import get_logger

__plugin_meta__ = PluginMetadata(
	name="{plugin_name.replace('_', ' ').title()}",
	description="{description}",
	usage="""{usage.strip()}""",
	type="application",
	homepage="{homepage}",
	supported_adapters={{~onebot.v11}},
)

logger = get_logger("{plugin_name}")

# ========== 命令处理器 ==========

# 创建命令处理器
{plugin_name}_cmd = on_command("{plugin_name}", priority=10, block=True)

@{plugin_name}_cmd.handle()
async def handle_{plugin_name}(event: MessageEvent):
	"""处理 {plugin_name} 命令"""
	logger.info(f"用户 {{event.user_id}} 使用了 {plugin_name} 命令")
	await {plugin_name}_cmd.send("这是 {plugin_name} 插件的响应！")

# ========== 可选：消息处理器 ==========

# 如果需要@机器人触发，取消下面的注释
# at_me = on_message(priority=10, block=True, rule=to_me())
#
# @at_me.handle()
# async def handle_at_me(event: MessageEvent):
# 	"""处理@机器人的消息"""
# 	logger.info(f"用户 {{event.user_id}} @了机器人")
# 	await at_me.send("你@我了！")

# ========== 插件初始化（可选） ==========

def _init():
	"""插件初始化"""
	logger.info("{plugin_name} 插件已加载")

_init()
'''
	return template


def create_plugin_file(
	plugin_name: str,
	plugin_dir: Optional[Path] = None,
	description: str = "",
	usage: str = "",
	author: str = "NoneBot Chatbot Team",
	homepage: str = "https://github.com/your-username/nonebot-chatbot",
	force: bool = False,
) -> bool:
	"""
	创建插件文件
	
	Args:
		plugin_name: 插件名称（文件名，不含.py）
		plugin_dir: 插件目录（默认: src/plugins）
		description: 插件描述
		usage: 使用说明
		author: 作者
		homepage: 主页链接
		force: 是否覆盖已存在的文件
		
	Returns:
		是否成功
	"""
	# 验证插件名称
	if not plugin_name:
		print("❌ 错误: 插件名称不能为空")
		return False
	
	# 验证插件名称格式（只允许字母、数字、下划线）
	if not plugin_name.replace("_", "").isalnum():
		print("❌ 错误: 插件名称只能包含字母、数字和下划线")
		return False
	
	# 转换为小写
	plugin_name = plugin_name.lower()
	
	# 确定插件目录
	if plugin_dir is None:
		# 默认使用项目根目录下的 src/plugins
		current_file = Path(__file__)
		project_root = current_file.parent.parent.parent
		plugin_dir = project_root / "src" / "plugins"
	else:
		plugin_dir = Path(plugin_dir)
	
	# 确保插件目录存在
	plugin_dir.mkdir(parents=True, exist_ok=True)
	
	# 插件文件路径
	plugin_file = plugin_dir / f"{plugin_name}.py"
	
	# 检查文件是否已存在
	if plugin_file.exists() and not force:
		print(f"❌ 错误: 插件文件已存在: {plugin_file}")
		print("   使用 --force 参数可以覆盖已存在的文件")
		return False
	
	# 生成插件模板
	template = get_plugin_template(
		plugin_name=plugin_name,
		description=description,
		usage=usage,
		author=author,
		homepage=homepage,
	)
	
	# 写入文件
	try:
		plugin_file.write_text(template, encoding="utf-8")
		print(f"✅ 插件文件已创建: {plugin_file}")
		print(f"   插件名称: {plugin_name}")
		print(f"   文件路径: {plugin_file}")
		return True
	except Exception as e:
		print(f"❌ 错误: 创建插件文件失败: {e}")
		return False


def main():
	"""命令行入口"""
	parser = argparse.ArgumentParser(
		description="快速创建 NoneBot 插件",
		formatter_class=argparse.RawDescriptionHelpFormatter,
		epilog="""
示例:
  %(prog)s my_plugin
  %(prog)s weather --description "天气查询插件"
  %(prog)s admin --description "管理员插件" --usage "/admin - 管理员命令"
  %(prog)s my_plugin --dir ./custom_plugins
  %(prog)s my_plugin --force
		"""
	)
	
	parser.add_argument(
		"name",
		help="插件名称（文件名，不含.py，例如: my_plugin）"
	)
	
	parser.add_argument(
		"-d", "--description",
		default="",
		help="插件描述（默认: 插件名称）"
	)
	
	parser.add_argument(
		"-u", "--usage",
		default="",
		help="使用说明（默认: 自动生成）"
	)
	
	parser.add_argument(
		"--dir",
		help="插件目录（默认: src/plugins）"
	)
	
	parser.add_argument(
		"--author",
		default="NoneBot Chatbot Team",
		help="作者（默认: NoneBot Chatbot Team）"
	)
	
	parser.add_argument(
		"--homepage",
		default="https://github.com/your-username/nonebot-chatbot",
		help="主页链接"
	)
	
	parser.add_argument(
		"-f", "--force",
		action="store_true",
		help="覆盖已存在的文件"
	)
	
	args = parser.parse_args()
	
	# 创建插件文件
	plugin_dir = Path(args.dir) if args.dir else None
	success = create_plugin_file(
		plugin_name=args.name,
		plugin_dir=plugin_dir,
		description=args.description,
		usage=args.usage,
		author=args.author,
		homepage=args.homepage,
		force=args.force,
	)
	
	if success:
		print("\n📝 下一步:")
		print("1. 编辑插件文件，实现你的功能")
		print("2. 在数据库中启用插件（如果需要）:")
		print(f"   sqlite3 data/bot.db \"INSERT INTO plugin_configs (plugin_name, enabled, config_data) VALUES ('{args.name}', 1, '{{}}');\"")
		print("3. 重启机器人")
		sys.exit(0)
	else:
		sys.exit(1)


if __name__ == "__main__":
	main()

