#!/bin/bash
# NoneBot 市场发布脚本

set -e

echo "=========================================="
echo "NoneBot 市场发布准备"
echo "=========================================="

# 检查是否在项目根目录
if [ ! -f "pyproject.toml" ]; then
    echo "错误: 请在项目根目录运行此脚本"
    exit 1
fi

# 1. 检查必需文件
echo ""
echo "1. 检查必需文件..."
files=("pyproject.toml" "README.md" "LICENSE")
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✓ $file 存在"
    else
        echo "  ✗ $file 不存在"
        exit 1
    fi
done

# 2. 运行代码检查
echo ""
echo "2. 运行代码检查..."
if command -v ruff &> /dev/null; then
    ruff check . || echo "  警告: ruff 检查发现问题，请修复"
else
    echo "  跳过: ruff 未安装"
fi

# 3. 运行测试
echo ""
echo "3. 运行测试..."
if command -v pytest &> /dev/null; then
    pytest tests/ -v || echo "  警告: 测试失败，请修复"
else
    echo "  跳过: pytest 未安装"
fi

# 4. 清理旧的构建文件
echo ""
echo "4. 清理旧的构建文件..."
rm -rf dist/ build/ *.egg-info
echo "  ✓ 清理完成"

# 5. 构建包
echo ""
echo "5. 构建包..."
if command -v python &> /dev/null; then
    python -m pip install --upgrade build
    python -m build
    echo "  ✓ 构建完成"
else
    echo "  错误: Python 未找到"
    exit 1
fi

# 6. 检查构建产物
echo ""
echo "6. 检查构建产物..."
if [ -d "dist" ]; then
    ls -lh dist/
    echo "  ✓ 构建产物已生成"
else
    echo "  ✗ 构建失败"
    exit 1
fi

# 7. 显示发布命令
echo ""
echo "=========================================="
echo "发布准备完成！"
echo "=========================================="
echo ""
echo "下一步操作："
echo ""
echo "1. 测试发布到 TestPyPI："
echo "   pip install twine"
echo "   twine upload --repository testpypi dist/*"
echo ""
echo "2. 正式发布到 PyPI："
echo "   twine upload dist/*"
echo ""
echo "3. 提交到 NoneBot 市场："
echo "   访问 https://github.com/nonebot/nonebot2/tree/master/packages"
echo "   按照指南提交 PR"
echo ""
echo "=========================================="

