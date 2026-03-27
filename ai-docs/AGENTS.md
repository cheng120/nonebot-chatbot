# NoneBot通用聊天机器人 - 项目导航

> 生成时间: 2026-01-20

## 项目概述

NoneBot通用聊天机器人是一个基于Python NoneBot2框架的通用聊天机器人平台，一期对接NTQQ平台（通过NapCatQQ或Lagrange.OneBot），实现消息收发、事件处理和插件扩展功能。

**技术栈**：
- 框架：NoneBot2 + FastAPI
- 适配器：OneBot V11
- 数据库：SQLite / MySQL
- ORM：SQLAlchemy 2.0+

---

## 快速导航

| 需求类型 | 入口文档 |
|---------|---------|
| **项目理解** | [业务蓝图](docs/project-blueprint.md) |
| **开发规范** | [技术规范](docs/project-rules.md) |
| **快速开始** | [README.md](../README.md) |

---

## 功能模块索引

### 核心模块

| 模块 | 路径 | 说明 |
|------|------|------|
| **应用入口** | [`bot.py`](../bot.py) | 应用启动、组件初始化 |
| **配置管理** | [`config.py`](../config.py) | 配置模型定义和加载 |
| **OneBot适配器** | [`src/adapters/onebot_v11.py`](../src/adapters/onebot_v11.py) | OneBot V11协议适配 |

### 业务服务

| 服务 | 路径 | 说明 |
|------|------|------|
| **插件管理** | [`src/services/plugin_manager.py`](../src/services/plugin_manager.py) | 插件加载、启用/禁用 |
| **事件处理** | [`src/services/event_handler.py`](../src/services/event_handler.py) | 事件分发和处理 |
| **消息处理** | [`src/services/message_handler.py`](../src/services/message_handler.py) | 消息处理逻辑 |
| **状态管理** | [`src/services/status_manager.py`](../src/services/status_manager.py) | 连接状态监控 |
| **状态API** | [`src/services/status_api.py`](../src/services/status_api.py) | 状态查询API |

### 数据层

| 组件 | 路径 | 说明 |
|------|------|------|
| **数据库连接** | [`src/database/connection.py`](../src/database/connection.py) | 数据库连接管理 |
| **数据模型** | [`src/database/models.py`](../src/database/models.py) | 数据模型定义 |
| **插件配置ORM** | [`src/database/plugin_config.py`](../src/database/plugin_config.py) | 插件配置数据访问 |
| **数据库迁移** | [`src/database/migrations/`](../src/database/migrations/) | 数据库迁移脚本 |

### 工具层

| 工具 | 路径 | 说明 |
|------|------|------|
| **配置加载** | [`src/utils/config_loader.py`](../src/utils/config_loader.py) | YAML和环境变量加载 |
| **日志工具** | [`src/utils/logger.py`](../src/utils/logger.py) | 日志配置和管理 |
| **重试工具** | [`src/utils/retry.py`](../src/utils/retry.py) | 重试机制 |

---

## 开发指南

### 新手入门

1. **了解项目**：阅读 [业务蓝图](docs/project-blueprint.md)
2. **配置环境**：参考 [README.md](../README.md) 快速开始
3. **理解规范**：阅读 [技术规范](docs/project-rules.md)
4. **运行测试**：执行 `pytest tests/`

### 开发任务

| 任务类型 | 入口文件 |
|---------|---------|
| **添加新插件** | [`src/services/plugin_manager.py`](../src/services/plugin_manager.py) |
| **处理新事件** | [`src/services/event_handler.py`](../src/services/event_handler.py) |
| **修改配置** | [`config.py`](../config.py) + [`configs/config.yaml`](../configs/config.yaml) |
| **添加数据库表** | [`src/database/`](../src/database/) |
| **修改日志** | [`src/utils/logger.py`](../src/utils/logger.py) |

### 测试指南

| 测试类型 | 入口 |
|---------|------|
| **配置测试** | [`tests/test_config.py`](../tests/test_config.py) |
| **适配器测试** | [`tests/test_adapters.py`](../tests/test_adapters.py) |
| **数据库测试** | [`tests/test_database.py`](../tests/test_database.py) |
| **服务测试** | [`tests/test_services.py`](../tests/test_services.py) |
| **工具测试** | [`tests/test_utils.py`](../tests/test_utils.py) |

---

## 配置文件

| 文件 | 说明 |
|------|------|
| [`configs/config.yaml`](../configs/config.yaml) | 主配置文件 |
| [`requirements.txt`](../requirements.txt) | Python依赖 |
| [`pytest.ini`](../pytest.ini) | 测试配置 |
| [`Dockerfile`](../Dockerfile) | Docker构建文件 |
| [`docker-compose.yml`](../docker-compose.yml) | Docker编排文件 |

---

## 常见问题

### 1. 如何添加新功能？

根据功能类型，找到对应的模块：

- **新插件**：参考 [`src/services/plugin_manager.py`](../src/services/plugin_manager.py)
- **新事件处理**：修改 [`src/services/event_handler.py`](../src/services/event_handler.py)
- **新配置项**：修改 [`config.py`](../config.py) 和 [`configs/config.yaml`](../configs/config.yaml)

### 2. 如何调试？

使用loguru日志系统，查看 [`src/utils/logger.py`](../src/utils/logger.py) 配置。

### 3. 如何部署？

参考 [README.md](../README.md) 中的部署说明或使用Docker：

```bash
docker build -t nonebot-chatbot:latest .
docker-compose up -d
```

---

## 相关资源

| 资源 | 链接 |
|------|------|
| **NoneBot2官方文档** | https://nonebot.dev/ |
| **OneBot协议文档** | https://github.com/botuniverse/onebot-11 |
| **Pydantic文档** | https://docs.pydantic.dev/ |
| **SQLAlchemy文档** | https://docs.sqlalchemy.org/ |

---

## 项目文档索引

- [业务蓝图](docs/project-blueprint.md) - 项目整体架构和业务流程
- [技术规范](docs/project-rules.md) - 编码规范和技术标准
- [README](../README.md) - 快速开始和基本使用
- [快速开始](../快速开始.md) - 项目快速启动指南

---

> 文档版本: v1.0
> 最后更新: 2026-01-20
