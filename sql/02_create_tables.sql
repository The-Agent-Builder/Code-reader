-- =====================================================
-- 02_create_tables.sql
-- 创建所有表结构
-- =====================================================

USE code_analysis;

-- 1. 仓库表
CREATE TABLE IF NOT EXISTS repositories (
  id INT AUTO_INCREMENT PRIMARY KEY COMMENT '仓库ID',
  name VARCHAR(255) NOT NULL COMMENT '仓库名称',
  full_name VARCHAR(255) NULL COMMENT '完整仓库名 (org/repo)',
  url VARCHAR(512) NULL COMMENT '仓库URL',
  description TEXT NULL COMMENT '仓库描述',
  language VARCHAR(64) NULL COMMENT '主要编程语言',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  
  INDEX idx_name (name),
  INDEX idx_full_name (full_name),
  INDEX idx_language (language),
  INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='代码仓库信息表';

-- 2. 分析任务表
CREATE TABLE IF NOT EXISTS analysis_tasks (
  id INT AUTO_INCREMENT PRIMARY KEY COMMENT '任务ID',
  repository_id INT NOT NULL COMMENT '仓库ID',
  status VARCHAR(32) DEFAULT 'running' COMMENT '任务状态: pending/running/completed/failed',
  start_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '开始时间',
  end_time DATETIME NULL COMMENT '结束时间',
  total_files INT DEFAULT 0 COMMENT '总文件数',
  successful_files INT DEFAULT 0 COMMENT '成功分析文件数',
  failed_files INT DEFAULT 0 COMMENT '失败文件数',
  analysis_config JSON NULL COMMENT '分析配置信息',
  
  INDEX idx_repository_id (repository_id),
  INDEX idx_status (status),
  INDEX idx_start_time (start_time),
  INDEX idx_status_repo (status, repository_id),
  
  CONSTRAINT fk_task_repo FOREIGN KEY (repository_id) 
    REFERENCES repositories(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='代码分析任务表';

-- 3. 文件分析表
CREATE TABLE IF NOT EXISTS file_analyses (
  id INT AUTO_INCREMENT PRIMARY KEY COMMENT '文件分析ID',
  task_id INT NOT NULL COMMENT '任务ID',
  file_path VARCHAR(1024) NOT NULL COMMENT '文件路径',
  language VARCHAR(64) NULL COMMENT '编程语言',
  analysis_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '分析时间',
  status VARCHAR(32) DEFAULT 'success' COMMENT '分析状态: success/failed',
  error_message TEXT NULL COMMENT '错误信息',
  
  INDEX idx_task_id (task_id),
  INDEX idx_file_path (file_path(255)),
  INDEX idx_language (language),
  INDEX idx_status (status),
  INDEX idx_analysis_timestamp (analysis_timestamp),
  INDEX idx_task_status (task_id, status),
  
  CONSTRAINT fk_file_task FOREIGN KEY (task_id) 
    REFERENCES analysis_tasks(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='文件分析结果表';

-- 4. 检索目标表
CREATE TABLE IF NOT EXISTS search_targets (
  id INT AUTO_INCREMENT PRIMARY KEY COMMENT '检索目标ID',
  file_analysis_id INT NOT NULL COMMENT '文件分析ID',
  target_type VARCHAR(32) NOT NULL COMMENT '目标类型: file/class/function',
  target_name VARCHAR(255) NULL COMMENT '目标名称 (类名/函数名)',
  target_identifier VARCHAR(512) NOT NULL COMMENT '完整标识符',
  
  INDEX idx_file_analysis_id (file_analysis_id),
  INDEX idx_target_type (target_type),
  INDEX idx_target_name (target_name),
  INDEX idx_target_identifier (target_identifier(255)),
  INDEX idx_file_type (file_analysis_id, target_type),
  
  CONSTRAINT fk_target_file FOREIGN KEY (file_analysis_id) 
    REFERENCES file_analyses(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='检索目标表';

-- 5. 分析项表
CREATE TABLE IF NOT EXISTS analysis_items (
  id INT AUTO_INCREMENT PRIMARY KEY COMMENT '分析项ID',
  file_analysis_id INT NOT NULL COMMENT '文件分析ID',
  search_target_id INT NULL COMMENT '检索目标ID',
  title VARCHAR(512) NOT NULL COMMENT '标题',
  description TEXT NULL COMMENT '描述',
  source VARCHAR(1024) NULL COMMENT '源码位置',
  language VARCHAR(64) NULL COMMENT '编程语言',
  code LONGTEXT NULL COMMENT '代码片段',
  start_line INT NULL COMMENT '起始行号',
  end_line INT NULL COMMENT '结束行号',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  
  INDEX idx_file_analysis_id (file_analysis_id),
  INDEX idx_search_target_id (search_target_id),
  INDEX idx_title (title(255)),
  INDEX idx_language (language),
  INDEX idx_created_at (created_at),
  INDEX idx_file_target (file_analysis_id, search_target_id),
  
  CONSTRAINT fk_item_file FOREIGN KEY (file_analysis_id) 
    REFERENCES file_analyses(id) ON DELETE CASCADE,
  CONSTRAINT fk_item_target FOREIGN KEY (search_target_id) 
    REFERENCES search_targets(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='代码分析项表';

-- 显示创建结果
SELECT 'All tables created successfully' AS status;
SHOW TABLES;
