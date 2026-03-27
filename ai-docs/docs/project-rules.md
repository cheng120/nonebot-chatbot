# NoneBot通用聊天机器人 - 项目技术规范

> 生成时间: 2026-01-20

## 1. 项目信息

| 项目名称 | NoneBot通用聊天机器人 |
|---------|---------------------|
| 项目类型 | Python Web应用（聊天机器人框架） |
| 语言 | Python 3.9+ |
| 框架 | NoneBot2 + FastAPI |
| 构建工具 | pip / poetry |
| 包管理 | pip + requirements.txt |
| 测试框架 | pytest + pytest-asyncio |

---

## 2. 项目结构

### 2.1 分层架构

```
┌─────────────────────────────────────────┐
│           入口层 (Entry)                │
│         bot.py - 应用入口               │
├─────────────────────────────────────────┤
│          业务服务层 (Services)          │
│  插件管理、事件处理、消息处理、状态管理 │
├─────────────────────────────────────────┤
│         数据访问层 (Database)            │
│      数据库连接、模型、配置持久化       │
├─────────────────────────────────────────┤
│         适配器层 (Adapters)              │
│         OneBot V11适配器                │
├─────────────────────────────────────────┤
│          工具层 (Utils)                  │
│    配置加载、日志、重试、工具函数       │
└─────────────────────────────────────────┘
```

### 2.2 目录结构

```
nonebot-chatbot/
├── bot.py                 # 应用入口
├── config.py              # 配置模型定义
├── requirements.txt       # Python依赖
├── pytest.ini            # 测试配置
├── Dockerfile             # Docker构建文件
├── docker-compose.yml     # Docker编排文件
│
├── configs/               # 配置文件目录
│   └── config.yaml        # 主配置文件
│
├── src/                   # 源代码目录
│   ├── adapters/          # 适配器层
│   │   └── onebot_v11.py  # OneBot V11适配器
│   ├── services/          # 业务服务层
│   │   ├── event_handler.py      # 事件处理
│   │   ├── message_handler.py    # 消息处理
│   │   ├── plugin_manager.py     # 插件管理
│   │   ├── status_manager.py     # 状态管理
│   │   └── status_api.py         # 状态API
│   ├── database/          # 数据访问层
│   │   ├── connection.py         # 数据库连接
│   │   ├── models.py             # 数据模型
│   │   ├── plugin_config.py      # 插件配置ORM
│   │   └── migrations/           # 数据库迁移
│   │       └── 001_init_tables.sql
│   └── utils/             # 工具层
│       ├── config_loader.py      # 配置加载
│       ├── logger.py             # 日志工具
│       └── retry.py              # 重试工具
│
├── tests/                 # 测试目录
│   ├── conftest.py        # pytest配置
│   ├── test_config.py     # 配置测试
│   ├── test_adapters.py   # 适配器测试
│   ├── test_database.py   # 数据库测试
│   ├── test_services.py   # 服务测试
│   └── test_utils.py      # 工具测试
│
├── logs/                  # 日志目录
├── data/                  # 数据目录
└── ai-docs/              # AI文档目录
    └── docs/             # 项目文档
        ├── project-blueprint.md
        └── project-rules.md
```

---

## 3. 编码规范

### 3.1 命名规范

| 类型 | 命名规则 | 示例 |
|------|---------|------|
| 模块/包 | 小写字母+下划线 | `plugin_manager.py` |
| 类名 | 大驼峰 | `PluginManager` |
| 函数/方法 | 小写字母+下划线 | `load_plugin()` |
| 常量 | 大写字母+下划线 | `MAX_RETRY_TIMES` |
| 私有成员 | 前缀下划线 | `_private_method()` |
| 配置类 | 功能名+Config | `LogConfig` |

### 3.2 代码风格

- 遵循 PEP 8 编码规范
- 使用类型提示（Type Hints）
- 最大行长度：120字符
- 导入顺序：标准库 -> 第三方库 -> 本地模块
- 使用空行分隔函数和类（2行空行分隔类，1行空行分隔方法）

