# 第三方插件修改记录

本文档记录了在 `src/plugins/` 目录下修改过的第三方 NoneBot 插件。

## 修改的插件列表

### 1. suggarchat 系列
- **路径**: `src/plugins/suggarchat/`, `src/plugins/_suggarchat_disabled/`
- **原插件**: nonebot-plugin-suggarchat
- **修改内容**: [待补充具体修改说明]

### 2. alconna
- **路径**: `src/plugins/alconna/`
- **原插件**: arclet-alconna
- **修改内容**: [待补充具体修改说明]

### 3. bilichat
- **路径**: `src/plugins/bilichat/`
- **原插件**: nonebot-plugin-bilichat
- **修改内容**: [待补充具体修改说明]

### 4. xiuxian_2
- **路径**: `src/plugins/xiuxian_2/`
- **原插件**: nonebot-plugin-xiuxian-2
- **修改内容**: [待补充具体修改说明]

### 5. 其他插件
- dorodoro, epicfree, fishing2, jrrp3, memes_api, shindan 等
- **修改内容**: [待补充具体修改说明]

## Git 管理策略

1. **本地化插件**: 所有修改过的第三方插件都放在 `src/plugins/` 下
2. **避免冲突**: 不在 `requirements.txt` 中列出这些本地化的插件
3. **版本记录**: 每次修改后及时提交
4. **备份策略**: 定期推送到远程仓库

## 恢复原始版本

如需恢复某个插件的原始版本，请参考对应插件的官方仓库。

---
创建时间: 2026-03-30
最后更新: 2026-03-30