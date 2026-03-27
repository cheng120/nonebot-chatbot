"""
宝可梦猜谜插件配置管理
提供命令来动态配置 nonebot_plugin_pokemonle 插件的参数
"""
import yaml
import json
from pathlib import Path
from typing import Optional, List, Union
from nonebot import on_command, get_plugin_config
from nonebot.adapters.onebot.v11 import MessageEvent, Message
from nonebot.params import CommandArg
from nonebot.plugin import PluginMetadata
from src.utils.logger import get_logger

__plugin_meta__ = PluginMetadata(
	name="宝可梦猜谜配置管理",
	description="动态配置 nonebot_plugin_pokemonle 插件的参数",
	usage="""
可用命令：
- /pokemonle_config - 查看当前配置
- /pokemonle_config set <参数名> <值> - 设置配置参数
- /pokemonle_config max_attempts <数字> - 设置最大尝试次数
- /pokemonle_config gens <世代列表> - 设置世代选择，例如：/pokemonle_config gens 第一世代,第三世代,第五世代
- /pokemonle_config cheat <true/false> - 开启/关闭恶作剧
	""",
	type="application",
	homepage="https://github.com/your-username/nonebot-chatbot",
	supported_adapters={"~onebot.v11"},
)

logger = get_logger("pokemonle_config")

# 配置文件路径
CONFIG_PATH = Path(__file__).parent.parent.parent / "configs" / "config.yaml"

# 世代映射（中文到数字）
GEN_MAP = {
	"第一世代": 1, "1": 1,
	"第二世代": 2, "2": 2,
	"第三世代": 3, "3": 3,
	"第四世代": 4, "4": 4,
	"第五世代": 5, "5": 5,
	"第六世代": 6, "6": 6,
	"第七世代": 7, "7": 7,
	"第八世代": 8, "8": 8,
	"第九世代": 9, "9": 9,
}

def get_config_path() -> Path:
	"""获取配置文件路径"""
	return CONFIG_PATH

def load_yaml_config() -> dict:
	"""加载 YAML 配置"""
	try:
		with open(get_config_path(), "r", encoding="utf-8") as f:
			return yaml.safe_load(f) or {}
	except Exception as e:
		logger.error(f"加载配置文件失败: {e}")
		return {}

def save_yaml_config(config: dict) -> bool:
	"""保存 YAML 配置"""
	try:
		with open(get_config_path(), "w", encoding="utf-8") as f:
			yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
		logger.info(f"配置文件已保存: {get_config_path()}")
		return True
	except Exception as e:
		logger.error(f"保存配置文件失败: {e}")
		return False

def get_current_config() -> dict:
	"""获取当前配置"""
	config = load_yaml_config()
	pokemonle_config = config.get("pokemonle", {})
	
	# 获取默认值
	current = {
		"pokemonle_max_attempts": pokemonle_config.get("pokemonle_max_attempts", 10),
		"pokemonle_gens": pokemonle_config.get("pokemonle_gens", []),
		"pokemonle_cheat": pokemonle_config.get("pokemonle_cheat", False),
	}
	return current

def update_config(key: str, value: Union[int, bool, List]) -> bool:
	"""更新配置"""
	config = load_yaml_config()
	
	# 确保 pokemonle 节点存在
	if "pokemonle" not in config:
		config["pokemonle"] = {}
	
	# 更新配置值
	config["pokemonle"][key] = value
	
	# 保存配置
	return save_yaml_config(config)

# 查看配置命令
config_cmd = on_command("pokemonle_config", aliases={"宝可梦配置", "pokemonle配置"}, priority=10, block=True)

