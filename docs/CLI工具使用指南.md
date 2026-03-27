# CLI 工具使用指南

## 概述

项目提供了一个命令行工具 `nb-add-plugin`，用于快速创建 NoneBot 插件模板。

## 安装

### 方式 1: 从源码安装（开发模式）

```bash
cd nonebot-chatbot
pip install -e .
```

### 方式 2: 从 PyPI 安装

```bash
pip install nonebot-chatbot
```

安装后，`nb-add-plugin` 命令将可用。

## 使用方法

### 基本用法

```bash
# 创建最简单的插件
nb-add-plugin my_plugin

# 创建带描述的插件
nb-add-plugin weather --description "天气查询插件"

# 创建带使用说明的插件
nb-add-plugin admin --description "管理员插件" --usage "/admin - 管理员命令"
```

### 完整参数

```bash
nb-add-plugin <插件名称> [选项]
```

#### 必需参数

- `name`: 插件名称（文件名，不含.py，例如: `my_plugin`）

#### 可选参数

- `-d, --description`: 插件描述（默认: 插件名称）
- `-u, --usage`: 使用说明（默认: 自动生成）
- `--dir`: 插件目录（默认: `src/plugins`）
- `--author`: 作者（默认: `NoneBot Chatbot Team`）
- `--homepage`: 主页链接（默认: 项目主页）
- `-f, --force`: 覆盖已存在的文件

### 示例

#### 示例 1: 创建简单插件

```bash
nb-add-plugin hello
```

生成文件: `src/plugins/hello.py`

#### 示例 2: 创建带描述的插件

```bash
nb-add-plugin weather --description "天气查询插件，支持查询全国主要城市天气"
```

#### 示例 3: 创建带使用说明的插件

```bash
nb-add-plugin calculator \
  --description "计算器插件" \
  --usage "/calc <表达式> - 计算数学表达式\n示例: /calc 1+2*3"
```

#### 示例 4: 创建到自定义目录

```bash
nb-add-plugin custom_plugin --dir ./custom_plugins
```

#### 示例 5: 覆盖已存在的文件

```bash
nb-add-plugin my_plugin --force
```

## 生成的插件模板

工具会生成包含以下内容的插件模板：

1. **插件元数据** (`PluginMetadata`)
   - 插件名称
   - 插件描述
   - 使用说明
   - 类型标识
   - 主页链接
   - 支持的适配器

2. **基础命令处理器**
   - 简单的命令处理示例
   - 日志记录
   - 消息响应

3. **可选功能**
   - @机器人消息处理（注释状态）
   - 插件初始化函数

### 模板示例

生成的插件文件结构：

```python
"""
插件描述
"""
from nonebot import on_command, on_message
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, Message, MessageSegment
from nonebot.params import CommandArg
from nonebot.plugin import PluginMetadata
from nonebot.rule import to_me
from src.utils.logger import get_logger

__plugin_meta__ = PluginMetadata(
    name="插件名称",
    description="插件描述",
    usage="使用说明",
    type="application",
    homepage="https://github.com/your-username/nonebot-chatbot",
    supported_adapters={"~onebot.v11"},
)

logger = get_logger("plugin_name")

# 命令处理器
plugin_name_cmd = on_command("plugin_name", priority=10, block=True)

@plugin_name_cmd.handle()
async def handle_plugin_name(event: MessageEvent):
    """处理命令"""
    logger.info(f"用户 {event.user_id} 使用了 plugin_name 命令")
    await plugin_name_cmd.send("这是 plugin_name 插件的响应！")
```

## 插件命名规范

- ✅ 使用小写字母、数字和下划线
- ✅ 示例: `my_plugin`, `weather_query`, `admin_tools`
- ❌ 不能包含空格、特殊字符
- ❌ 不能以数字开头

## 工作流程

### 1. 创建插件

```bash
nb-add-plugin my_plugin --description "我的插件"
```

### 2. 编辑插件文件

编辑 `src/plugins/my_plugin.py`，实现你的功能。

### 3. 启用插件（可选）

如果使用数据库管理插件状态：

```bash
sqlite3 data/bot.db "INSERT INTO plugin_configs (plugin_name, enabled, config_data) VALUES ('my_plugin', 1, '{}');"
```

### 4. 重启机器人

```bash
python bot.py
```

## 常见问题

### Q1: 命令未找到？

**A:** 确保已安装项目：
```bash
pip install -e .
```

### Q2: 如何修改插件目录？

**A:** 使用 `--dir` 参数：
```bash
nb-add-plugin my_plugin --dir ./custom_plugins
```

### Q3: 如何覆盖已存在的插件？

**A:** 使用 `--force` 参数：
```bash
nb-add-plugin my_plugin --force
```

### Q4: 生成的模板可以修改吗？

**A:** 可以，生成的模板只是起点，你可以根据需要修改。

### Q5: 如何查看帮助？

**A:** 使用 `--help` 参数：
```bash
nb-add-plugin --help
```

## 高级用法

### 批量创建插件

```bash
# 创建多个插件
for plugin in weather admin calculator; do
    nb-add-plugin $plugin --description "${plugin} 插件"
done
```

### 使用脚本自动化

创建 `create_plugins.sh`:

```bash
#!/bin/bash
nb-add-plugin weather --description "天气查询插件"
nb-add-plugin admin --description "管理员插件"
nb-add-plugin calculator --description "计算器插件"
```

## 与手动创建对比

### 手动创建

1. 创建文件
2. 编写代码
3. 添加元数据
4. 配置日志
5. 实现命令处理器

**时间**: 5-10 分钟

### 使用 CLI 工具

```bash
nb-add-plugin my_plugin --description "我的插件"
```

**时间**: 10 秒

## 总结

`nb-add-plugin` 工具可以：

- ✅ 快速创建插件模板
- ✅ 自动生成 PluginMetadata
- ✅ 包含基础命令处理器
- ✅ 符合 NoneBot 规范
- ✅ 支持自定义参数

使用 CLI 工具可以大大提高插件开发效率！

