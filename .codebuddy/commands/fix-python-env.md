---
description: 修复 CodeBuddy Python 环境配置
---

# 修复 Python 环境配置

## 使用场景

当 CodeBuddy 报错 "basedpyright Error: 无法解析导入 xxx" 时使用。

## 诊断步骤

1. 检查虚拟环境是否存在
2. 验证 nonebot 等包是否可导入
3. 检查 `.vscode/settings.json` 配置
4. 提供 CodeBuddy 解释器选择指导

## 执行操作

### 1. 验证虚拟环境

```bash
cd /Users/cheng/Desktop/document/cheng/nonebot-chatbot
./venv/bin/python --version
```

应该输出: `Python 3.13.5`

### 2. 验证 nonebot

```bash
./venv/bin/python -c "import nonebot; print('✅ nonebot 版本:', nonebot.__version__)"
```

应该输出: `✅ nonebot 版本: 2.4.4`

### 3. 运行完整验证

```bash
python3 validate_cursor_config.py
```

### 4. 在 CodeBuddy 中选择解释器

如果验证通过但 CodeBuddy 仍报错：

1. 在 CodeBuddy 中按 `Cmd + Shift + P`
2. 输入: `Python: Select Interpreter`
3. 选择: `./venv/bin/python`
4. 等待重新索引完成

### 5. 重启 CodeBuddy

如果以上步骤无效：

1. 完全关闭 CodeBuddy (Cmd + Q)
2. 重新打开项目
3. 等待索引完成（右下角显示 "Ready"）
4. 验证错误是否消失

## 配置文件检查

### .vscode/settings.json

确保包含以下配置：

```json
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "python.languageServer": "Pylance",
  "python.analysis.typeCheckingMode": "basic"
}
```

### 检查配置

```bash
cat .vscode/settings.json
```

## 常见问题

### Q1: 虚拟环境不存在

```bash
# 创建虚拟环境
python3 -m venv venv

# 安装依赖
./venv/bin/pip install -r requirements.txt
```

### Q2: nonebot 未安装

```bash
# 安装依赖
./venv/bin/pip install -r requirements.txt

# 或单独安装
./venv/bin/pip install nonebot2 nonebot-adapter-onebot
```

### Q3: CodeBuddy 不识别虚拟环境

**原因**: 解释器路径错误或未选择

**解决**:
1. 检查 `.vscode/settings.json` 中的路径
2. 使用 `Python: Select Interpreter` 手动选择
3. 重启 CodeBuddy

## 验证成功标志

运行以下检查应该全部通过：

- [ ] `./venv/bin/python --version` 输出 `Python 3.13.5`
- [ ] `./venv/bin/python -c "import nonebot"` 无错误
- [ ] `python3 validate_cursor_config.py` 输出 `✅ 所有检查通过！`
- [ ] CodeBuddy 右下角显示 `Python 3.13.x: venv`
- [ ] `bot.py` 第 6 行 `import nonebot` 无错误
- [ ] 输入 `nonebot.` 有智能提示

## 相关命令

- `/test-bot` - 测试 Bot 连接
- `/restart-bot` - 重启 Bot 服务

## 相关文档

- [Python 虚拟环境配置规则](.cursor/rules/python-venv-config.md)
- [验证脚本](validate_cursor_config.py)
- [诊断脚本](fix_cursor_issues.sh)
