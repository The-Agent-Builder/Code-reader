-- 更新 repositories 表结构以包含 repo_info.json 的全部内容
-- 2025-08-16: 扩展表结构以支持更详细的仓库信息

USE code_analysis;

-- 备份现有数据
CREATE TABLE repositories_backup AS SELECT * FROM repositories;

-- 临时禁用外键检查
SET FOREIGN_KEY_CHECKS = 0;

-- 删除现有表
DROP TABLE repositories;

-- 创建新的 repositories 表
CREATE TABLE repositories (
    -- 基本标识信息
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL COMMENT '仓库名称',
    full_name VARCHAR(255) NOT NULL COMMENT '完整仓库名称 (owner/repo)',
    url VARCHAR(512) NOT NULL COMMENT '仓库 URL',
    clone_url VARCHAR(512) COMMENT 'Git clone URL',
    ssh_url VARCHAR(512) COMMENT 'SSH clone URL',
    
    -- 描述信息
    description TEXT COMMENT '仓库描述',
    readme LONGTEXT COMMENT 'README 内容',
    
    -- 主要编程语言
    primary_language VARCHAR(64) COMMENT '主要编程语言',
    language VARCHAR(64) COMMENT '语言字段 (兼容旧版)',
    
    -- 语言分布 (JSON格式存储)
    languages JSON COMMENT '语言分布统计 {"Python": {"bytes": 542033, "percentage": 71.08}}',
    
    -- 社交统计
    stars VARCHAR(20) COMMENT '星标数 (可能包含k等单位)',
    stargazers_count INT COMMENT '精确星标数',
    forks VARCHAR(20) COMMENT '分叉数 (可能包含k等单位)', 
    forks_count INT COMMENT '精确分叉数',
    watchers VARCHAR(20) COMMENT '观察者数 (可能包含k等单位)',
    watchers_count INT COMMENT '精确观察者数',
    open_issues_count INT COMMENT '开放问题数',
    
    -- 仓库属性
    size INT COMMENT '仓库大小 (KB)',
    default_branch VARCHAR(64) COMMENT '默认分支',
    license VARCHAR(255) COMMENT '许可证',
    
    -- 状态标志
    archived BOOLEAN DEFAULT FALSE COMMENT '是否已归档',
    disabled BOOLEAN DEFAULT FALSE COMMENT '是否已禁用',
    private BOOLEAN DEFAULT FALSE COMMENT '是否私有',
    fork BOOLEAN DEFAULT FALSE COMMENT '是否为分叉',
    
    -- 主题标签 (JSON数组格式)
    topics JSON COMMENT '仓库主题标签数组',
    
    -- 时间信息
    repo_created_at DATETIME COMMENT '仓库创建时间',
    repo_updated_at DATETIME COMMENT '仓库最后更新时间',
    last_updated VARCHAR(64) COMMENT '最后更新时间字符串',
    
    -- 数据来源
    source VARCHAR(64) DEFAULT 'GitHub API' COMMENT '数据来源',
    
    -- 系统时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '记录更新时间',
    
    -- 索引
    INDEX idx_name (name),
    INDEX idx_full_name (full_name),
    INDEX idx_primary_language (primary_language),
    INDEX idx_stargazers_count (stargazers_count),
    INDEX idx_repo_created_at (repo_created_at),
    INDEX idx_repo_updated_at (repo_updated_at),
    UNIQUE KEY uk_full_name (full_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='代码仓库信息表 - 包含详细的GitHub仓库元数据';

-- 恢复基本数据 (从备份表)
INSERT INTO repositories (
    id, name, full_name, url, description, language, created_at, updated_at
) 
SELECT 
    id, name, 
    COALESCE(full_name, name) as full_name,
    url, description, language, created_at, updated_at
FROM repositories_backup;

-- 重新启用外键检查
SET FOREIGN_KEY_CHECKS = 1;

-- 删除备份表
DROP TABLE repositories_backup;

-- 显示新表结构
DESCRIBE repositories;