@config_cmd.handle()
async def handle_config(event: MessageEvent, args: Message = CommandArg()):
	"""处理配置命令"""
	arg_str = str(args).strip()
	
	if not arg_str:
		# 显示当前配置
		current = get_current_config()
		
		# 格式化世代列表
		gens_str = "全部世代" if not current["pokemonle_gens"] else ", ".join([f"第{gen}世代" for gen in current["pokemonle_gens"]])
		
		config_text = f"""
🎮 宝可梦猜谜插件当前配置

• 最大尝试次数: {current['pokemonle_max_attempts']}
• 世代选择: {gens_str}
• 恶作剧功能: {'开启' if current['pokemonle_cheat'] else '关闭'}

💡 使用 /pokemonle_config set <参数名> <值> 来修改配置
💡 使用 /pokemonle_config max_attempts <数字> 设置尝试次数
💡 使用 /pokemonle_config gens <世代列表> 设置世代
💡 使用 /pokemonle_config cheat <true/false> 开启/关闭恶作剧

⚠️ 注意: 修改配置后需要重启机器人才能生效
		""".strip()
		
		await config_cmd.send(config_text)
		return
	
	# 解析命令
	parts = arg_str.split(None, 1)
	subcommand = parts[0].lower()
	
	if subcommand == "set" and len(parts) > 1:
		# 设置配置: /pokemonle_config set <参数名> <值>
		params = parts[1].split(None, 1)
		if len(params) < 2:
			await config_cmd.send("❌ 用法: /pokemonle_config set <参数名> <值>\n示例: /pokemonle_config set pokemonle_max_attempts 5")
			return
		
		key = params[0]
		value_str = params[1]
		
		# 解析值
		if key == "pokemonle_max_attempts":
			try:
				value = int(value_str)
				if value < 1:
					await config_cmd.send("❌ 最大尝试次数必须大于 0")
					return
			except ValueError:
				await config_cmd.send("❌ 最大尝试次数必须是数字")
				return
		elif key == "pokemonle_gens":
			# 解析世代列表
			gens = [g.strip() for g in value_str.split(",")]
			gen_nums = []
			for gen in gens:
				if gen in GEN_MAP:
					gen_num = GEN_MAP[gen]
					if gen_num not in gen_nums:
						gen_nums.append(gen_num)
				else:
					await config_cmd.send(f"❌ 无效的世代: {gen}\n可用世代: 第一世代, 第二世代, ..., 第九世代 或 1, 2, ..., 9")
					return
			value = gen_nums
		elif key == "pokemonle_cheat":
			value = value_str.lower() in ("true", "1", "yes", "开启", "on")
		else:
			await config_cmd.send(f"❌ 未知的配置参数: {key}\n可用参数: pokemonle_max_attempts, pokemonle_gens, pokemonle_cheat")
			return
		
		# 更新配置
		if update_config(key, value):
			await config_cmd.send(f"✅ 配置已更新: {key} = {value}\n⚠️ 请重启机器人使配置生效")
		else:
			await config_cmd.send("❌ 配置更新失败，请查看日志")
	
	elif subcommand == "max_attempts" and len(parts) > 1:
		# 设置最大尝试次数: /pokemonle_config max_attempts <数字>
		try:
			value = int(parts[1])
			if value < 1:
				await config_cmd.send("❌ 最大尝试次数必须大于 0")
				return
			
			if update_config("pokemonle_max_attempts", value):
				await config_cmd.send(f"✅ 最大尝试次数已设置为: {value}\n⚠️ 请重启机器人使配置生效")
			else:
				await config_cmd.send("❌ 配置更新失败，请查看日志")
		except ValueError:
			await config_cmd.send("❌ 最大尝试次数必须是数字\n示例: /pokemonle_config max_attempts 5")
	
	elif subcommand == "gens" and len(parts) > 1:
		# 设置世代: /pokemonle_config gens <世代列表>
		gens_str = parts[1]
		gens = [g.strip() for g in gens_str.split(",")]
		gen_nums = []
		
		for gen in gens:
			if gen in GEN_MAP:
				gen_num = GEN_MAP[gen]
				if gen_num not in gen_nums:
					gen_nums.append(gen_num)
			else:
				await config_cmd.send(f"❌ 无效的世代: {gen}\n可用世代: 第一世代, 第二世代, ..., 第九世代 或 1, 2, ..., 9\n示例: /pokemonle_config gens 第一世代,第三世代,第五世代")
				return
		
		# 如果为空，表示全部世代
		if not gen_nums:
			gen_nums = []
		
		if update_config("pokemonle_gens", gen_nums):
			if gen_nums:
				gens_display = ", ".join([f"第{gen}世代" for gen in gen_nums])
				await config_cmd.send(f"✅ 世代选择已设置为: {gens_display}\n⚠️ 请重启机器人使配置生效")
			else:
				await config_cmd.send(f"✅ 世代选择已设置为: 全部世代\n⚠️ 请重启机器人使配置生效")
		else:
			await config_cmd.send("❌ 配置更新失败，请查看日志")
	
	elif subcommand == "cheat" and len(parts) > 1:
		# 设置恶作剧: /pokemonle_config cheat <true/false>
		value_str = parts[1].lower()
		value = value_str in ("true", "1", "yes", "开启", "on", "enable")
		
		if update_config("pokemonle_cheat", value):
			status = "开启" if value else "关闭"
			await config_cmd.send(f"✅ 恶作剧功能已{status}\n⚠️ 请重启机器人使配置生效")
		else:
			await config_cmd.send("❌ 配置更新失败，请查看日志")
	
	else:
		await config_cmd.send("""
❌ 未知的子命令

可用命令：
• /pokemonle_config - 查看当前配置
• /pokemonle_config max_attempts <数字> - 设置最大尝试次数
• /pokemonle_config gens <世代列表> - 设置世代选择
• /pokemonle_config cheat <true/false> - 开启/关闭恶作剧

示例：
• /pokemonle_config max_attempts 5
• /pokemonle_config gens 第一世代,第三世代,第五世代
• /pokemonle_config cheat true
		""".strip())