**示例**：

```python
from typing import Optional, List
from pydantic import BaseModel
from loguru import logger


class PluginManager(BaseModel):
    """插件管理器"""

    def __init__(self, plugin_dir: str, db_manager: DatabaseManager):
        """初始化插件管理器"""
        self.plugin_dir = plugin_dir
        self.db_manager = db_manager
        self.plugins: Dict[str, Plugin] = {}

    async def load_plugin(self, name: str) -> bool:
        """
        加载插件

        Args:
            name: 插件名称

        Returns:
            是否加载成功
        """
        try:
            # 实现逻辑
            pass
        except Exception as e:
            logger.error(f"加载插件失败: {e}")
            return False
```

### 3.3 注释规范

- 文件级注释：使用三引号字符串描述模块用途
- 类级注释：使用类文档字符串
- 方法级注释：使用Google风格的文档字符串
- 关键逻辑：添加行内注释

**示例**：

```python
"""
插件管理模块

负责插件的加载、启用、禁用和配置管理
"""

class PluginManager:
    """
    插件管理器

    负责扫描插件目录、加载插件、管理插件状态
    """

    def load_plugin(self, name: str) -> bool:
        """
        加载指定插件

        Args:
            name: 插件名称

        Returns:
            bool: 加载成功返回True，否则返回False

        Raises:
            PluginLoadError: 当插件加载失败时抛出
        """
        # 检查插件是否存在
        if not self._plugin_exists(name):
            return False

        # 加载插件
        try:
            plugin = self._import_plugin(name)
        except Exception as e:
            logger.error(f"导入插件失败: {e}")
            return False

        return True
```

### 3.4 错误处理

- 使用try-except捕获预期异常
- 使用loguru记录错误日志
- 避免使用裸except
- 自定义异常继承Exception

**示例**：

```python
class PluginLoadError(Exception):
    """插件加载错误"""

async def load_plugin(self, name: str) -> bool:
    try:
        plugin = self._import_plugin(name)
    except ImportError as e:
        logger.error(f"插件导入失败: {e}")
        return False
    except Exception as e:
        logger.exception(f"加载插件时发生未知错误: {e}")
        raise PluginLoadError(f"无法加载插件 {name}") from e
```

### 3.5 日志规范

- 使用loguru记录日志
- 使用不同的日志级别（DEBUG、INFO、WARNING、ERROR、CRITICAL）
- 日志内容包括：时间、级别、模块、消息

**示例**：

```python
from loguru import logger

# DEBUG: 详细调试信息
logger.debug(f"正在加载插件: {plugin_name}")

# INFO: 一般信息
logger.info("插件加载完成")

# WARNING: 警告信息
logger.warning(f"插件 {plugin_name} 已加载，但未启用")

# ERROR: 错误信息
logger.error(f"插件加载失败: {error_message}")

# CRITICAL: 严重错误
logger.critical("数据库连接失败，无法继续运行")
```

---

## 4. 接口规范

### 4.1 OneBot V11协议

本项目使用OneBot V11协议与NTQQ通信。

#### WebSocket接口

- **连接地址**: `ws://127.0.0.1:3001`
- **认证方式**: Access Token（可选）
- **事件类型**: 消息事件、通知事件、请求事件、元事件

#### HTTP API接口

- **API根路径**: `http://127.0.0.1:3000`
- **请求方式**: GET / POST
- **认证方式**: Access Token（可选）

**主要API**：

| API | 方法 | 说明 |
|-----|------|------|
| `/send_msg` | POST | 发送消息 |
| `/get_msg` | GET | 获取消息 |
| `/get_group_info` | GET | 获取群信息 |
| `/get_friend_list` | GET | 获取好友列表 |

### 4.2 状态API接口

#### GET /api/status

获取机器人运行状态

**响应示例**：

```json
{
  "running": true,
  "connected": true,
  "connection_method": "websocket",
  "plugins_loaded": 5,
  "last_check": "2026-01-20T10:30:00Z",
  "last_error": null
}
```

