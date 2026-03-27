# 快速开始指南

## 安装项目

```bash
# 克隆项目
git clone https://github.com/your-username/nonebot-chatbot
cd nonebot-chatbot

# 安装项目（包含 CLI 工具）
pip install -e .
```

## 使用 CLI 工具添加插件

### 基本用法

```bash
# 创建插件
nb-add-plugin my_plugin

# 创建带描述的插件
nb-add-plugin weather --description "天气查询插件"

# 查看帮助
nb-add-plugin --help
```

### 完整示例

```bash
# 1. 创建插件
nb-add-plugin calculator \
  --description "计算器插件" \
  --usage "/calc <表达式> - 计算数学表达式"

# 2. 编辑插件文件
# 编辑 src/plugins/calculator.py，实现你的功能

# 3. 启用插件（如果需要）
sqlite3 data/bot.db "INSERT INTO plugin_configs (plugin_name, enabled, config_data) VALUES ('calculator', 1, '{}');"

# 4. 重启机器人
python bot.py
```

## 更多资源

- [CLI工具使用指南](docs/CLI工具使用指南.md) - 详细的 CLI 工具文档
- [插件开发指南](docs/插件开发指南.md) - 完整的插件开发文档
- [快速添加插件](docs/快速添加插件.md) - 快速入门

