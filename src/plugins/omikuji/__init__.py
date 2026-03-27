import contextlib
import os
from datetime import datetime

from nonebot import get_driver, logger
from nonebot.plugin import PluginMetadata, require

require("nonebot_plugin_localstore")
require("nonebot_plugin_orm")
from importlib import metadata

from . import commands, sql_models
from .cache import OmikujiCache
from .config import get_cache_dir, get_config

_HAS_SUGGARCHAT = False
Menu = None
ToolsManager = None
TOOL_DATA = None

# SuggarChat / Amrita 的 WebUI 在部分环境下可能会因为 FastAPI 生命周期问题加载失败。
# 御神签的“聊天抽签”属于可选功能：即使 SuggarChat 不可用，也应保证 `omikuji` 指令本体可用。
try:
	require("nonebot_plugin_suggarchat")
	from nonebot_plugin_suggarchat.API import Menu as _Menu, ToolsManager as _ToolsManager
	from .llm_tool import TOOL_DATA as _TOOL_DATA
	Menu = _Menu
	ToolsManager = _ToolsManager
	TOOL_DATA = _TOOL_DATA
	_HAS_SUGGARCHAT = True
except Exception as e:
	logger.warning(f"omikuji：nonebot_plugin_suggarchat 加载失败，将跳过聊天抽签工具注册：{e}")

__plugin_meta__ = PluginMetadata(
    name="御神签",
    description="依赖SuggarChat的聊天御神签抽签插件模块",
    usage="/omikuji [板块]\n/omikuji 解签\n或者使用聊天直接抽签。",
    type="application",
    homepage="https://github.com/LiteSuggarDEV/nonebot_plugin_omikuji",
    supported_adapters={"~onebot.v11"},
)

__all__ = ["commands", "sql_models"]


@get_driver().on_startup
async def init():
    version = "Unknown"
    with contextlib.suppress(Exception):
        version = metadata.version("nonebot_plugin_omikuji")
        if "dev" in version:
            logger.warning("当前版本为开发版本，可能存在不稳定情况！")
    logger.info(f"Loading OMIKUJI V{version}......")
    conf = get_config()
    if conf.enable_omikuji:
        if _HAS_SUGGARCHAT and ToolsManager and TOOL_DATA and Menu:
            ToolsManager().register_tool(TOOL_DATA)
            Menu().reg_menu("omikuji", "抽御神签", "[可选]主题")
    logger.info("正在初始化缓存数据......")
    os.makedirs(get_cache_dir(), exist_ok=True)
    for cache in get_cache_dir().glob("*.json"):
        if cache is not None:
            with cache.open("r", encoding="utf-8") as f:
                data = OmikujiCache.model_validate_json(f.read())
            if not data.timestamp.date() == datetime.now().date():
                os.remove(str(cache))
    logger.info("缓存数据初始化完成！")
