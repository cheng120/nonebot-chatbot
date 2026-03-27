-- 数据库初始化脚本
-- 兼容SQLite和MySQL语法

-- 插件配置表
CREATE TABLE IF NOT EXISTS plugin_configs (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    plugin_name VARCHAR(255) NOT NULL UNIQUE COMMENT '插件名称',
    enabled TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否启用',
    config_data TEXT COMMENT '插件配置JSON数据',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_plugin_name (plugin_name),
    INDEX idx_enabled (enabled)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='插件配置表';

-- 插件状态表
CREATE TABLE IF NOT EXISTS plugin_status (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    plugin_name VARCHAR(255) NOT NULL UNIQUE COMMENT '插件名称',
    status VARCHAR(50) NOT NULL DEFAULT 'loaded' COMMENT '插件状态: loaded, enabled, disabled, error',
    error_message TEXT COMMENT '错误信息',
    last_error_at DATETIME COMMENT '最后错误时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_plugin_name (plugin_name),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='插件状态表';

-- 消息日志表（可选，用于调试）
CREATE TABLE IF NOT EXISTS message_logs (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    message_id BIGINT COMMENT '消息ID',
    message_type VARCHAR(50) NOT NULL COMMENT '消息类型: private, group',
    user_id BIGINT COMMENT '用户ID',
    group_id BIGINT COMMENT '群组ID',
    message_content TEXT COMMENT '消息内容',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_message_type (message_type),
    INDEX idx_user_id (user_id),
    INDEX idx_group_id (group_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='消息日志表';

