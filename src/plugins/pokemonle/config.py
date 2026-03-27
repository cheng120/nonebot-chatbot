from nonebot import get_plugin_config, get_driver
from pydantic import BaseModel
from pathlib import Path
import yaml
from loguru import logger

class Config(BaseModel):
    #猜宝可梦最大尝试次数
    pokemonle_max_attempts: int = 10
    #世代选择，空代表都选
    pokemonle_gens: list = []
    #是否开启恶作剧
    pokemonle_cheat: bool = False

# 尝试从 get_plugin_config 获取配置
try:
    plugin_config = get_plugin_config(Config)
    logger.info(f"[pokemonle config] get_plugin_config 返回: max_attempts={plugin_config.pokemonle_max_attempts}, gens={plugin_config.pokemonle_gens}, cheat={plugin_config.pokemonle_cheat}")
except Exception as e:
    logger.warning(f"[pokemonle config] get_plugin_config 失败: {e}")
    plugin_config = Config()

# 如果配置是默认值，尝试从配置文件直接读取
if plugin_config.pokemonle_max_attempts == 10 and not plugin_config.pokemonle_gens:
    try:
        # 尝试从多个可能的配置文件路径读取
        possible_config_paths = [
            Path(__file__).parent.parent.parent.parent / "configs" / "config.yaml",  # 项目根目录
            Path(__file__).parent.parent.parent / "configs" / "config.yaml",  # 另一种路径
            Path.cwd() / "configs" / "config.yaml",  # 当前工作目录
        ]
        
        for config_path in possible_config_paths:
            if config_path.exists():
                with open(config_path, "r", encoding="utf-8") as f:
                    yaml_config = yaml.safe_load(f) or {}
                
                # 尝试多种可能的配置键名
                possible_keys = [
                    "nonebot_plugin_pokemonle",
                    "nonebot-plugin-pokemonle",
                    "pokemonle",
                ]
                
                for key in possible_keys:
                    if key in yaml_config:
                        config_data = yaml_config[key]
                        if isinstance(config_data, dict):
                            # 更新配置
                            if "pokemonle_max_attempts" in config_data:
                                plugin_config.pokemonle_max_attempts = config_data["pokemonle_max_attempts"]
                            if "pokemonle_gens" in config_data:
                                plugin_config.pokemonle_gens = config_data["pokemonle_gens"]
                            if "pokemonle_cheat" in config_data:
                                plugin_config.pokemonle_cheat = config_data["pokemonle_cheat"]
                            logger.info(f"[pokemonle config] 从配置文件 {config_path} 读取配置 (键名: {key}): max_attempts={plugin_config.pokemonle_max_attempts}, gens={plugin_config.pokemonle_gens}, cheat={plugin_config.pokemonle_cheat}")
                            break
                break
    except Exception as e:
        logger.warning(f"[pokemonle config] 从配置文件读取失败: {e}")

logger.info(f"[pokemonle config] 最终配置: max_attempts={plugin_config.pokemonle_max_attempts}, gens={plugin_config.pokemonle_gens}, cheat={plugin_config.pokemonle_cheat}")