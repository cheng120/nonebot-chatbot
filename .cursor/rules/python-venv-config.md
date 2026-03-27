# Python 虚拟环境配置规则

## 规则说明

确保 CodeBuddy (Cursor) 使用项目的虚拟环境进行类型检查和代码分析。

## 配置要求

### 1. Python 解释器路径
- 路径: `./venv/bin/python`
- 版本: Python 3.13.5
- 包位置: `./venv/lib/python3.13/site-packages`

### 2. 类型检查
- 使用基于 Right (basedpyright) 进行类型检查
- 启用自动补全和智能提示
- 忽略第三方库的类型错误（可选）

### 3. 依赖包
所有必需的 Python 包都已安装在虚拟环境中：
- nonebot2 (v2.4.4)
- nonebot-adapter-onebot (v2.4.6)
- fastapi (v0.128.0)
- loguru (v0.7.3)
- sqlalchemy (v2.0.45)
- pydantic (v2.12.5)

## 验证方法

### 方法 1: 运行验证脚本
```bash
python3 validate_cursor_config.py
```

### 方法 2: 手动验证
```bash
./venv/bin/python -c "import nonebot; print('✅ nonebot 可用')"
```

### 方法 3: 在 CodeBuddy 中验证
1. 打开 `bot.py` 文件
2. 检查右下角状态栏
3. 应该显示 `Python 3.13.x: venv`
4. 第 6 行 `import nonebot` 不应该有错误

## 故障排除

### 问题: basedpyright 报错 "无法解析导入 nonebot"

**原因**: CodeBuddy 未使用正确的 Python 解释器

**解决方案**:
1. 在 CodeBuddy 中按 `Cmd + Shift + P`
2. 输入: `Python: Select Interpreter`
3. 选择: `./venv/bin/python`
4. 等待重新索引完成

### 问题: 右下角显示错误的 Python 版本

**原因**: 选择了系统 Python 而非虚拟环境

**解决方案**:
- 手动选择解释器（参考上面的解决方案）

### 问题: 重启后配置丢失

**原因**: CodeBuddy 需要时间重新加载配置

**解决方案**:
1. 完全关闭 CodeBuddy
2. 重新打开项目
3. 等待索引完成（右下角显示 "Ready"）

## 配置优先级

```
.vscode/settings.json (项目级配置)
  >
.cursor/rules/*.md (项目级规则)
  >
~/.cursor/ (全局配置)
  >
默认配置
```

## 相关文件

- `.vscode/settings.json` - 主要配置文件
- `validate_cursor_config.py` - 验证脚本
- `fix_cursor_issues.sh` - 诊断和修复脚本
