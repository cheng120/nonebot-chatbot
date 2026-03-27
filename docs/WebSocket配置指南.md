# WebSocket 配置指南

## 概述

NoneBot 通过 WebSocket 连接到 NapCatQQ（正向 WebSocket 模式）。需要同时配置 NapCatQQ 和 NoneBot 两端的设置。

## 配置步骤

### 1. 配置 NapCatQQ（服务端）

编辑 `napcat/config/onebot11.json`：

```json
{
    "network": {
      "websocketServers": [
        {
          "name": "WsServer",
          "enable": true,  // 必须设置为 true
          "host": "0.0.0.0",  // 监听所有网络接口
          "port": 3001,  // WebSocket 端口
          "messagePostFormat": "array",
          "reportSelfMessage": false,
          "token": "",  // 如果设置了 token，需要在 NoneBot 中也配置
          "enableForcePushEvent": true,
          "debug": false,
          "heartInterval": 30000
        }
      ]
    }
}
```

**重要配置项：**
- `enable`: 必须为 `true` 才能启用 WebSocket 服务器
- `host`: `0.0.0.0` 表示监听所有网络接口，`127.0.0.1` 表示仅本地
- `port`: WebSocket 端口，默认 3001
- `token`: 鉴权密钥（可选，如果设置需要在 NoneBot 中也配置）

### 2. 配置 NoneBot（客户端）

编辑 `configs/config.yaml`：

```yaml
# 适配器配置（OneBot V11）
adapters:
  - name: OneBot V11
    api_root: http://127.0.0.1:3000  # HTTP API 地址（用于主动调用）
    access_token: ""  # HTTP API 访问令牌（如果 NapCatQQ 设置了 token）
    websocket:
      url: ws://127.0.0.1:3001  # WebSocket 地址（必须与 NapCatQQ 的端口一致）
      access_token: ""  # WebSocket 访问令牌（如果 NapCatQQ 设置了 token）
```

**配置说明：**
- `websocket.url`: WebSocket 连接地址
  - 本地连接：`ws://127.0.0.1:3001`
  - 远程连接：`ws://服务器IP:3001`
- `websocket.access_token`: 如果 NapCatQQ 的 `token` 不为空，这里也需要填写相同的值
- `api_root`: HTTP API 地址，用于主动调用 API（如发送消息）

### 3. 配置示例

#### 示例 1：本地连接（无鉴权）

**NapCatQQ (`onebot11.json`):**
```json
{
  "websocketServers": [{
    "enable": true,
    "host": "0.0.0.0",
    "port": 3001,
    "token": ""
  }]
}
```

**NoneBot (`config.yaml`):**
```yaml
adapters:
  - name: OneBot V11
    api_root: http://127.0.0.1:3000
    access_token: ""
    websocket:
      url: ws://127.0.0.1:3001
      access_token: ""
```

#### 示例 2：本地连接（有鉴权）

**NapCatQQ (`onebot11.json`):**
```json
{
  "websocketServers": [{
    "enable": true,
    "host": "0.0.0.0",
    "port": 3001,
    "token": "my-secret-token-123"
  }]
}
```

**NoneBot (`config.yaml`):**
```yaml
adapters:
  - name: OneBot V11
    api_root: http://127.0.0.1:3000
    access_token: "my-secret-token-123"
    websocket:
      url: ws://127.0.0.1:3001
      access_token: "my-secret-token-123"
```

#### 示例 3：远程连接

**NapCatQQ (`onebot11.json`):**
```json
{
  "websocketServers": [{
    "enable": true,
    "host": "0.0.0.0",  // 监听所有接口，允许远程连接
    "port": 3001,
    "token": "secure-token-456"
  }]
}
```

**NoneBot (`config.yaml`):**
```yaml
adapters:
  - name: OneBot V11
    api_root: http://192.168.1.100:3000  # 远程服务器 IP
    access_token: "secure-token-456"
    websocket:
      url: ws://192.168.1.100:3001  # 远程服务器 IP
      access_token: "secure-token-456"
```

## 验证配置

### 1. 检查 NapCatQQ 是否启动 WebSocket 服务器

启动 NapCatQQ 后，查看日志应该能看到：
```
WebSocket Server listening on 0.0.0.0:3001
```

### 2. 检查 NoneBot 连接状态

启动 NoneBot 后，查看日志应该能看到：
```
设置环境变量 ONEBOT_WS_URL=ws://127.0.0.1:3001
OneBot V11适配器已注册
  HTTP API: http://127.0.0.1:3000
  WebSocket: ws://127.0.0.1:3001
  连接模式: 正向 WebSocket（Bot 连接到 NapCat）
```

### 3. 测试连接

发送一条消息给机器人，如果配置正确，应该能看到：
- NoneBot 接收到消息
- 消息日志被记录
- 插件能够正常响应

## 常见问题

### 问题 1：连接失败

**症状：** NoneBot 无法连接到 NapCatQQ

**解决方法：**
1. 检查 NapCatQQ 的 `enable` 是否为 `true`
2. 检查端口是否一致（NapCatQQ 的 `port` 和 NoneBot 的 `url` 端口）
3. 检查防火墙是否阻止了连接
4. 检查 NapCatQQ 是否正在运行

### 问题 2：鉴权失败

**症状：** 连接被拒绝，提示 token 错误

**解决方法：**
1. 确保 NapCatQQ 的 `token` 和 NoneBot 的 `websocket.access_token` 完全一致
2. 如果不需要鉴权，两边都设置为空字符串 `""`

### 问题 3：只能本地连接

**症状：** 本地可以连接，但远程无法连接

**解决方法：**
1. 将 NapCatQQ 的 `host` 设置为 `0.0.0.0`（监听所有接口）
2. 确保防火墙开放了相应端口
3. 检查网络路由配置

### 问题 4：消息收不到

**症状：** 连接成功但收不到消息

**解决方法：**
1. 检查 `reportSelfMessage` 设置（如果设置为 `false`，机器人自己发送的消息不会上报）
2. 检查消息日志是否启用
3. 查看 NoneBot 的日志是否有错误信息

## 连接模式说明

### 正向 WebSocket（当前使用）

- **模式**：Bot（NoneBot）主动连接到 NapCatQQ
- **优点**：Bot 可以部署在任何地方，只要能够访问 NapCatQQ 的 WebSocket 服务器
- **配置**：NapCatQQ 作为服务器，NoneBot 作为客户端

### 反向 WebSocket（可选）

如果需要使用反向 WebSocket（NapCatQQ 连接到 NoneBot），需要：
1. 配置 `websocketClients` 而不是 `websocketServers`
2. NoneBot 需要启动 WebSocket 服务器
3. 配置 NapCatQQ 连接到 NoneBot

## 相关文件

- NapCatQQ 配置：`napcat/config/onebot11.json`
- NoneBot 配置：`configs/config.yaml`
- 适配器代码：`src/adapters/onebot_v11.py`

