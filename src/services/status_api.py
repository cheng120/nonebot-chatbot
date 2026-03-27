"""
状态API服务
提供HTTP API接口查看机器人状态
"""
from nonebot import get_driver
from src.services.status_manager import StatusManager
from src.utils.logger import get_logger
from typing import Optional

logger = get_logger("status_api")

# 全局状态管理器引用（在bot.py中设置）
_status_manager: Optional[StatusManager] = None


def setup_status_api(status_manager: StatusManager):
	"""
	设置状态API路由
	
	Args:
		status_manager: 状态管理器实例
	"""
	global _status_manager
	_status_manager = status_manager
	
	try:
		driver = get_driver()
		
		# 尝试获取FastAPI应用
		# NoneBot2的FastAPI驱动会提供server_app属性
		try:
			app = driver.server_app
			if app is None:
				logger.warning("无法获取FastAPI应用实例，状态API未注册")
				return
		except AttributeError:
			logger.warning("当前驱动不支持server_app，状态API未注册")
			return
		
		# 导入FastAPI相关模块
		try:
			from fastapi import APIRouter
		except ImportError:
			logger.warning("FastAPI未安装，状态API未注册")
			return
		
		# 创建路由
		router = APIRouter(prefix="/api/status", tags=["状态"])
		
		@router.get("/")
		async def get_status():
			"""获取机器人状态"""
			if _status_manager:
				return _status_manager.get_status()
			return {"error": "状态管理器未初始化"}
		
		@router.get("/health")
		async def health_check():
			"""健康检查"""
			if _status_manager:
				status = _status_manager.get_status()
				return {
					"status": "healthy" if status.get("connected") else "unhealthy",
					"connected": status.get("connected", False),
					"plugins_loaded": status.get("plugins_loaded", 0)
				}
			return {"status": "unknown", "error": "状态管理器未初始化"}
		
		# 注册路由
		app.include_router(router)
		logger.info("状态API已注册: /api/status")
		
	except Exception as e:
		logger.warning(f"注册状态API失败（不影响运行）: {e}")

