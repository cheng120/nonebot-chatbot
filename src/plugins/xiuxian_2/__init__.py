"""
修仙插件 - 项目内运行版本
"""
from pathlib import Path
from nonebot import require

# 声明依赖插件（必须在导入子模块之前）
require('nonebot_plugin_apscheduler')

# 导入子模块，触发 xiuxian/__init__.py 的执行
# 注意：插件管理器会自动发现并加载整个插件目录
# xiuxian/__init__.py 会处理子模块的加载
from . import xiuxian