**字段说明**：

| 字段 | 类型 | 说明 |
|------|------|------|
| running | bool | 是否运行中 |
| connected | bool | 是否已连接 |
| connection_method | str | 连接方式（websocket/http） |
| plugins_loaded | int | 已加载插件数 |
| last_check | str | 最后检查时间（ISO 8601） |
| last_error | str/null | 最后错误信息 |

---

## 5. 数据库规范

### 5.1 表设计规范

- 表名：小写字母+下划线
- 主键：`id`（自增）
- 时间字段：`created_at`（创建时间）、`updated_at`（更新时间）
- 软删除字段：`deleted_at`（可选）

**示例**：

```sql
CREATE TABLE plugin_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plugin_name TEXT NOT NULL UNIQUE,
    config_json TEXT NOT NULL,
    enabled INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 5.2 索引规范

- 为频繁查询的字段创建索引
- 唯一约束字段自动创建索引
- 复合索引按查询频率排列字段顺序

**示例**：

```sql
CREATE INDEX idx_plugin_name ON plugin_config(plugin_name);
CREATE INDEX idx_enabled ON plugin_config(enabled);
```

### 5.3 SQL规范

- 使用参数化查询防止SQL注入
- 事务操作要显式提交或回滚
- 避免使用 `SELECT *`

**示例**：

```python
# 使用参数化查询
async def get_plugin_config(self, plugin_name: str) -> Optional[Dict]:
    query = "SELECT * FROM plugin_config WHERE plugin_name = ?"
    async with self.db.execute(query, (plugin_name,)) as cursor:
        row = await cursor.fetchone()
        return dict(row) if row else None
```

### 5.4 事务规范

- 多个SQL操作使用事务
- 异常时回滚
- 成功时提交

**示例**：

```python
async def update_plugin_config(self, plugin_name: str, config: Dict):
    async with self.db.begin() as conn:
        try:
            await conn.execute(
                "UPDATE plugin_config SET config_json = ?, updated_at = CURRENT_TIMESTAMP "
                "WHERE plugin_name = ?",
                (json.dumps(config), plugin_name)
            )
            await conn.commit()
        except Exception as e:
            await conn.rollback()
            raise
```

---

## 6. 中间件规范

### 6.1 配置管理

使用Pydantic进行配置验证和类型检查。

**配置加载优先级**：

```
环境变量 > config.yaml > 默认值
```

**示例**：

```python
from pydantic import BaseModel, Field, field_validator

class LogConfig(BaseModel):
    """日志配置"""
    level: str = "INFO"
    console: bool = True
    file: bool = True
    file_path: str = "./logs/bot.log"

    @field_validator("level")
    @classmethod
    def validate_level(cls, v: str) -> str:
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"日志级别必须是: {', '.join(valid_levels)}")
        return v.upper()
```

### 6.2 日志管理

使用loguru进行日志管理。

**配置**：

- 日志级别：可配置
- 日志输出：控制台 + 文件
- 日志轮转：按时间或大小
- 日志保留：按时间或数量

**示例**：

```python
from loguru import logger

def setup_logger(config: LogConfig):
    """配置日志系统"""
    # 控制台输出
    if config.console:
        logger.remove()
        logger.add(
            sys.stdout,
            level=config.level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
        )

    # 文件输出
    if config.file:
        logger.add(
            config.file_path,
            level=config.level,
            rotation=config.file_rotation,
            retention=config.file_retention,
            encoding="utf-8"
        )
```

### 6.3 重试机制

使用自定义重试装饰器。

**配置**：

- 最大重试次数：可配置
- 重试间隔：可配置
- 重试异常：可指定

**示例**：

```python
from functools import wraps
import asyncio

