# MySQL 数据库脚本说明

本目录包含了代码分析系统所需的 MySQL 数据库脚本。

## 📁 文件说明

### 核心脚本（按顺序执行）

1. **01_create_database.sql** - 创建数据库和用户

   - 创建 `code_analysis` 数据库
   - 可选：创建专用用户和权限设置
   - 设置字符集为 utf8mb4

2. **02_create_tables.sql** - 创建表结构

   - repositories（仓库表）
   - analysis_tasks（分析任务表）
   - file_analyses（文件分析表）
   - search_targets（检索目标表）
   - analysis_items（分析项表）

3. **03_create_indexes.sql** - 创建性能优化索引
   - 基础索引和复合索引
   - 全文索引（用于代码搜索）
   - 性能优化索引

### 辅助脚本

4. **04_sample_queries.sql** - 常用查询示例

   - 统计查询
   - 性能分析
   - 错误分析
   - 代码搜索

5. **99_cleanup.sql** - 清理和重置脚本
   - 清空表数据
   - 删除表结构
   - 删除数据库（谨慎使用）

## 🚀 安装步骤

### 方法一：逐个执行（推荐）

```bash
# 1. 登录 MySQL
mysql -u root -p

# 2. 按顺序执行脚本
source /path/to/sql/01_create_database.sql
source /path/to/sql/02_create_tables.sql

```

### 方法二：命令行执行

```bash
# 执行单个脚本
mysql -u root -p < sql/01_create_database.sql
mysql -u root -p < sql/02_create_tables.sql

# 或者一次性执行所有核心脚本
cat sql/01_create_database.sql sql/02_create_tables.sql sql | mysql -u root -p
```

### 方法三：使用 MySQL Workbench

1. 打开 MySQL Workbench
2. 连接到 MySQL 服务器
3. 依次打开并执行脚本文件

## 📊 数据库表结构详细说明

### 1. repositories（仓库表）

存储代码仓库的基本信息和元数据。

| 字段名        | 数据类型     | 约束                                                  | 说明                                                |
| ------------- | ------------ | ----------------------------------------------------- | --------------------------------------------------- |
| `id`          | INT          | PRIMARY KEY, AUTO_INCREMENT                           | 仓库唯一标识符，自动递增                            |
| `name`        | VARCHAR(255) | NOT NULL                                              | 仓库名称，如 "my-project"                           |
| `full_name`   | VARCHAR(255) | NULL                                                  | 完整仓库名，格式为 "组织/仓库"，如 "github/octocat" |
| `url`         | VARCHAR(512) | NULL                                                  | 仓库的完整 URL 地址，支持 Git、HTTP 等协议          |
| `description` | TEXT         | NULL                                                  | 仓库的详细描述信息                                  |
| `language`    | VARCHAR(64)  | NULL                                                  | 仓库的主要编程语言，如 "Python"、"JavaScript"       |
| `created_at`  | DATETIME     | DEFAULT CURRENT_TIMESTAMP                             | 记录创建时间，自动设置为当前时间                    |
| `updated_at`  | DATETIME     | DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP | 记录更新时间，修改时自动更新                        |

**索引说明：**

- `idx_name`: 仓库名称索引，用于快速查找
- `idx_full_name`: 完整名称索引，支持组织/仓库查询
- `idx_language`: 编程语言索引，支持按语言筛选
- `idx_created_at`: 创建时间索引，支持时间范围查询

### 2. analysis_tasks（分析任务表）

记录每次代码分析任务的执行情况和统计信息。

| 字段名             | 数据类型    | 约束                        | 说明                                                                         |
| ------------------ | ----------- | --------------------------- | ---------------------------------------------------------------------------- |
| `id`               | INT         | PRIMARY KEY, AUTO_INCREMENT | 任务唯一标识符，自动递增                                                     |
| `repository_id`    | INT         | NOT NULL, FOREIGN KEY       | 关联的仓库 ID，引用 repositories.id                                          |
| `status`           | VARCHAR(32) | DEFAULT 'running'           | 任务状态：pending（等待）/running（运行中）/completed（完成）/failed（失败） |
| `start_time`       | DATETIME    | DEFAULT CURRENT_TIMESTAMP   | 任务开始时间，自动设置为当前时间                                             |
| `end_time`         | DATETIME    | NULL                        | 任务结束时间，完成或失败时设置                                               |
| `total_files`      | INT         | DEFAULT 0                   | 需要分析的文件总数                                                           |
| `successful_files` | INT         | DEFAULT 0                   | 成功分析的文件数量                                                           |
| `failed_files`     | INT         | DEFAULT 0                   | 分析失败的文件数量                                                           |
| `analysis_config`  | JSON        | NULL                        | 分析配置信息，存储 JSON 格式的配置参数                                       |

**索引说明：**

