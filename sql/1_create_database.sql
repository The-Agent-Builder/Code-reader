-- =====================================================
-- 1_create_database.sql
-- 数据库名称：code_reader
-- =====================================================

-- 1. 创建数据库
CREATE DATABASE IF NOT EXISTS code_reader
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

-- 2. 使用数据库
USE code_reader;

-- 3. 显示创建结果
SELECT 'Database code_reader created successfully' AS status;
SHOW DATABASES LIKE 'code_reader';

-- 4. 显示数据库字符集信息
SELECT
    SCHEMA_NAME as 'Database',
    DEFAULT_CHARACTER_SET_NAME as 'Character Set',
    DEFAULT_COLLATION_NAME as 'Collation'
FROM information_schema.SCHEMATA
WHERE SCHEMA_NAME = 'code_reader';

