# 如何给 NoneBot 聊天机器人增加插件

## 📋 目录

- [快速开始](#快速开始)
- [详细步骤](#详细步骤)
- [插件示例](#插件示例)
- [常见问题](#常见问题)

## 🚀 快速开始

### 三步添加插件

1. **创建插件文件** → `src/plugins/my_plugin.py`
2. **启用插件** → 在数据库中启用
3. **重启机器人** → 插件自动加载

## 📝 详细步骤

### 步骤 1: 创建插件文件

在 `src/plugins/` 目录下创建新的 Python 文件：

```python
"""
我的插件
"""
from nonebot import on_command
from nonebot.adapters.onebot.v11 import MessageEvent
from src.utils.logger import get_logger

logger = get_logger("my_plugin")

# 创建命令处理器
my_cmd = on_command("mycmd", priority=10, block=True)

@my_cmd.handle()
async def handle_my_cmd(event: MessageEvent):
    """处理命令"""
    logger.info(f"用户 {event.user_id} 使用了 mycmd 命令")
    await my_cmd.send("这是我的插件响应！")
```

**文件命名规则：**
- ✅ 使用小写字母和下划线：`my_plugin.py`
- ✅ 不能以 `_` 开头
- ✅ 不能是 `__init__.py`

### 步骤 2: 启用插件

插件创建后需要在数据库中启用。有两种方式：

#### 方式 A: 使用 SQLite 命令行（推荐）

```bash
# 进入项目目录
cd nonebot-chatbot

# 打开数据库
sqlite3 data/bot.db

# 插入插件配置（启用插件）
INSERT INTO plugin_configs (plugin_name, enabled, config_data) 
VALUES ('my_plugin', 1, '{}');

# 查看是否成功
SELECT * FROM plugin_configs WHERE plugin_name = 'my_plugin';

# 退出
.quit
```

#### 方式 B: 使用 Python 脚本

创建 `enable_plugin.py`：

```python
import asyncio
from src.database.connection import DatabaseManager
from src.database.plugin_config import PluginConfig
from config import load_config

async def main():
    config = load_config()
    db_manager = DatabaseManager(config.database)
    await db_manager.init_db()
    
    async with db_manager.get_session() as session:
        await PluginConfig.create_or_update(
            session, 
            "my_plugin",  # 插件名称（文件名，不含.py）
            enabled=True
        )
        print("✅ 插件已启用")

if __name__ == "__main__":
    asyncio.run(main())
```

运行：
```bash
python enable_plugin.py
```

### 步骤 3: 重启机器人

```bash
python bot.py
```

启动日志中会显示：
```
插件 my_plugin 已加载并启用
```

## 📚 插件示例

### 示例 1: 简单命令插件

```python
"""
简单命令插件
"""
from nonebot import on_command
from nonebot.adapters.onebot.v11 import MessageEvent
from src.utils.logger import get_logger

logger = get_logger("simple_cmd")

cmd = on_command("hello", priority=10, block=True)

@cmd.handle()
async def handle_cmd(event: MessageEvent):
    await cmd.send("Hello, World!")
```

### 示例 2: 带参数的命令

```python
"""
带参数的命令插件
"""
from nonebot import on_command
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import MessageEvent, Message
from src.utils.logger import get_logger

logger = get_logger("param_cmd")

echo = on_command("echo", priority=10, block=True)

@echo.handle()
async def handle_echo(event: MessageEvent, args: Message = CommandArg()):
    arg_str = str(args).strip()
    if arg_str:
        await echo.send(f"你说: {arg_str}")
    else:
        await echo.send("用法: /echo <内容>")
```

### 示例 3: @机器人触发

```python
"""
@机器人触发插件
"""
from nonebot import on_message
from nonebot.rule import to_me
from nonebot.adapters.onebot.v11 import MessageEvent
from src.utils.logger import get_logger

logger = get_logger("at_me")

handler = on_message(priority=10, block=True, rule=to_me())

@handler.handle()
async def handle_at_me(event: MessageEvent):
    await handler.send("你@我了！")
```

### 完整示例

查看 `src/plugins/example_plugin.py`，这是一个功能完整的插件示例，包含：
- ✅ 多个命令处理器
- ✅ 消息处理器
- ✅ 参数解析
- ✅ 图片发送
- ✅ 错误处理
- ✅ 日志记录

## 🔍 检查插件状态

### 查看日志

```bash
# 实时查看日志
tail -f logs/bot.log

# 搜索插件相关日志
grep "my_plugin" logs/bot.log
```

### 查看数据库

```bash
sqlite3 data/bot.db

# 查看所有插件
SELECT plugin_name, enabled FROM plugin_configs;

# 查看插件状态
SELECT * FROM plugin_status WHERE plugin_name = 'my_plugin';
```

### 测试插件

启动机器人后，在 QQ 中测试：

```
/hello        # 如果插件有 hello 命令
/mycmd        # 如果插件有 mycmd 命令
@机器人 帮助   # 如果插件支持@触发
```

## ❓ 常见问题

### Q1: 插件创建后没有生效？

**检查清单：**
1. ✅ 文件是否在 `src/plugins/` 目录下
2. ✅ 文件名是否符合规范（不能以 `_` 开头）
3. ✅ 插件是否在数据库中启用
4. ✅ 查看日志是否有错误信息

**查看日志：**
```bash
grep -i "error\|fail\|my_plugin" logs/bot.log
```

### Q2: 如何调试插件？

1. **查看日志**
   ```bash
   tail -f logs/bot.log
   ```

2. **添加调试日志**
   ```python
   logger.debug("调试信息")
   logger.info("信息日志")
   logger.error("错误日志")
   ```

3. **检查命令优先级**
   ```python
   # priority 值越小优先级越高
   cmd = on_command("cmd", priority=10, block=True)
   ```

### Q3: 插件如何访问数据库？

```python
from src.database.connection import DatabaseManager

# 需要从 bot.py 中获取 db_manager 实例
# 或者通过依赖注入获取

async def use_database():
    # 假设有 db_manager 实例
    async with db_manager.get_session() as session:
        # 使用 session 进行数据库操作
        pass
```

### Q4: 插件如何读取配置？

```python
from src.services.plugin_manager import PluginManager

# 通过 PluginManager 读取配置
config = await plugin_manager.get_plugin_config("my_plugin")
if config:
    config_data = config.get("config_data", {})
```

### Q5: 如何实现插件热重载？

目前不支持热重载，需要重启机器人。重启命令：
```bash
# 停止机器人（Ctrl+C）
# 然后重新启动
python bot.py
```

## 📖 更多资源

- 📘 [完整插件开发指南](./docs/插件开发指南.md) - 详细的开发文档
- 🚀 [快速添加插件指南](./docs/快速添加插件.md) - 快速入门
- 💡 [示例插件](./src/plugins/example_plugin.py) - 完整功能示例
- 📝 [现有插件示例](./src/plugins/hello.py) - 简单示例

## 🎯 总结

添加插件的三个步骤：

1. **创建** → 在 `src/plugins/` 创建 `.py` 文件
2. **启用** → 在数据库中启用插件
3. **重启** → 重启机器人，插件自动加载

**插件命名：**
- 文件名：`my_plugin.py`
- 插件名：`my_plugin`（用于数据库配置）

**快速测试：**
```bash
# 1. 创建插件文件
# 2. 启用插件
sqlite3 data/bot.db "INSERT INTO plugin_configs (plugin_name, enabled, config_data) VALUES ('my_plugin', 1, '{}');"

# 3. 重启机器人
python bot.py
```

如有问题，请查看日志或参考完整文档！