- `idx_repository_id`: 仓库 ID 索引，快速查找特定仓库的任务
- `idx_status`: 状态索引，支持按状态筛选任务
- `idx_start_time`: 开始时间索引，支持时间范围查询
- `idx_status_repo`: 复合索引（状态+仓库），优化常用查询

**外键约束：**

- `fk_task_repo`: 当仓库被删除时，相关任务也会被级联删除

### 3. file_analyses（文件分析表）

存储每个文件的分析结果和状态信息。

| 字段名               | 数据类型      | 约束                        | 说明                                      |
| -------------------- | ------------- | --------------------------- | ----------------------------------------- |
| `id`                 | INT           | PRIMARY KEY, AUTO_INCREMENT | 文件分析唯一标识符，自动递增              |
| `task_id`            | INT           | NOT NULL, FOREIGN KEY       | 关联的任务 ID，引用 analysis_tasks.id     |
| `file_path`          | VARCHAR(1024) | NOT NULL                    | 文件的相对路径，如 "src/main.py"          |
| `language`           | VARCHAR(64)   | NULL                        | 文件的编程语言，如 "Python"、"JavaScript" |
| `analysis_timestamp` | DATETIME      | DEFAULT CURRENT_TIMESTAMP   | 文件分析的具体时间                        |
| `status`             | VARCHAR(32)   | DEFAULT 'success'           | 分析状态：success（成功）/failed（失败）  |
| `error_message`      | TEXT          | NULL                        | 分析失败时的错误信息详情                  |

**索引说明：**

- `idx_task_id`: 任务 ID 索引，快速查找任务下的所有文件
- `idx_file_path`: 文件路径索引（前 255 字符），支持路径查询
- `idx_language`: 编程语言索引，支持按语言筛选
- `idx_status`: 状态索引，快速筛选成功/失败的文件
- `idx_analysis_timestamp`: 分析时间索引，支持时间范围查询
- `idx_task_status`: 复合索引（任务+状态），优化常用查询

**外键约束：**

- `fk_file_task`: 当任务被删除时，相关文件分析记录也会被级联删除

### 4. search_targets（检索目标表）

记录代码中的检索目标，支持文件、类、函数等不同粒度的代码元素追踪。

| 字段名              | 数据类型     | 约束                        | 说明                                                   |
| ------------------- | ------------ | --------------------------- | ------------------------------------------------------ |
| `id`                | INT          | PRIMARY KEY, AUTO_INCREMENT | 检索目标唯一标识符，自动递增                           |
| `file_analysis_id`  | INT          | NOT NULL, FOREIGN KEY       | 关联的文件分析 ID，引用 file_analyses.id               |
| `target_type`       | VARCHAR(32)  | NOT NULL                    | 目标类型：file（文件）/class（类）/function（函数）    |
| `target_name`       | VARCHAR(255) | NULL                        | 目标名称，如类名 "UserService" 或函数名 "calculate"    |
| `target_identifier` | VARCHAR(512) | NOT NULL                    | 完整的标识符，如 "com.example.UserService.getUserById" |

**索引说明：**

- `idx_file_analysis_id`: 文件分析 ID 索引，快速查找文件中的所有目标
- `idx_target_type`: 目标类型索引，支持按类型筛选
- `idx_target_name`: 目标名称索引，支持名称查询
- `idx_target_identifier`: 标识符索引（前 255 字符），支持精确查找
- `idx_file_type`: 复合索引（文件+类型），优化常用查询

**外键约束：**

- `fk_target_file`: 当文件分析记录被删除时，相关检索目标也会被级联删除

### 5. analysis_items（分析项表）

存储具体的代码分析项，包含代码片段、位置信息等详细内容。

| 字段名             | 数据类型      | 约束                        | 说明                                              |
| ------------------ | ------------- | --------------------------- | ------------------------------------------------- |
| `id`               | INT           | PRIMARY KEY, AUTO_INCREMENT | 分析项唯一标识符，自动递增                        |
| `file_analysis_id` | INT           | NOT NULL, FOREIGN KEY       | 关联的文件分析 ID，引用 file_analyses.id          |
| `search_target_id` | INT           | NULL, FOREIGN KEY           | 关联的检索目标 ID，引用 search_targets.id，可为空 |
| `title`            | VARCHAR(512)  | NOT NULL                    | 分析项标题，简要描述分析内容                      |
| `description`      | TEXT          | NULL                        | 详细描述，说明分析项的具体内容和意义              |
| `source`           | VARCHAR(1024) | NULL                        | 源码位置信息，如文件路径和行号范围                |
| `language`         | VARCHAR(64)   | NULL                        | 代码片段的编程语言                                |
| `code`             | LONGTEXT      | NULL                        | 完整的代码片段内容，支持大文本存储                |
| `start_line`       | INT           | NULL                        | 代码片段在文件中的起始行号                        |
| `end_line`         | INT           | NULL                        | 代码片段在文件中的结束行号                        |
| `created_at`       | DATETIME      | DEFAULT CURRENT_TIMESTAMP   | 分析项创建时间，自动设置为当前时间                |

