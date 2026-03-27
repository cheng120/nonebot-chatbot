#!usr/bin/env python3
# -*- coding: utf-8 -*-
from .download_xiuxian_data import download_xiuxian_data
from nonebot.plugin import PluginMetadata
from nonebot.log import logger
from nonebot.message import event_preprocessor, IgnoredException
from nonebot.adapters.onebot.v11 import (
    Bot,
    GroupMessageEvent
)
from nonebot import get_driver
from .xiuxian_config import XiuConfig
from pathlib import Path
from pkgutil import iter_modules
from nonebot.log import logger
from nonebot import require, load_all_plugins, get_plugin_by_module_name
from .config import config as _config


DRIVER = get_driver()

try:
    NICKNAME: str = list(DRIVER.config.nickname)[0]
except Exception as e:
    logger.info(f"缺少超级用户配置文件，{e}!")
    NICKNAME = 'bot'

try:
    download_xiuxian_data()
except Exception as e:
    logger.warning(f"下载修仙配置文件失败: {e}，插件将继续加载，但部分功能可能无法使用。请稍后手动下载数据文件。")
    # 不再抛出异常，允许插件加载，但数据文件可能不存在

put_bot = XiuConfig().put_bot
shield_group = XiuConfig().shield_group

try:
    put_bot_ = put_bot[0]
except:
    logger.info(f"修仙插件没有配置put_bot,如果有多个qq和nb链接,请务必配置put_bot,具体介绍参考【风控帮助】！")

require('nonebot_plugin_apscheduler')

# 检测是否在项目内运行（模块名包含 src.plugins.xiuxian_2）
# 或者作为独立插件运行（模块名为 xiuxian 或 nonebot_plugin_xiuxian_2.xiuxian）
current_module = __name__
is_local_plugin = "src.plugins.xiuxian_2" in current_module

# 检查插件是否已加载（支持多种模块名格式）
plugin_loaded = (
    get_plugin_by_module_name("xiuxian") or
    get_plugin_by_module_name("xiuxian_2") or
    get_plugin_by_module_name("src.plugins.xiuxian_2.xiuxian") or
    get_plugin_by_module_name(current_module)
)

if plugin_loaded or is_local_plugin:
    # 确定模块前缀
    if is_local_plugin:
        # 项目内运行：使用完整模块路径
        module_prefix = current_module
        logger.info(f"项目内运行模式，使用模块前缀: {module_prefix}")
    else:
        # 独立插件运行：使用 xiuxian 前缀
        module_prefix = "xiuxian"
        logger.info("独立插件运行模式，使用模块前缀: xiuxian")
    
    # 加载子模块
    submodules = [
        f"{module_prefix}.{module.name}"
        for module in iter_modules([str(Path(__file__).parent)])
        if module.ispkg
        and (
            (name := module.name[11:]) == "meta"
            or name not in _config.disabled_plugins
        )
        # module.name[:11] == xiuxian_
    ]
    
    if submodules:
        logger.info(f"开始加载 {len(submodules)} 个子模块: {submodules}")
        try:
            load_all_plugins(submodules, [])
            logger.info(f"修仙插件子模块加载完成")
        except Exception as e:
            logger.error(f"修仙插件子模块加载失败: {e}", exc_info=True)
    else:
        logger.warning("未找到需要加载的子模块")

__plugin_meta__ = PluginMetadata(
    name='修仙模拟器',
    description='',
    usage=(
        "必死之境机逢仙缘，修仙之路波澜壮阔！\n"
        " 输入 < 修仙帮助 > 获取仙界信息"
    ),
    extra={
        "show": True,
        "priority": 15
    }
)


def _is_xiuxian_switch_cmd(msg: str) -> bool:
    """是否为启用/禁用修仙功能指令（任意 bot 都需响应，便于群管开启）"""
    msg = (msg or "").strip()
    return msg in ("启用修仙功能", "禁用修仙功能")


@event_preprocessor
async def do_something(bot: Bot, event: GroupMessageEvent):
    """事件预处理器：检查bot和群组配置"""
    global put_bot
    # 启用/禁用修仙功能：不因 put_bot 忽略，保证群管在任何连接上都能开启
    raw = event.message.extract_plain_text().strip()
    if _is_xiuxian_switch_cmd(raw):
        return
    if not put_bot:
        # put_bot为空，允许所有bot处理消息
        logger.debug(f"修仙插件: put_bot为空，允许bot {bot.self_id} 处理群 {event.group_id} 的消息")
        pass
    else:
        # put_bot不为空，只允许配置的bot处理消息
        if str(bot.self_id) in put_bot:
            if str(event.group_id) in shield_group:
                logger.debug(f"修仙插件: 群 {event.group_id} 在屏蔽列表中，忽略消息")
                raise IgnoredException("为屏蔽群消息,已忽略")
            else:
                logger.debug(f"修仙插件: bot {bot.self_id} 允许处理群 {event.group_id} 的消息")
                pass
        else:
            logger.debug(f"修仙插件: bot {bot.self_id} 不在put_bot列表中，忽略消息")
            raise IgnoredException("非主bot信息,已忽略")


