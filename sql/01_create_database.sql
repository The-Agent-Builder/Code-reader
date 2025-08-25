-- =====================================================
-- 01_create_database.sql
-- 创建数据库和用户（可选）
-- =====================================================

-- 1. 创建数据库
CREATE DATABASE IF NOT EXISTS code_analysis
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_general_ci;

-- 2. 创建专用用户（可选，如果不想使用 root）
-- 取消注释以下行来创建专用用户
/*
CREATE USER IF NOT EXISTS 'code_analysis_user'@'localhost' IDENTIFIED BY 'your_secure_password';
CREATE USER IF NOT EXISTS 'code_analysis_user'@'%' IDENTIFIED BY 'your_secure_password';

-- 授予权限
GRANT ALL PRIVILEGES ON code_analysis.* TO 'code_analysis_user'@'localhost';
GRANT ALL PRIVILEGES ON code_analysis.* TO 'code_analysis_user'@'%';

-- 刷新权限
FLUSH PRIVILEGES;
*/

-- 3. 使用数据库
USE code_analysis;

-- 4. 显示创建结果
SELECT 'Database code_analysis created successfully' AS status;
SHOW DATABASES LIKE 'code_analysis';
