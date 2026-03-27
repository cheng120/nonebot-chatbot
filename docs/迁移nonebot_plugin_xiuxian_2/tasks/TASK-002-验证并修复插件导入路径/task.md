# TASK-002：验证并修复插件导入路径

## 概述

| 属性 | 内容 |
|------|------|
| 任务ID | TASK-002 |
| 任务类型 | [CFG] |
| 优先级 | P0 |
| 预估工时 | 1 小时 |
| 依赖任务 | TASK-001 |
| 关联文件 | `src/plugins/xiuxian_2/__init__.py` |

### 任务目标

检查插件迁移后的导入路径是否正确，修复可能的导入问题，确保插件可以正常加载。

---

## 任务详情

### 变更点清单

| # | 变更类型 | 文件路径 | 位置定位 | 变更说明 |
|---|----------|----------|----------|----------|
| 1 | 检查代码 | `src/plugins/xiuxian_2/__init__.py` | L1-L6 | 检查 `require` 和 `load_plugins` 调用 |
| 2 | 检查代码 | `src/plugins/xiuxian_2/xiuxian/**/*.py` | 所有 `import` 语句 | 检查相对导入和绝对导入 |
| 3 | 修改代码（如需要） | `src/plugins/xiuxian_2/__init__.py` | L5 | 修复 `require('nonebot_plugin_apscheduler')` 依赖 |

### 变更点详情

#### 变更点 1：检查插件入口文件

| 属性 | 内容 |
|------|------|
| 文件路径 | `src/plugins/xiuxian_2/__init__.py` |
| 变更类型 | 检查代码 |
| 参考代码 | ```1:6:venv/lib/python3.13/site-packages/nonebot_plugin_xiuxian_2/__init__.py
from pathlib import Path
from nonebot import require, load_plugins

dir_ = Path(__file__).parent
require('nonebot_plugin_apscheduler')
load_plugins(str(dir_ / "xiuxian"))
``` |

**检查要点**：
1. `require('nonebot_plugin_apscheduler')` - 检查依赖插件是否已安装或已迁移
2. `load_plugins(str(dir_ / "xiuxian"))` - 检查子模块加载路径是否正确
3. `Path(__file__).parent` - 检查路径解析是否正确

**预期行为**：
- `require` 调用应该能找到 `nonebot_plugin_apscheduler`（如果已迁移，可能需要改为 `src.plugins.apscheduler`）
- `load_plugins` 应该能正确加载 `xiuxian/` 目录下的所有子模块

---

#### 变更点 2：检查子模块导入

| 属性 | 内容 |
|------|------|
| 文件路径 | `src/plugins/xiuxian_2/xiuxian/**/*.py` |
| 变更类型 | 检查代码 |
| 检查范围 | 所有 Python 文件中的 `import` 语句 |

**检查要点**：
1. **相对导入**：检查 `from . import xxx` 或 `from .. import xxx` 是否正确
2. **绝对导入**：检查 `from nonebot_plugin_xiuxian_2.xiuxian import xxx` 是否需要改为 `from src.plugins.xiuxian_2.xiuxian import xxx`
3. **第三方依赖**：检查对其他插件的依赖（如 `nonebot_plugin_apscheduler`）

**检查命令**：

```bash
# 检查所有导入语句
cd /Users/cheng/Desktop/document/cheng/nonebot-chatbot
grep -r "from nonebot_plugin_xiuxian_2" src/plugins/xiuxian_2/
grep -r "import nonebot_plugin_xiuxian_2" src/plugins/xiuxian_2/

# 检查 require 调用
grep -r "require(" src/plugins/xiuxian_2/
```

**常见问题**：
- 如果插件内部使用 `from nonebot_plugin_xiuxian_2.xiuxian import xxx`，需要改为 `from .xiuxian import xxx` 或保持相对导入
- 如果插件内部使用绝对导入引用自身，可能需要修改为相对导入

---

#### 变更点 3：修复依赖插件引用（如需要）

| 属性 | 内容 |
|------|------|
| 文件路径 | `src/plugins/xiuxian_2/__init__.py` |
| 变更类型 | 修改代码（如需要） |
| 位置定位 | L5 `require('nonebot_plugin_apscheduler')` |

**修复场景**：
- 如果 `nonebot_plugin_apscheduler` 已迁移到本地，需要改为 `require('src.plugins.apscheduler')`
- 如果 `nonebot_plugin_apscheduler` 仍在 `site-packages`，保持原样即可

**修复示例**：

```python
# 原代码
require('nonebot_plugin_apscheduler')

# 如果 apscheduler 已迁移到本地
require('src.plugins.apscheduler')

# 或者尝试两种方式（兼容性更好）
try:
	require('src.plugins.apscheduler')
except Exception:
	require('nonebot_plugin_apscheduler')
```

**检查命令**：

```bash
# 检查 apscheduler 是否已迁移
ls -d src/plugins/apscheduler* 2>/dev/null || echo "apscheduler 未迁移到本地"

# 检查 apscheduler 是否在 site-packages
python -c "import nonebot_plugin_apscheduler; print(nonebot_plugin_apscheduler.__file__)"
```

---

## 实施检查表

### 代码实施检查

| # | 检查项 | 状态 |
|---|--------|------|
| 1 | `__init__.py` 中的 `require` 调用已检查 | ✅ |
| 2 | `__init__.py` 中的 `load_plugins` 调用已检查 | ✅ |
| 3 | 所有子模块的导入语句已检查 | ✅ |
| 4 | 发现的问题已修复（如有） | ✅ |
| 5 | 修复后的代码已验证语法正确 | ✅ |

### 功能测试检查

| # | 测试项 | 验证方法 | 预期结果 | 状态 |
|---|--------|----------|----------|------|
| 1 | Python 语法检查 | `python -m py_compile src/plugins/xiuxian_2/**/*.py` | 无语法错误 | ⬜ |
| 2 | 导入路径检查 | `python -c "import sys; sys.path.insert(0, 'src'); from plugins.xiuxian_2 import *"` | 无导入错误 | ⬜ |
| 3 | 依赖插件检查 | 检查 `nonebot_plugin_apscheduler` 是否可用 | 依赖插件可正常导入 | ⬜ |

### 完成确认

- [ ] 所有导入路径已检查
- [ ] 发现的问题已修复
- [ ] 代码语法验证通过
- [ ] 准备进入下一任务（TASK-003）

---

## 风险与应对

| 风险点 | 影响 | 应对方案 |
|--------|------|----------|
| 插件内部使用绝对导入引用自身 | 导入失败 | 修改为相对导入或添加路径映射 |
| 依赖插件未安装或未迁移 | `require` 失败 | 检查依赖插件状态，必要时迁移或安装 |
| 相对导入路径错误 | 模块找不到 | 检查目录结构，修正导入路径 |
| 循环导入问题 | 运行时错误 | 重构导入结构，避免循环依赖 |

---

## 备注

1. **最小改动原则**：根据迁移工具的设计原则，尽量不改动第三方源码，只在必要时修复导入问题
2. **依赖检查**：优先检查 `nonebot_plugin_apscheduler` 的状态，这是插件的核心依赖
3. **测试方法**：可以使用 Python 的 `-m py_compile` 检查语法，使用 `import` 测试导入

