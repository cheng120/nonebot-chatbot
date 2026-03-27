# TASK-003：更新配置文件并验证注册

## 概述

| 属性 | 内容 |
|------|------|
| 任务ID | TASK-003 |
| 任务类型 | [CFG] |
| 优先级 | P0 |
| 预估工时 | 0.5 小时 |
| 依赖任务 | TASK-002 |
| 关联文件 | `configs/config.yaml` |

### 任务目标

确认配置文件中的插件路径已正确更新，验证插件可以正常加载和注册到项目中。

---

## 任务详情

### 变更点清单

| # | 变更类型 | 文件路径 | 位置定位 | 变更说明 |
|---|----------|----------|----------|----------|
| 1 | 检查配置 | `configs/config.yaml` | L58 `plugins.enabled` | 确认 `src.plugins.xiuxian_2` 在启用列表中 |
| 2 | 验证加载 | `bot.py` | L106 `plugin_manager.load_all_plugins()` | 验证插件加载逻辑 |
| 3 | 测试运行 | 启动机器人 | - | 验证插件正常加载和运行 |

### 变更点详情

#### 变更点 1：检查配置文件

| 属性 | 内容 |
|------|------|
| 文件路径 | `configs/config.yaml` |
| 变更类型 | 检查配置 |
| 位置定位 | L58 `plugins.enabled` 列表 |

**检查要点**：
1. 确认 `src.plugins.xiuxian_2` 在 `plugins.enabled` 列表中
2. 确认没有旧的插件名称（如 `nonebot_plugin_xiuxian_2` 或 `nonebot-plugin-xiuxian-2`）在列表中
3. 确认 `plugins.dir` 配置为 `./src/plugins`

**当前配置状态**：

```yaml
plugins:
  dir: ./src/plugins
  enabled:
    - src.plugins.xiuxian_2  # 已存在，但插件文件尚未迁移
```

**验证命令**：

```bash
# 检查配置文件
cd /Users/cheng/Desktop/document/cheng/nonebot-chatbot
grep -A 20 "plugins:" configs/config.yaml | grep "xiuxian_2"

# 确认插件目录存在
ls -d src/plugins/xiuxian_2/
```

**预期结果**：
- `src.plugins.xiuxian_2` 在启用列表中
- 插件目录 `src/plugins/xiuxian_2/` 存在
- 没有重复的插件配置

---

#### 变更点 2：验证插件加载逻辑

| 属性 | 内容 |
|------|------|
| 文件路径 | `bot.py` |
| 变更类型 | 验证代码 |
| 位置定位 | L106 `await plugin_manager.load_all_plugins()` |

**验证要点**：
1. `PluginManager` 会扫描 `src/plugins/` 目录
2. 对于包结构插件（有 `__init__.py` 的目录），会自动识别为 `src.plugins.xxx`
3. 插件管理器会检查 `plugins.enabled` 列表，只加载启用的插件

**相关代码**：

```72:106:bot.py
# 初始化插件管理器（TASK-011）
from src.services.plugin_manager import PluginManager
plugin_manager = PluginManager(config.plugins.dir, db_manager, config.plugins)

# ... 其他初始化代码 ...

# 加载插件
try:
	await plugin_manager.load_all_plugins()
	logger.info("插件加载完成")
except Exception as e:
	logger.error(f"插件加载失败: {e}")
```

**验证方法**：
- 查看日志输出，确认插件加载成功
- 检查是否有错误信息

---

#### 变更点 3：测试插件运行

| 属性 | 内容 |
|------|------|
| 测试方式 | 启动机器人并检查日志 |
| 变更类型 | 功能测试 |

**测试步骤**：

1. **启动自检模式**（推荐，不启动 Web 服务）：

```bash
cd /Users/cheng/Desktop/document/cheng/nonebot-chatbot
NB_SELFTEST=1 ./venv/bin/python bot.py
```

2. **检查日志输出**：

```bash
# 查看日志文件
tail -f logs/bot.log | grep -i "xiuxian"

# 或查看控制台输出
# 应该看到类似以下信息：
# - "发现包结构插件: src.plugins.xiuxian_2"
# - "✅ 包结构插件 src.plugins.xiuxian_2 已被 load_plugins 自动加载"
# - "插件 src.plugins.xiuxian_2 已加载并启用"
```

3. **验证插件命令**（如果机器人已连接）：

```bash
# 测试修仙插件命令（需要在 QQ 群中测试）
# 例如：发送 "我要修仙" 或 "修仙帮助"
```

**预期结果**：
- 插件加载成功，无错误信息
- 日志中显示插件已启用
- 插件命令可以正常响应（如果机器人已连接）

---

## 实施检查表

### 代码实施检查

| # | 检查项 | 状态 |
|---|--------|------|
| 1 | `configs/config.yaml` 中 `src.plugins.xiuxian_2` 在启用列表中 | ✅ |
| 2 | 没有旧的插件名称在配置中 | ✅ |
| 3 | 插件目录 `src/plugins/xiuxian_2/` 存在 | ✅ |

### 功能测试检查

| # | 测试项 | 验证方法 | 预期结果 | 状态 |
|---|--------|----------|----------|------|
| 1 | 配置文件格式正确 | `python -c "import yaml; yaml.safe_load(open('configs/config.yaml'))"` | 无 YAML 解析错误 | ✅ |
| 2 | 插件目录存在 | `ls -d src/plugins/xiuxian_2/` | 目录存在 | ✅ |
| 3 | 插件加载成功 | 启动自检模式，查看日志 | 日志显示插件已加载 | ⚠️ |
| 4 | 插件启用成功 | 查看日志 | 日志显示插件已启用 | ⚠️ |
| 5 | 插件命令可用（可选） | 在 QQ 群中测试命令 | 命令正常响应 | ⬜ |

### 完成确认

- [ ] 配置文件已正确更新
- [ ] 插件加载测试通过
- [ ] 插件启用验证通过
- [ ] 所有检查项已完成
- [ ] 迁移任务完成

---

## 风险与应对

| 风险点 | 影响 | 应对方案 |
|--------|------|----------|
| 配置文件格式错误 | YAML 解析失败 | 检查缩进和语法，使用 YAML 验证工具 |
| 插件加载失败 | 插件无法使用 | 查看详细错误日志，检查导入路径和依赖 |
| 插件未启用 | 命令不响应 | 检查 `plugins.enabled` 配置，确认插件名称正确 |
| 依赖插件缺失 | 运行时错误 | 检查 `nonebot_plugin_apscheduler` 是否可用 |

---

## 备注

1. **配置文件优先级**：根据 `PluginManager` 的逻辑，配置文件的优先级高于数据库
2. **自动迁移机制**：`PluginManager` 有自动迁移外部插件的机制，但我们已经手动迁移，所以应该直接使用本地路径
3. **数据目录**：插件使用 `data/xiuxian/` 目录存储数据，确保该目录存在且有写权限
4. **测试建议**：建议先使用自检模式测试，确认无误后再正式启动机器人

---

## 后续工作

迁移完成后，可以考虑：
1. 从 `pyproject.toml` 中移除 `nonebot-plugin-xiuxian-2` 的配置（如果存在）
2. 从虚拟环境中卸载 `nonebot-plugin-xiuxian-2`（可选，如果不再需要）
3. 更新项目文档，说明插件已迁移到本地

