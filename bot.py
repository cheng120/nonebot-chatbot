"""
NoneBot通用聊天机器人 - 入口文件
"""
import os
import asyncio
import nonebot   
from nonebot.log import logger as nonebot_logger
from config import load_config, get_config
from src.utils.logger import setup_logger, get_logger

# 设置 FastAPI 驱动的端口和主机
os.environ.setdefault("HOST", "0.0.0.0")
os.environ.setdefault("PORT", "8880")

# 加载配置
config = load_config()

# 设置日志系统
setup_logger(config.log)
logger = get_logger("bot")

# 记录加载的驱动配置
logger.info(f"加载的驱动配置: {config.driver}")

# 初始化NoneBot
# 配置命令前缀：允许使用 hello 而不需要 /hello
# command_start 包含空字符串，允许无前缀命令
nonebot.init(
	driver=config.driver,
	log_level=config.log.level,
	command_start=["", "/"],  # 支持 hello 和 /hello 两种格式（空字符串优先，允许无前缀）
	command_sep=[" ", "."],  # 命令分隔符
	# 使用 ORM 启动检查，避免 migrate.sync 在迁移链缺失时直接抛 KeyError 导致进程退出
	alembic_startup_check=True,
)

# 对 nonebot-plugin-orm 的 alembic 检查做容错：
# 某些三方插件（如 amrita）迁移链不完整时，Alembic 会在构建 revision 图阶段抛 KeyError，
# 进而导致整个 bot 启动失败。此处捕获缺失 revision 的 KeyError，保证 bot 仍可启动。
try:
	import nonebot_plugin_orm.migrate as _orm_migrate
	_orig_check = _orm_migrate.check
	_orig_sync = _orm_migrate.sync

	def _safe_check(config):
		try:
			_orig_check(config)
		except KeyError as e:
			logger.warning(f"nonebot_plugin_orm：跳过迁移检查（缺失 revision）: {e}")
			return

	def _safe_sync(config, revision=None):
		try:
			_orig_sync(config, revision=revision)
		except KeyError as e:
			logger.warning(f"nonebot_plugin_orm：跳过数据库同步（缺失 revision）: {e}")
			return

	_orm_migrate.check = _safe_check
	_orm_migrate.sync = _safe_sync
except Exception as e:
	logger.warning(f"nonebot_plugin_orm 容错补丁未启用：{e}")

# 获取驱动实例（用于注册适配器）
driver = nonebot.get_driver()

# 注册适配器（TASK-006）
from src.adapters.onebot_v11 import setup_onebot_adapter
setup_onebot_adapter(config)

# 初始化数据库（TASK-002）
from src.database.connection import DatabaseManager
db_manager = DatabaseManager(config.database)

# 初始化消息日志记录器
from src.services.message_logger import init_message_logger
if config.message_log.enabled:
	message_logger = init_message_logger(
		db_manager=db_manager if config.message_log.log_to_database else None,
		log_to_file=config.message_log.log_to_file,
		log_file_path=config.message_log.file_path
	)
	logger.info(f"消息日志已启用 (文件: {config.message_log.log_to_file}, 数据库: {config.message_log.log_to_database})")
else:
	message_logger = None
	logger.info("消息日志已禁用")

# 初始化 WebSocket 事件日志记录器（记录所有 WebSocket 推送的事件）
if config.message_log.enabled:
	from src.services.websocket_event_logger import setup_websocket_event_logging
	setup_websocket_event_logging()
	logger.info("WebSocket 事件日志已启用")

# 导入消息处理器（确保消息处理器被注册）
# 注意：必须导入模块，否则消息处理器不会被注册
import src.services.message_handler
logger.info("消息处理器已导入")

# 初始化插件管理器（TASK-011）
from src.services.plugin_manager import PluginManager
plugin_manager = PluginManager(config.plugins.dir, db_manager, config.plugins)

# 初始化状态管理器（TASK-013）
from src.services.status_manager import StatusManager
status_manager = StatusManager(config.status.check_interval)

# 设置状态API（可选，用于查看状态）
try:
	from src.services.status_api import setup_status_api
	setup_status_api(status_manager)
except Exception as e:
	logger.warning(f"状态API设置失败（不影响运行）: {e}")