**索引说明：**

- `idx_file_analysis_id`: 文件分析 ID 索引，快速查找文件的所有分析项
- `idx_search_target_id`: 检索目标 ID 索引，查找特定目标的分析项
- `idx_title`: 标题索引（前 255 字符），支持标题搜索
- `idx_language`: 编程语言索引，支持按语言筛选
- `idx_created_at`: 创建时间索引，支持时间范围查询
- `idx_file_target`: 复合索引（文件+目标），优化关联查询

**外键约束：**

- `fk_item_file`: 当文件分析记录被删除时，相关分析项也会被级联删除
- `fk_item_target`: 当检索目标被删除时，相关分析项的 search_target_id 会被设置为 NULL

## 🔗 表关系说明

### 数据流向

1. **repositories** → **analysis_tasks** → **file_analyses** → **search_targets** / **analysis_items**
2. 一个仓库可以有多个分析任务
3. 一个分析任务可以分析多个文件
4. 一个文件可以有多个检索目标和分析项
5. 检索目标和分析项之间是可选的关联关系

### 级联删除策略

- 删除仓库 → 自动删除所有相关的分析任务、文件分析、检索目标和分析项
- 删除分析任务 → 自动删除所有相关的文件分析、检索目标和分析项
- 删除文件分析 → 自动删除所有相关的检索目标和分析项
- 删除检索目标 → 相关分析项的 search_target_id 设置为 NULL（软删除）

### 数据完整性

- 所有外键关系都有相应的约束确保数据一致性
- 使用 InnoDB 存储引擎支持事务和外键约束
- 关键字段设置了 NOT NULL 约束防止空值
- 时间字段自动维护创建和更新时间

- `idx_file_analysis_id`: 文件分析 ID 索引，快速查找文件的所有分析项
- `idx_search_target_id`: 检索目标 ID 索引，查找特定目标的分析项
- `idx_title`: 标题索引（前 255 字符），支持标题搜索
- `idx_language`: 编程语言索引，支持按语言筛选
- `idx_created_at`: 创建时间索引，支持时间范围查询
- `idx_file_target`: 复合索引（文件+目标），优化关联查询

**外键约束：**

- `fk_item_file`: 当文件分析记录被删除时，相关分析项也会被级联删除
- `fk_item_target`: 当检索目标被删除时，相关分析项的 search_target_id 会被设置为 NULL

## 🔧 配置要求

### MySQL 版本要求

- MySQL 5.7+ （推荐 8.0+）
- 支持 JSON 数据类型
- 支持 InnoDB 全文索引

### 字符集设置

- 数据库：utf8mb4
- 排序规则：utf8mb4_general_ci
- 支持 emoji 和多语言字符

### 存储引擎

- 使用 InnoDB 引擎
- 支持事务和外键约束
- 支持全文索引

## 🔍 验证安装

执行以下查询验证安装是否成功：

```sql
-- 检查数据库
SHOW DATABASES LIKE 'code_analysis';

-- 检查表
USE code_analysis;
SHOW TABLES;

-- 检查表结构
DESCRIBE repositories;
DESCRIBE analysis_tasks;
DESCRIBE file_analyses;
DESCRIBE search_targets;
DESCRIBE analysis_items;

-- 检查索引
SHOW INDEX FROM analysis_items;
```

## ⚠️ 注意事项

1. **备份数据**：在执行清理脚本前请备份重要数据
2. **权限设置**：确保数据库用户有足够的权限
3. **字符集**：使用 utf8mb4 避免中文和 emoji 乱码
4. **索引优化**：根据实际查询需求调整索引
5. **存储空间**：代码片段可能较大，注意磁盘空间

## 🛠️ 故障排除

### 常见问题

1. **字符集问题**

   ```sql
   -- 检查字符集
   SHOW VARIABLES LIKE 'character_set%';
   ```

2. **权限问题**

   ```sql
   -- 检查用户权限
   SHOW GRANTS FOR CURRENT_USER();
   ```

3. **外键约束错误**
   ```sql
   -- 临时禁用外键检查
   SET FOREIGN_KEY_CHECKS = 0;
   -- 执行操作后重新启用
   SET FOREIGN_KEY_CHECKS = 1;
   ```

## 📈 性能优化建议

1. **定期分析表**

   ```sql
   ANALYZE TABLE repositories, analysis_tasks, file_analyses, search_targets, analysis_items;
   ```

2. **监控慢查询**

   ```sql
   -- 启用慢查询日志
   SET GLOBAL slow_query_log = 'ON';
   SET GLOBAL long_query_time = 2;
   ```

## 📞 支持

如果在安装过程中遇到问题，请检查：

1. MySQL 服务是否正常运行
2. 用户权限是否足够
3. 字符集设置是否正确
4. 磁盘空间是否充足
