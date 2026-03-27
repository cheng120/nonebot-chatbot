# NoneBot通用聊天机器人

基于NoneBot2框架构建的通用聊天机器人，一期对接NTQQ平台，实现消息收发、事件处理和插件扩展功能。

## 项目简介

本项目使用NoneBot2框架构建，支持OneBot V11协议，可以对接NTQQ平台（通过NapCatQQ或Lagrange.OneBot），实现完整的消息收发、事件处理和插件扩展功能。

## 快速开始

### 环境要求

- Python 3.9+
- pip 或 conda

### 安装步骤

#### 方式1: 使用自动化脚本（推荐）

**Linux/Mac:**
```bash
cd nonebot-chatbot
./setup_and_test.sh
```

**Windows:**
```cmd
cd nonebot-chatbot
setup_and_test.bat
```

脚本会自动创建虚拟环境、安装依赖并运行测试。

#### 方式2: 手动安装

1. **克隆项目**（如果使用Git）

```bash
git clone <repository-url>
cd nonebot-chatbot
```

2. **创建虚拟环境**

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

3. **安装依赖**

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

4. **配置环境变量**

```bash
cp .env.example .env
# 编辑 .env 文件，配置NTQQ连接信息
```

5. **配置NTQQ**

确保NTQQ（NapCatQQ或Lagrange.OneBot）已启动并配置：
- HTTP API地址：`http://localhost:5700`
- WebSocket地址：`ws://localhost:6700`

6. **运行机器人**

```bash
python bot.py
```

## 配置说明

### 配置文件

配置文件位于 `configs/config.yaml`，包含以下配置项：

- **NoneBot配置**：驱动、日志级别等
- **OneBot适配器配置**：API地址、WebSocket地址、Access Token等
- **数据库配置**：数据库类型（SQLite/MySQL）、连接信息等
- **插件配置**：插件目录、自动重载等
- **重试配置**：重试次数、间隔等
- **状态监控配置**：检查间隔等

### 环境变量

环境变量配置在 `.env` 文件中，优先级高于配置文件。详见 `.env.example`。

## 命令使用

机器人提供了丰富的命令功能，详细使用说明请参考：

📖 **[命令使用文档](docs/命令使用文档.md)**

### 快速开始

- **打招呼**: `hello` 或 `/hello`
- **查看帮助**: @机器人并发送"帮助"
- **今日人品**: `/jrrp` 或 `/今日人品`
- **计算器**: `/calc <表达式>`
- **插件迁移**: `/migrate_plugin <插件名>`

更多命令请查看 [命令使用文档](docs/命令使用文档.md)。

## 开发指南

### 项目结构

```
nonebot-chatbot/
├── bot.py                 # NoneBot入口文件
├── config.py              # 配置管理模块
├── requirements.txt       # Python依赖
├── .env.example          # 环境变量示例
├── src/
│   ├── adapters/         # 适配器配置
│   ├── plugins/          # 插件目录
│   ├── services/         # 服务层
│   ├── database/         # 数据库层
│   └── utils/            # 工具模块
├── configs/              # 配置文件
├── logs/                 # 日志目录
└── data/                 # 数据目录
```

### 添加插件

#### 方式 1: 使用 CLI 工具（推荐）

```bash
# 安装项目（如果还没安装）
pip install -e .

# 使用 CLI 工具快速创建插件
nb-add-plugin my_plugin --description "我的插件"

# 查看帮助
nb-add-plugin --help
```

#### 方式 2: 手动创建

1. 在 `src/plugins/` 目录下创建插件文件
2. 按照NoneBot插件规范编写插件代码
3. 插件会自动加载（如果已启用）

详见 [插件开发指南](docs/插件开发指南.md) 和 [CLI工具使用指南](docs/CLI工具使用指南.md)

### 开发规范

- 使用Python 3.9+语法
- 遵循PEP 8代码规范
- 关键逻辑添加注释
- 使用类型提示（Type Hints）

## 部署说明

### 本地部署

直接运行 `python bot.py` 即可。

### Docker部署

```bash
# 构建镜像
docker build -t nonebot-chatbot:latest .

# 使用docker-compose启动
docker-compose up -d
```

## 功能特性

- ✅ 支持OneBot V11协议
- ✅ 对接NTQQ平台（WebSocket双向通信）
- ✅ 支持完整的消息类型（文本、图片、文件、语音、视频等）
- ✅ 支持完整的事件类型（消息、通知、请求、元事件）
- ✅ 插件系统（加载、启用/禁用、配置管理）
- ✅ 插件配置数据库持久化（SQLite/MySQL）
- ✅ 配置管理（配置文件+环境变量）
- ✅ 日志系统（文件存储、日志轮转）
- ✅ 错误处理和重试机制
- ✅ 状态监控

## 技术栈

- **框架**：NoneBot2
- **适配器**：OneBot V11
- **数据库**：SQLite / MySQL
- **ORM**：SQLAlchemy
- **配置**：Pydantic + python-dotenv
- **日志**：loguru

## 安装

### 从 PyPI 安装（推荐）

```bash
pip install nonebot-chatbot
```

### 从源码安装

```bash
git clone https://github.com/your-username/nonebot-chatbot
cd nonebot-chatbot
pip install -e .
```

### 使用 nb-cli 安装

```bash
pip install nb-cli
nb plugin install nonebot-chatbot
```

## 参考文档

- [NoneBot2官方文档](https://nonebot.dev/)
- [OneBot协议文档](https://github.com/botuniverse/onebot-11)
- [NTQQ应用指南](../blog/docs/NTQQ应用指南/NTQQ使用指南-2025-12-30.md)
- [NoneBot市场兼容指南](docs/NoneBot市场兼容指南.md)

## NoneBot 市场兼容性

本项目已配置为兼容 NoneBot 市场，可以：

- ✅ 通过 `pip install` 安装
- ✅ 使用 `nb-cli` 管理
- ✅ 在 NoneBot 市场发布

详见 [NoneBot市场兼容指南](docs/NoneBot市场兼容指南.md) 和 [兼容性总结](MARKET_COMPATIBILITY.md)。

## 许可证

MIT License

详见 [LICENSE](LICENSE) 文件。

## 贡献

欢迎提交 Issue 和 Pull Request！

## 更新日志

### v0.1.0 (2024-01-XX)

- ✅ 初始版本发布
- ✅ 支持 OneBot V11 协议
- ✅ 完整的插件系统
- ✅ 数据库持久化
- ✅ 状态监控
- ✅ NoneBot 市场兼容

