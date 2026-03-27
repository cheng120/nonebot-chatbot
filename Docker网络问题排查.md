# Docker网络问题排查

## 问题描述

Docker启动后，服务显示已启动：
- HTTP服务: 127.0.0.1:3000 已启动
- WebSocket服务: 127.0.0.1:3001 已启动
- WebSocket反向服务: ws://localhost:8082 已启动

但无法从宿主机访问这些服务。

## 问题原因

服务绑定在 `127.0.0.1`（localhost），这会导致：
- 容器内可以访问
- 但宿主机无法通过端口映射访问

**解决方案**: 需要将服务绑定到 `0.0.0.0`，这样Docker端口映射才能正常工作。

## 解决步骤

### 1. 检查NapCat配置文件

NapCat的配置文件通常在：
```
napcatqq/napcat/config/
```

查找包含以下内容的配置文件：
- HTTP服务配置（host: 127.0.0.1）
- WebSocket服务配置（host: 127.0.0.1）

### 2. 修改配置绑定地址

将服务绑定地址从 `127.0.0.1` 改为 `0.0.0.0`：

**HTTP服务配置**:
```json
{
  "host": "0.0.0.0",  // 改为0.0.0.0
  "port": 3000
}
```

**WebSocket服务配置**:
```json
{
  "host": "0.0.0.0",  // 改为0.0.0.0
  "port": 3001
}
```

### 3. 重启Docker容器

```bash
cd /Users/cheng/Desktop/document/cheng/napcatqq
docker-compose restart
# 或
docker-compose down
docker-compose up -d
```

### 4. 验证端口映射

```bash
# 检查端口是否被监听
lsof -i :3000
lsof -i :3001

# 测试HTTP连接
curl http://localhost:3000/status
# 或
curl http://127.0.0.1:3000/status

# 测试WebSocket（使用测试脚本）
cd /Users/cheng/Desktop/document/cheng/nonebot-chatbot
python3 测试连接.py
```

## 配置文件位置

根据NapCat的配置结构，配置文件可能在：

1. **OneBot配置**: `napcat/config/onebot.json` 或类似文件
2. **主配置文件**: `napcat/config/napcat.json` 或 `config.json`
3. **环境变量**: 通过docker-compose.yml的环境变量配置

## 快速修复方法

### 方法1: 修改docker-compose.yml（如果支持环境变量）

```yaml
services:
    napcat:
        environment:
            - NAPCAT_UID=${NAPCAT_UID}
            - NAPCAT_GID=${NAPCAT_GID}
            - HTTP_HOST=0.0.0.0  # 添加这个
            - WS_HOST=0.0.0.0    # 添加这个
        ports:
            - 3000:3000
            - 3001:3001
            - 6099:6099
```

### 方法2: 直接修改配置文件

找到NapCat的配置文件，将host改为0.0.0.0。

### 方法3: 使用host网络模式（不推荐，但可以快速测试）

```yaml
services:
    napcat:
        network_mode: host  # 改为host模式
        # 注意：host模式下不需要ports映射
```

## 验证修复

修复后，应该能看到：
- 服务绑定在 `0.0.0.0:3000` 和 `0.0.0.0:3001`
- 可以从宿主机访问 `http://localhost:3000`
- WebSocket可以连接 `ws://localhost:3001`

## 更新机器人配置

修复后，更新机器人配置：

```yaml
# configs/config.yaml
adapters:
  - name: OneBot V11
    api_root: http://localhost:3000  # 或 http://127.0.0.1:3000
    access_token: "9U7Cq1BP7v22TJ,l"
    websocket:
      url: ws://localhost:3001  # 或 ws://127.0.0.1:3001
      access_token: "3Nh{+9<i^rF-DvGZ"
```

---

**提示**: 如果找不到配置文件，可以：
1. 查看Docker容器内的配置：`docker exec -it napcat ls -la /app/config`
2. 查看NapCat的文档了解配置位置
3. 检查环境变量配置方式