def retry(max_attempts: int = 3, interval: float = 1.0):
    """重试装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(interval)
            raise last_exception
        return wrapper
    return decorator
```

---

## 7. 安全规范

### 7.1 敏感信息管理

- Access Token等敏感信息使用环境变量
- 配置文件中不要包含敏感信息
- 日志中不要记录敏感信息

**示例**：

```python
# .env文件（不提交到版本控制）
ONEBOT_ACCESS_TOKEN=your_token_here
DB_PASSWORD=your_password_here

# config.yaml（提交到版本控制）
adapters:
  - name: OneBot V11
    access_token: ""  # 从环境变量读取
```

### 7.2 输入验证

- 使用Pydantic验证输入
- 对用户输入进行转义
- 防止SQL注入（使用参数化查询）

### 7.3 依赖管理

- 定期更新依赖到最新稳定版本
- 使用requirements.txt固定版本
- 定期检查安全漏洞

---

## 8. 测试规范

### 8.1 单元测试

- 使用pytest框架
- 测试文件命名：`test_*.py`
- 测试函数命名：`test_*`

**示例**：

```python
import pytest
from src.services.plugin_manager import PluginManager

@pytest.fixture
def plugin_manager(db_manager):
    """创建插件管理器fixture"""
    return PluginManager("./tests/fixtures/plugins", db_manager)

@pytest.mark.asyncio
async def test_load_plugin(plugin_manager):
    """测试加载插件"""
    result = await plugin_manager.load_plugin("test_plugin")
    assert result is True
    assert "test_plugin" in plugin_manager.plugins
```

### 8.2 集成测试

- 测试多个模块的交互
- 使用pytest-asyncio支持异步测试
- 使用mock隔离外部依赖

**示例**：

```python
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_bot_startup():
    """测试机器人启动流程"""
    with patch('src.database.connection.DatabaseManager.init_db') as mock_init:
        mock_init.return_value = None
        # 测试逻辑
        pass
```

### 8.3 测试覆盖率

- 目标覆盖率：80%以上
- 使用pytest-cov生成覆盖率报告
- 关键业务逻辑必须测试

---

## 9. 构建和部署

### 9.1 依赖安装

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install --upgrade pip
pip install -r requirements.txt
```

### 9.2 运行项目

```bash
# 本地运行
python bot.py

# 或使用pytest运行测试
pytest tests/
```

### 9.3 Docker构建

```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "bot.py"]
```

```bash
# 构建镜像
docker build -t nonebot-chatbot:latest .

# 运行容器
docker run -d -p 8080:8080 --name bot nonebot-chatbot:latest
```

### 9.4 Docker Compose

```yaml
version: '3.8'
services:
  bot:
    build: .
    ports:
      - "8080:8080"
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
    restart: unless-stopped
```

---

## 10. Git工作流

### 10.1 分支管理

- `main`: 主分支，稳定版本
- `develop`: 开发分支
- `feature/*`: 功能分支
- `bugfix/*`: 修复分支

### 10.2 提交规范

使用约定式提交（Conventional Commits）：

```
<type>(<scope>): <subject>

<body>

<footer>
```

**类型**：

- `feat`: 新功能
- `fix`: 修复bug
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建/工具相关

**示例**：

```
feat(plugin): 添加插件热加载功能

- 实现插件动态加载
- 支持配置热更新
- 添加插件状态管理

Closes #123
```

---

## 11. 开发工具

### 11.1 推荐IDE

- PyCharm / VS Code
- 安装Python插件
- 配置代码格式化（black）

### 11.2 代码质量工具

- **black**: 代码格式化
- **flake8**: 代码检查
- **mypy**: 类型检查
- **pytest**: 单元测试

### 11.3 调试工具

- loguru: 日志记录
- pytest-dbg: 调试测试
- pdb: Python调试器

---

## 12. 版本控制

### 12.1 版本号格式

使用语义化版本（Semantic Versioning）：`MAJOR.MINOR.PATCH`

- **MAJOR**: 不兼容的API修改
- **MINOR**: 向下兼容的功能新增
- **PATCH**: 向下兼容的bug修复

### 12.2 变更日志

维护CHANGELOG.md，记录每次发布的变更。

---

> 文档版本: v1.0
> 最后更新: 2026-01-20
