# TASK-001：复制插件文件到本地目录

## 概述

| 属性 | 内容 |
|------|------|
| 任务ID | TASK-001 |
| 任务类型 | [CFG] |
| 优先级 | P0 |
| 预估工时 | 0.5 小时 |
| 依赖任务 | 无 |
| 关联文件 | `src/plugins/xiuxian_2/` |

### 任务目标

将 `nonebot_plugin_xiuxian_2` 插件从虚拟环境的 `site-packages` 目录复制到项目的 `src/plugins/xiuxian_2` 目录，完成文件层面的迁移。

---

## 任务详情

### 变更点清单

| # | 变更类型 | 文件路径 | 位置定位 | 变更说明 |
|---|----------|----------|----------|----------|
| 1 | 新增目录 | `src/plugins/xiuxian_2/` | - | 创建插件目标目录 |
| 2 | 新增文件 | `src/plugins/xiuxian_2/__init__.py` | - | 复制插件主入口文件 |
| 3 | 新增目录 | `src/plugins/xiuxian_2/xiuxian/` | - | 复制插件核心模块目录 |
| 4 | 新增文件 | `src/plugins/xiuxian_2/xiuxian/**/*.py` | - | 复制所有 Python 文件 |
| 5 | 新增文件 | `src/plugins/xiuxian_2/xiuxian/**/*.json` | - | 复制所有 JSON 配置文件 |

### 变更点详情

#### 变更点 1：创建插件目标目录

| 属性 | 内容 |
|------|------|
| 文件路径 | `src/plugins/xiuxian_2/` |
| 变更类型 | 新增目录 |
| 参考实现 | 其他已迁移插件目录结构（如 `src/plugins/anans_sketchbook/`） |

**实现要点**：
- 使用项目迁移工具 `src/plugins/migrate_plugin.py` 的 `copy_plugin_to_local` 函数
- 目标目录名：`xiuxian_2`（从 `nonebot-plugin-xiuxian-2` 转换而来）
- 如果目录已存在，工具会自动备份到 `xiuxian_2.bak.<timestamp>`

**执行命令**：

```bash
# 方式1：使用迁移脚本（推荐）
cd /Users/cheng/Desktop/document/cheng/nonebot-chatbot
./venv/bin/python -c "
from src.plugins.migrate_plugin import copy_plugin_to_local
success, path, error = copy_plugin_to_local('nonebot_plugin_xiuxian_2', 'nonebot-plugin-xiuxian-2')
print(f'迁移结果: success={success}, path={path}, error={error}')
"

# 方式2：使用批量迁移脚本
./venv/bin/python scripts/migrate_all_plugins.py
```

---

#### 变更点 2-5：复制插件文件

| 属性 | 内容 |
|------|------|
| 源路径 | `venv/lib/python3.13/site-packages/nonebot_plugin_xiuxian_2/` |
| 目标路径 | `src/plugins/xiuxian_2/` |
| 变更类型 | 新增文件（批量复制） |

**需要复制的文件类型**：
- 所有 `.py` 文件（Python 源代码）
- 所有 `.json` 文件（配置文件）
- 所有 `.yaml` / `.yml` 文件（配置文件）
- 所有 `.txt` / `.md` 文件（文档）
- 所有 `.html` / `.css` / `.js` 文件（前端资源）
- 所有图片文件（`.png`, `.jpg`, `.jpeg`, `.gif`, `.svg` 等）
- 所有字体文件（`.ttf`, `.woff`, `.woff2` 等）

**文件结构**：

```
src/plugins/xiuxian_2/
├── __init__.py                    # 插件入口（已存在，直接复制）
├── xiuxian/                       # 核心模块目录
│   ├── __init__.py
│   ├── config.py
│   ├── data_source.py
│   ├── download_xiuxian_data.py
│   ├── item_json.py
│   ├── lay_out.py
│   ├── player_fight.py
│   ├── read_buff.py
│   ├── utils.py
│   ├── xiuxian_back/              # 背包模块
│   ├── xiuxian_bank/              # 银行模块
│   ├── xiuxian_base/              # 基础模块
│   ├── xiuxian_boss/              # Boss模块
│   ├── xiuxian_buff/              # Buff模块
│   ├── xiuxian_config.py
│   ├── xiuxian_impart/            # 传承模块
│   ├── xiuxian_impart_pk/         # 虚神界模块
│   ├── xiuxian_info/              # 信息模块
│   ├── xiuxian_mixelixir/         # 炼丹模块
│   ├── xiuxian_opertion.py
│   ├── xiuxian_rift/              # 秘境模块
│   ├── xiuxian_sect/              # 宗门模块
│   ├── xiuxian_work/              # 悬赏令模块
│   ├── xiuxian2_handle.py
│   ├── xn_xiuxian_impart_config.py
│   └── xn_xiuxian_impart.py
└── ...（其他资源文件）
```

**实现要点**：
- 使用 `shutil.copy2()` 复制文件，保留元数据
- 保持目录结构不变
- 不修改文件内容（原样复制）

---

## 实施检查表

### 代码实施检查

| # | 检查项 | 状态 |
|---|--------|------|
| 1 | 目标目录 `src/plugins/xiuxian_2/` 已创建 | ✅ |
| 2 | `__init__.py` 文件已复制 | ✅ |
| 3 | `xiuxian/` 目录及其所有子目录已复制 | 🔄 |
| 4 | 所有 `.py` 文件已复制 | 🔄 |
| 5 | 所有资源文件（`.json`, `.yaml`, 图片等）已复制 | ⬜ |
| 6 | 文件权限和元数据已保留 | ✅ |

### 功能测试检查

| # | 测试项 | 验证方法 | 预期结果 | 状态 |
|---|--------|----------|----------|------|
| 1 | 目录结构完整性 | `ls -R src/plugins/xiuxian_2/` | 目录结构与源目录一致 | ⬜ |
| 2 | 文件数量一致性 | 统计文件数量 | 与源目录文件数量一致 | ⬜ |
| 3 | Python 语法检查 | `python -m py_compile src/plugins/xiuxian_2/**/*.py` | 无语法错误 | ⬜ |

### 完成确认

- [ ] 所有文件已复制完成
- [ ] 目录结构验证通过
- [ ] 文件完整性检查通过
- [ ] 准备进入下一任务（TASK-002）

---

## 风险与应对

| 风险点 | 影响 | 应对方案 |
|--------|------|----------|
| 目标目录已存在 | 可能覆盖已有文件 | 迁移工具会自动备份到 `.bak.<timestamp>` |
| 文件权限问题 | 无法复制文件 | 检查文件权限，必要时使用 `sudo` |
| 磁盘空间不足 | 复制失败 | 检查磁盘空间，清理临时文件 |
| 路径编码问题 | 文件名乱码 | 确保使用 UTF-8 编码处理路径 |

---

## 备注

1. **迁移工具说明**：项目已有迁移工具 `src/plugins/migrate_plugin.py`，可以直接使用其 `copy_plugin_to_local` 函数
2. **备份机制**：如果目标目录已存在，工具会自动备份，无需手动处理
3. **文件完整性**：迁移工具会复制所有相关文件，包括资源文件和配置文件

