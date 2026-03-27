@echo off
REM NoneBot通用聊天机器人启动脚本（Windows）

echo ========================================
echo   NoneBot通用聊天机器人
echo ========================================
echo.

cd /d "%~dp0"

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到 Python
    pause
    exit /b 1
)

echo Python版本:
python --version
echo.

REM 检查虚拟环境
if exist "venv\Scripts\activate.bat" (
    echo 激活虚拟环境...
    call venv\Scripts\activate.bat
) else (
    echo 警告: 未找到虚拟环境，使用系统Python
    echo 建议: 创建虚拟环境以隔离依赖
    echo.
)

REM 检查依赖
echo 检查依赖...
python -c "import nonebot" >nul 2>&1
if errorlevel 1 (
    echo 错误: NoneBot未安装
    echo 正在安装依赖...
    pip install -r requirements.txt
)

REM 检查配置文件
if not exist "configs\config.yaml" (
    echo 警告: 配置文件不存在，使用默认配置
    if not exist "configs" mkdir configs
)

REM 创建必要的目录
echo 创建必要的目录...
if not exist "logs" mkdir logs
if not exist "data" mkdir data
if not exist "src\plugins" mkdir src\plugins

REM 启动机器人
echo.
echo 启动NoneBot机器人...
echo 提示: 按 Ctrl+C 停止机器人
echo.

python bot.py

pause

