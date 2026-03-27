#!/bin/bash
# NoneBot通用聊天机器人启动脚本

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  NoneBot通用聊天机器人${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}错误: 未找到 python3${NC}"
    exit 1
fi

echo -e "${YELLOW}Python版本:${NC} $(python3 --version)"
echo ""

# 检查虚拟环境
if [ -d "venv" ]; then
    echo -e "${YELLOW}激活虚拟环境...${NC}"
    source venv/bin/activate
else
    echo -e "${YELLOW}警告: 未找到虚拟环境，使用系统Python${NC}"
    echo -e "${YELLOW}建议: 创建虚拟环境以隔离依赖${NC}"
    echo ""
fi

# 检查依赖
echo -e "${YELLOW}检查依赖...${NC}"
if ! python3 -c "import nonebot" 2>/dev/null; then
    echo -e "${RED}错误: NoneBot未安装${NC}"
    echo -e "${YELLOW}正在安装依赖...${NC}"
    pip3 install -r requirements.txt
fi

# 检查配置文件
if [ ! -f "configs/config.yaml" ]; then
    echo -e "${YELLOW}警告: 配置文件不存在，使用默认配置${NC}"
    mkdir -p configs
fi

# 创建必要的目录
echo -e "${YELLOW}创建必要的目录...${NC}"
mkdir -p logs
mkdir -p data
mkdir -p src/plugins

# 启动机器人
echo ""
echo -e "${GREEN}启动NoneBot机器人...${NC}"
echo -e "${YELLOW}提示: 按 Ctrl+C 停止机器人${NC}"
echo ""

python3 bot.py

