#!/bin/bash
# 测试执行脚本

set -e

echo "=========================================="
echo "NoneBot通用聊天机器人 - 测试执行"
echo "=========================================="

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装"
    exit 1
fi

# 检查pytest
if ! python3 -m pytest --version &> /dev/null; then
    echo "⚠️  pytest 未安装，正在安装..."
    pip install pytest pytest-asyncio pytest-cov
fi

# 设置测试环境变量
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# 运行测试
echo ""
echo "运行单元测试..."
python3 -m pytest tests/ -v --tb=short

echo ""
echo "运行测试并生成覆盖率报告..."
python3 -m pytest tests/ --cov=src --cov=config --cov-report=html --cov-report=term

echo ""
echo "=========================================="
echo "测试完成！"
echo "覆盖率报告: htmlcov/index.html"
echo "=========================================="

