# NoneBot 市场兼容指南

## 概述

本文档说明如何让项目兼容 NoneBot 市场（NoneBot Store），以便插件可以被市场识别、安装和管理。

## 市场要求

### 1. 项目命名规范

- **插件项目**：必须以 `nonebot-plugin-` 为前缀
- **适配器项目**：必须以 `nonebot-adapter-` 为前缀
- **机器人项目**：可以使用其他命名，但建议遵循规范

**注意**：当前项目名为 `nonebot-chatbot`，如果要发布为插件，建议重命名为 `nonebot-plugin-chatbot`。

### 2. 必需文件

#### pyproject.toml

这是最重要的配置文件，必须包含：

```toml
[project]
name = "nonebot-plugin-xxx"
version = "0.1.0"
description = "插件描述"
readme = "README.md"
requires-python = ">=3.9,<4.0"
dependencies = [
    "nonebot2>=2.0.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

#### README.md

必须包含：
- 项目简介
- 安装方法
- 使用方法
- 配置说明
- 许可证信息

#### LICENSE

必须包含许可证文件（推荐 MIT 或 Apache 2.0）。

### 3. 插件元数据

每个插件文件应该包含 `PluginMetadata`：

```python
from nonebot.plugin import PluginMetadata

__plugin_meta__ = PluginMetadata(
    name="插件名称",
    description="插件描述",
    usage="使用方法",
    type="application",  # 或 "library"
    homepage="https://github.com/user/repo",
    supported_adapters={"~onebot.v11"},
)
```

### 4. 项目结构

推荐的项目结构：

```
nonebot-plugin-xxx/
├── pyproject.toml          # 项目配置
├── README.md              # 项目说明
├── LICENSE                # 许可证
├── MANIFEST.in           # 打包清单（可选）
├── src/
│   └── plugins/
│       └── plugin_name.py # 插件代码
└── tests/                # 测试文件（可选）
```

## 当前项目配置

### 已完成的配置

✅ **pyproject.toml** - 已创建，包含完整的项目元数据
✅ **PluginMetadata** - 已为 hello.py 和 example_plugin.py 添加元数据
✅ **MANIFEST.in** - 已创建打包清单
✅ **README.md** - 已存在，包含项目说明

### 需要调整的内容

#### 1. 项目名称（可选）

如果要发布到市场，建议将项目重命名：

```bash
# 方式1: 修改 pyproject.toml 中的 name
[project]
name = "nonebot-plugin-chatbot"  # 改为插件命名

# 方式2: 保持当前名称，作为机器人框架发布
# 当前名称 nonebot-chatbot 也可以，但更适合作为框架而非插件
```

#### 2. 添加 LICENSE 文件

创建 `LICENSE` 文件（推荐 MIT）：

```text
MIT License

Copyright (c) 2024 NoneBot Chatbot Team

Permission is hereby granted...
```

#### 3. 更新 README.md

确保 README.md 包含：
- ✅ 项目简介
- ✅ 安装方法（pip install）
- ✅ 快速开始
- ✅ 配置说明
- ✅ 许可证信息

#### 4. 为所有插件添加元数据

为 `src/plugins/` 目录下的所有插件添加 `PluginMetadata`：

- ✅ hello.py - 已添加
- ✅ example_plugin.py - 已添加
- ⏳ admin.py - 需要添加
- ⏳ weather.py - 需要添加

## 发布到市场

### 步骤 1: 准备发布

1. **确保所有测试通过**
   ```bash
   pytest
   ```

2. **检查代码质量**
   ```bash
   ruff check .
   ```

3. **更新版本号**
   在 `pyproject.toml` 中更新版本号。

### 步骤 2: 构建包

```bash
# 安装构建工具
pip install build

# 构建包
python -m build
```

这会生成 `dist/` 目录，包含：
- `nonebot-chatbot-0.1.0.tar.gz` - 源码包
- `nonebot_chatbot-0.1.0-py3-none-any.whl` - 轮子包

### 步骤 3: 发布到 PyPI

```bash
# 安装 twine
pip install twine

# 上传到 PyPI（测试）
twine upload --repository testpypi dist/*

# 上传到 PyPI（正式）
twine upload dist/*
```

### 步骤 4: 提交到 NoneBot 市场

1. 访问 [NoneBot 商店仓库](https://github.com/nonebot/nonebot2/tree/master/packages)
2. 按照仓库的 CONTRIBUTING 指南提交 PR
3. 在相应的 JSON 文件中添加项目信息

## 安装和使用

### 从 PyPI 安装

```bash
pip install nonebot-chatbot
```

### 从源码安装

```bash
git clone https://github.com/your-username/nonebot-chatbot
cd nonebot-chatbot
pip install -e .
```

### 使用 nb-cli 安装（如果发布为插件）

```bash
nb plugin install nonebot-plugin-chatbot
```

## 验证兼容性

### 使用 nb-cli 验证

```bash
# 安装 nb-cli
pip install nb-cli

# 创建测试项目
nb create

# 安装插件
nb plugin install nonebot-chatbot

# 测试插件加载
nb plugin test
```

### 检查清单

- [ ] pyproject.toml 配置完整
- [ ] README.md 包含必要信息
- [ ] LICENSE 文件存在
- [ ] 所有插件包含 PluginMetadata
- [ ] 可以通过 pip install 安装
- [ ] 代码通过 lint 检查
- [ ] 测试通过

## 常见问题

### Q1: 项目名称不符合规范怎么办？

**A:** 有两种选择：
1. 重命名项目为 `nonebot-plugin-xxx`
2. 保持当前名称，作为机器人框架而非插件发布

### Q2: 如何测试插件是否能被市场识别？

**A:** 
1. 使用 `nb-cli` 创建测试项目
2. 安装你的插件
3. 检查是否能正常加载

### Q3: 插件依赖如何处理？

**A:** 在 `pyproject.toml` 的 `dependencies` 中声明所有依赖，市场会自动处理。

### Q4: 需要发布到 PyPI 吗？

**A:** 是的，NoneBot 市场要求插件必须可以通过 `pip install` 安装，所以需要发布到 PyPI。

## 参考资源

- [NoneBot 官方文档](https://nonebot.dev/)
- [PEP 621 - 项目元数据](https://peps.python.org/pep-0621/)
- [hatchling 文档](https://hatch.pypa.io/)
- [NoneBot 商店仓库](https://github.com/nonebot/nonebot2/tree/master/packages)

## 总结

要让项目兼容 NoneBot 市场，需要：

1. ✅ 创建 `pyproject.toml` 配置文件
2. ✅ 为插件添加 `PluginMetadata`
3. ✅ 确保项目可以通过 pip 安装
4. ⏳ 创建 LICENSE 文件
5. ⏳ 更新 README.md（如需要）
6. ⏳ 发布到 PyPI
7. ⏳ 提交到 NoneBot 市场

当前项目已经完成了大部分配置，可以开始准备发布了！

