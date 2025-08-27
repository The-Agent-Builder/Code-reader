# Code Reader 数据库脚本

本目录包含 Code Reader 系统的 MySQL 数据库脚本。

## 📁 文件说明

### 1_create_database.sql

创建数据库

- 创建 `code_reader` 数据库
- 设置字符集为 utf8mb4

### 2_create_tables.sql

创建所有表结构

- 创建 `repositories` 表
- 创建 `analysis_tasks` 表
- 创建 `file_analyses` 表
- 创建 `analysis_items` 表
- 设置索引和约束

## 🚀 使用方法

### 执行脚本

```bash
# 步骤1：创建数据库
mysql -u root -p < sql/1_create_database.sql

# 步骤2：创建表结构
mysql -u root -p < sql/2_create_tables.sql

# 或者在 MySQL 客户端内执行
mysql -u root -p
source /path/to/sql/1_create_database.sql
source /path/to/sql/2_create_tables.sql
```

## 📊 表结构说明

### repositories（仓库表）

存储本地代码仓库信息

| 字段名       | 数据类型      | 约束                        | 说明                   |
| ------------ | ------------- | --------------------------- | ---------------------- |
| `id`         | INT           | PRIMARY KEY, AUTO_INCREMENT | 仓库唯一标识符         |
| `user_id`    | INT           | NOT NULL                    | 上传用户 ID            |
| `name`       | VARCHAR(255)  | NOT NULL                    | 仓库名称               |
| `full_name`  | VARCHAR(255)  | NULL                        | 完整仓库名             |
| `local_path` | VARCHAR(1024) | NOT NULL, UNIQUE            | 本地仓库路径           |
| `status`     | TINYINT       | DEFAULT 1                   | 状态：1=存在，0=已删除 |
| `created_at` | DATETIME      | DEFAULT CURRENT_TIMESTAMP   | 创建时间               |
| `updated_at` | DATETIME      | AUTO UPDATE                 | 更新时间               |

**索引：**

- `idx_user_id`: 按用户查询
- `idx_name`: 按名称查询
- `idx_status`: 按状态筛选
- `idx_created_at`: 按时间排序
- `idx_user_status`: 按用户和状态组合查询
- `uk_local_path`: 路径唯一约束

### analysis_tasks（分析任务表）

存储代码分析任务的执行情况和统计信息

| 字段名             | 数据类型    | 约束                        | 说明                                       |
| ------------------ | ----------- | --------------------------- | ------------------------------------------ |
| `id`               | INT         | PRIMARY KEY, AUTO_INCREMENT | 任务唯一标识符                             |
| `repository_id`    | INT         | NOT NULL, FOREIGN KEY       | 关联的仓库 ID                              |
| `total_files`      | INT         | DEFAULT 0                   | 总文件数                                   |
| `successful_files` | INT         | DEFAULT 0                   | 成功分析文件数                             |
| `failed_files`     | INT         | DEFAULT 0                   | 失败文件数                                 |
| `code_lines`       | INT         | DEFAULT 0                   | 代码行数                                   |
| `module_count`     | INT         | DEFAULT 0                   | 模块数量                                   |
| `status`           | VARCHAR(32) | DEFAULT 'pending'           | 任务状态：pending/running/completed/failed |
| `start_time`       | DATETIME    | DEFAULT CURRENT_TIMESTAMP   | 任务开始时间                               |
| `end_time`         | DATETIME    | NULL                        | 任务结束时间                               |

**索引：**

- `idx_repository_id`: 按仓库查询任务
- `idx_status`: 按状态筛选任务
- `idx_start_time`: 按开始时间排序
- `idx_status_repo`: 按仓库和状态组合查询

**外键约束：**

- `fk_task_repo`: 当仓库被删除时，相关任务也会被级联删除

### file_analyses（文件分析表）

存储每个文件的详细分析结果和代码内容

