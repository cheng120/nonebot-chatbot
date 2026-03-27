@echo off
REM Windows测试执行脚本

echo ==========================================
echo NoneBot通用聊天机器人 - 测试执行
echo ==========================================

REM 检查Python环境
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python 未安装
    exit /b 1
)

REM 检查pytest
python -m pytest --version >nul 2>&1
if errorlevel 1 (
    echo ⚠️  pytest 未安装，正在安装...
    pip install pytest pytest-asyncio pytest-cov
)

REM 设置测试环境变量
set PYTHONPATH=%PYTHONPATH%;%CD%

REM 运行测试
echo.
echo 运行单元测试...
python -m pytest tests/ -v --tb=short

echo.
echo 运行测试并生成覆盖率报告...
python -m pytest tests/ --cov=src --cov=config --cov-report=html --cov-report=term

echo.
echo ==========================================
echo 测试完成！
echo 覆盖率报告: htmlcov\index.html
echo ==========================================
pause