# 启动前钩子
@driver.on_startup
async def on_startup():
	"""启动时执行"""
	logger.info("NoneBot机器人启动中...")
	logger.info(f"驱动: {config.driver}")
	logger.info(f"日志级别: {config.log.level}")
	logger.info(f"插件目录: {config.plugins.dir}")
	logger.info(f"使用配置文件管理: {config.plugins.use_config_file}")
	logger.info(f"启用的插件列表: {config.plugins.enabled}")
	logger.info(f"禁用的插件列表: {config.plugins.disabled}")
	
	# 初始化数据库
	try:
		await db_manager.init_db()
		logger.info("数据库初始化完成")
	except Exception as e:
		logger.error(f"数据库初始化失败: {e}")
	
	# 加载插件
	try:
		await plugin_manager.load_all_plugins()
		logger.info("插件加载完成")
	except Exception as e:
		logger.error(f"插件加载失败: {e}")
	
	# 启动自检模式：只做启动流程（尤其是插件加载），然后自动退出
	# 用法: NB_SELFTEST=1 ./venv/bin/python bot.py
	if os.environ.get("NB_SELFTEST") == "1":
		logger.info("NB_SELFTEST=1 启动自检完成，进程即将退出")
		try:
			asyncio.get_running_loop().call_later(0.2, lambda: os._exit(0))
		except Exception:
			os._exit(0)
		return
	
	# 启动状态监控
	if config.status.enabled:
		try:
			asyncio.create_task(status_manager.start_monitoring())
			logger.info("状态监控已启动")
			
			# 显示初始状态（等待更长时间让WebSocket连接建立）
			logger.info("等待适配器建立连接...")
			for i in range(5):  # 最多等待10秒（每次2秒）
				await asyncio.sleep(2)
				# 手动触发一次状态检查
				await status_manager.check_status()
				initial_status = status_manager.get_status()
				if initial_status.get('connected'):
					logger.info(f"适配器连接成功（等待了 {(i+1)*2} 秒）")
					break
			
			# 显示最终状态
			initial_status = status_manager.get_status()
			logger.info("=" * 50)
			logger.info("机器人状态")
			logger.info("=" * 50)
			logger.info(f"运行状态: {'运行中' if initial_status.get('running') else '未运行'}")
			logger.info(f"连接状态: {'已连接' if initial_status.get('connected') else '未连接'}")
			if initial_status.get('connection_method'):
				logger.info(f"连接方式: {initial_status.get('connection_method')}")
			logger.info(f"已加载插件: {initial_status.get('plugins_loaded', 0)}")
			if initial_status.get('last_error'):
				logger.warning(f"错误信息: {initial_status.get('last_error')}")
				if initial_status.get('connected'):
					logger.info("提示: 虽然WebSocket可能未连接，但HTTP API正常，机器人功能可用")
				else:
					logger.warning("提示: 如果WebSocket连接失败，请检查WebSocket配置和NTQQ服务")
			logger.info("=" * 50)
			logger.info("状态API: http://localhost:8880/api/status")
			logger.info("=" * 50)
		except Exception as e:
			logger.error(f"状态监控启动失败: {e}")

# 关闭前钩子
@driver.on_shutdown
async def on_shutdown():
	"""关闭时执行"""
	logger.info("NoneBot机器人正在关闭...")
	
	# 停止状态监控
	if config.status.enabled:
		try:
			await status_manager.stop_monitoring()
		except Exception as e:
			logger.error(f"停止状态监控失败: {e}")
	
	# 关闭数据库连接
	try:
		await db_manager.close()
	except Exception as e:
		logger.error(f"关闭数据库连接失败: {e}")

if __name__ == "__main__":
	logger.info("=" * 50)
	logger.info("NoneBot通用聊天机器人")
	logger.info("=" * 50)
	
	# 启动自检模式：不启动 Web 服务，只执行数据库初始化 + 插件加载
	# 用法: NB_SELFTEST=1 ./venv/bin/python bot.py
	if os.environ.get("NB_SELFTEST") == "1":
		async def _selftest():
			try:
				await db_manager.init_db()
				logger.info("[自检] 数据库初始化完成")
			except Exception as e:
				logger.error(f"[自检] 数据库初始化失败: {e}")
			
			try:
				await plugin_manager.load_all_plugins()
				logger.info("[自检] 插件加载完成")
			except Exception as e:
				logger.error(f"[自检] 插件加载失败: {e}")
			
			try:
				await db_manager.close()
			except Exception:
				pass
		
		asyncio.run(_selftest())
	else:
		nonebot.run()