| 字段名               | 数据类型      | 约束                        | 说明                             |
| -------------------- | ------------- | --------------------------- | -------------------------------- |
| `id`                 | INT           | PRIMARY KEY, AUTO_INCREMENT | 文件分析唯一标识符               |
| `task_id`            | INT           | NOT NULL, FOREIGN KEY       | 关联的任务 ID                    |
| `file_path`          | VARCHAR(1024) | NOT NULL                    | 文件路径                         |
| `language`           | VARCHAR(64)   | NULL                        | 编程语言                         |
| `analysis_version`   | VARCHAR(32)   | DEFAULT '1.0'               | 分析版本                         |
| `status`             | VARCHAR(32)   | DEFAULT 'pending'           | 分析状态：pending/success/failed |
| `code_lines`         | INT           | DEFAULT 0                   | 代码总行数                       |
| `code_content`       | LONGTEXT      | NULL                        | 文件的完整代码内容               |
| `file_analysis`      | LONGTEXT      | NULL                        | AI 对文件的分析结果              |
| `dependencies`       | TEXT          | NULL                        | 依赖模块列表（如 flask、re 等）  |
| `analysis_timestamp` | DATETIME      | DEFAULT CURRENT_TIMESTAMP   | 分析时间                         |
| `error_message`      | TEXT          | NULL                        | 错误信息                         |

**索引：**

- `idx_task_id`: 按任务查询所有文件
- `idx_file_path`: 按文件路径查询
- `idx_language`: 按编程语言筛选
- `idx_analysis_version`: 按分析版本筛选
- `idx_status`: 按分析状态筛选
- `idx_code_lines`: 按代码行数排序
- `idx_analysis_timestamp`: 按分析时间排序
- `idx_task_status`: 按任务和状态组合查询

**外键约束：**

- `fk_file_task`: 当任务被删除时，相关文件分析记录也会被级联删除

### analysis_items（分析项表）

存储具体的代码分析项和代码片段

| 字段名             | 数据类型      | 约束                        | 说明                          |
| ------------------ | ------------- | --------------------------- | ----------------------------- |
| `id`               | INT           | PRIMARY KEY, AUTO_INCREMENT | 分析项唯一标识符              |
| `file_analysis_id` | INT           | NOT NULL, FOREIGN KEY       | 关联的文件分析 ID             |
| `title`            | VARCHAR(512)  | NOT NULL                    | 分析项标题                    |
| `description`      | TEXT          | NULL                        | 详细描述                      |
| `target_type`      | VARCHAR(32)   | NULL                        | 目标类型：file/class/function |
| `target_name`      | VARCHAR(255)  | NULL                        | 目标名称（类名/函数名）       |
| `language`         | VARCHAR(64)   | NULL                        | 编程语言                      |
| `source`           | VARCHAR(1024) | NULL                        | 源码位置信息                  |
| `code`             | LONGTEXT      | NULL                        | 代码片段                      |
| `start_line`       | INT           | NULL                        | 起始行号                      |
| `end_line`         | INT           | NULL                        | 结束行号                      |
| `created_at`       | DATETIME      | DEFAULT CURRENT_TIMESTAMP   | 创建时间                      |
| `updated_at`       | DATETIME      | AUTO UPDATE                 | 修改时间                      |

**索引：**

- `idx_file_analysis_id`: 按文件查询所有分析项
- `idx_title`: 按标题搜索
- `idx_target_type`: 按目标类型筛选
- `idx_target_name`: 按目标名称搜索
- `idx_language`: 按编程语言筛选
- `idx_start_line`: 按起始行号排序
- `idx_created_at`: 按创建时间排序
- `idx_updated_at`: 按修改时间排序
- `idx_target_type_name`: 按目标类型和名称组合查询

**外键约束：**

- `fk_item_file`: 当文件分析记录被删除时，相关分析项也会被级联删除

## ⚙️ 配置要求

- MySQL 5.7+ （推荐 8.0+）
- 字符集：utf8mb4
- 存储引擎：InnoDB

## 🔍 验证安装

```sql
-- 检查数据库
SHOW DATABASES LIKE 'code_reader';

-- 检查表
USE code_reader;
SHOW TABLES;

-- 检查表结构
DESCRIBE repositories;
DESCRIBE analysis_tasks;
DESCRIBE file_analyses;
DESCRIBE analysis_items;
```
