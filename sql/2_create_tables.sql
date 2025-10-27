-- =====================================================
-- 2_create_tables.sql
-- 创建所有表结构
-- 数据库名称：code_reader
-- =====================================================

USE code_reader;

-- 1. 创建 repositories 表
CREATE TABLE IF NOT EXISTS repositories (
  id INT AUTO_INCREMENT PRIMARY KEY COMMENT '仓库ID',
  user_id INT NOT NULL COMMENT '上传用户ID',
  name VARCHAR(255) NOT NULL COMMENT '仓库名称',
  full_name VARCHAR(255) NULL COMMENT '完整仓库名',
  local_path VARCHAR(1024) NOT NULL COMMENT '本地仓库路径',
  status TINYINT DEFAULT 1 COMMENT '状态：1=存在，0=已删除',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

  INDEX idx_user_id (user_id),
  INDEX idx_name (name),
  INDEX idx_status (status),
  INDEX idx_created_at (created_at),
  INDEX idx_user_status (user_id, status),
  UNIQUE KEY uk_local_path (local_path(255))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='本地代码仓库信息表';

-- 2. 创建 analysis_tasks 表
CREATE TABLE IF NOT EXISTS analysis_tasks (
  id INT AUTO_INCREMENT PRIMARY KEY COMMENT '任务ID',
  repository_id INT NOT NULL COMMENT '仓库ID',
  total_files INT DEFAULT 0 COMMENT '总文件数',
  successful_files INT DEFAULT 0 COMMENT '成功分析文件数',
  failed_files INT DEFAULT 0 COMMENT '失败文件数',
  code_lines INT DEFAULT 0 COMMENT '代码行数',
  module_count INT DEFAULT 0 COMMENT '模块数量',
  status VARCHAR(32) DEFAULT 'pending' COMMENT '任务状态：pending/running/completed/failed',
  task_index VARCHAR(255) NULL COMMENT '任务索引',
  start_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '开始时间',
  end_time DATETIME NULL COMMENT '结束时间',

  INDEX idx_repository_id (repository_id),
  INDEX idx_status (status),
  INDEX idx_start_time (start_time),
  INDEX idx_status_repo (status, repository_id),
  INDEX idx_task_index (task_index),

  CONSTRAINT fk_task_repo FOREIGN KEY (repository_id)
    REFERENCES repositories(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='代码分析任务表';

-- 3. 创建 file_analyses 表
CREATE TABLE IF NOT EXISTS file_analyses (
  id INT AUTO_INCREMENT PRIMARY KEY COMMENT '文件分析ID',
  task_id INT NOT NULL COMMENT '任务ID',
  file_path VARCHAR(1024) NOT NULL COMMENT '文件路径',
  language VARCHAR(64) NULL COMMENT '编程语言',
  analysis_version VARCHAR(32) DEFAULT '1.0' COMMENT '分析版本',
  status VARCHAR(32) DEFAULT 'pending' COMMENT '分析状态：pending/success/failed',
  code_lines INT DEFAULT 0 COMMENT '代码行数',
  code_content LONGTEXT NULL COMMENT '代码内容',
  file_analysis LONGTEXT NULL COMMENT '文件分析结果',
  dependencies TEXT NULL COMMENT '依赖模块列表',
  analysis_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '分析时间',
  error_message TEXT NULL COMMENT '错误信息',

  INDEX idx_task_id (task_id),
  INDEX idx_file_path (file_path(255)),
  INDEX idx_language (language),
  INDEX idx_analysis_version (analysis_version),
  INDEX idx_status (status),
  INDEX idx_code_lines (code_lines),
  INDEX idx_analysis_timestamp (analysis_timestamp),
  INDEX idx_task_status (task_id, status),

  CONSTRAINT fk_file_task FOREIGN KEY (task_id)
    REFERENCES analysis_tasks(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文件分析结果表';

-- 4. 创建 analysis_items 表
CREATE TABLE IF NOT EXISTS analysis_items (
  id INT AUTO_INCREMENT PRIMARY KEY COMMENT '分析项ID',
  file_analysis_id INT NOT NULL COMMENT '文件分析ID',
  title VARCHAR(512) NOT NULL COMMENT '标题',
  description TEXT NULL COMMENT '描述',
  target_type VARCHAR(32) NULL COMMENT '目标类型：file/class/function',
  target_name VARCHAR(255) NULL COMMENT '目标名称（类名/函数名）',
  source VARCHAR(1024) NULL COMMENT '源码位置',
  language VARCHAR(64) NULL COMMENT '编程语言',
  code LONGTEXT NULL COMMENT '代码片段',
  start_line INT NULL COMMENT '起始行号',
  end_line INT NULL COMMENT '结束行号',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '修改时间',

  INDEX idx_file_analysis_id (file_analysis_id),
  INDEX idx_title (title(255)),
  INDEX idx_target_type (target_type),
  INDEX idx_target_name (target_name),
  INDEX idx_language (language),
  INDEX idx_start_line (start_line),
  INDEX idx_created_at (created_at),
  INDEX idx_updated_at (updated_at),
  INDEX idx_target_type_name (target_type, target_name),

  CONSTRAINT fk_item_file FOREIGN KEY (file_analysis_id)
    REFERENCES file_analyses(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='代码分析项表';

-- 5. 创建 task_readmes 表
CREATE TABLE IF NOT EXISTS task_readmes (
  id INT AUTO_INCREMENT PRIMARY KEY COMMENT 'readme仓库ID',
  task_id INT NOT NULL COMMENT '任务ID',
  content LONGTEXT NOT NULL COMMENT 'readme的完整内容',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  rendered_content LONGTEXT NULL COMMENT '渲染后的内容',
  INDEX idx_task_id (task_id),
  INDEX idx_created_at (created_at),
  INDEX idx_updated_at (updated_at),

  CONSTRAINT fk_readme_task FOREIGN KEY (task_id)
    REFERENCES analysis_tasks(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='任务生成的README表';

-- 显示创建结果
SELECT 'Tables created successfully' AS status;
SHOW TABLES;

-- 显示表结构
DESCRIBE repositories;
DESCRIBE analysis_tasks;
DESCRIBE file_analyses;
DESCRIBE analysis_items;
DESCRIBE task_readmes;