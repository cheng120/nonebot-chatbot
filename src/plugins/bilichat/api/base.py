import nonebot
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from nonebot.drivers import ReverseDriver
from nonebot.drivers.fastapi import Driver as FastAPIDriver

driver: FastAPIDriver = nonebot.get_driver()  # type: ignore

if not isinstance(driver, ReverseDriver) or not isinstance(driver.server_app, FastAPI):
    raise NotImplementedError("Only FastAPI reverse driver is supported.")

app = driver.server_app

app.separate_input_output_schemas = False

# 插件在 lifespan 启动阶段加载，此时 app 已 started，无法再 add_middleware；跳过 CORS 以允许插件加载
try:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
except RuntimeError as e:
    if "middleware" in str(e).lower() and "started" in str(e).lower():
        from nonebot.log import logger
        logger.warning("BiliChat: 应用已启动，跳过 CORS 中间件注册，WebUI 可能需同源访问")
    else:
        raise
