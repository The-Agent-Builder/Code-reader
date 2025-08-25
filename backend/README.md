# AI 代码库领航员 - 后端 API 服务

智能代码库分析和导航系统的后端 API 服务，基于 FastAPI 构建。

## 功能特性

- ✅ 健康检查接口
- 📚 自动生成的 API 文档 (Swagger UI)
- 🔧 环境变量配置
- 🌐 CORS 跨域支持
- 🚀 热重载开发模式

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

确保项目根目录的 `.env` 文件包含必要的配置：

```bash
# 应用配置
APP_HOST=0.0.0.0
APP_PORT=8000

# 数据库配置
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=code_analysis
DB_USER=root
DB_PASSWORD=123456
```

### 3. 启动服务

```bash
# 方式1: 直接运行主文件
python main.py

# 方式2: 使用启动脚本
python run.py

# 方式3: 使用uvicorn命令
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## API 文档

启动服务后，可以通过以下地址访问 API 文档：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## API 接口

### 健康检查

```http
GET /health
```

返回系统运行状态和基本信息。

**响应示例:**

```json
{
  "status": "healthy",
  "message": "AI 代码库领航员后端服务运行正常",
  "timestamp": "2024-01-01T12:00:00.000000",
  "version": "1.0.0",
  "service": "AI Codebase Navigator API"
}
```

### 数据库连接测试

```http
GET /database/test
```

测试数据库连接状态。

**成功响应示例:**

```json
{
  "status": "success",
  "message": "数据库连接正常",
  "connection_test": 1,
  "database_version": "8.0.33",
  "database_name": "code_analysis",
  "database_url": "mysql+pymysql://root@127.0.0.1:3306/code_analysis",
  "pool_size": 5,
  "max_overflow": 10
}
```

**失败响应示例:**

```json
{
  "status": "error",
  "message": "数据库连接失败",
  "error": "Connection refused",
  "database_url": "mysql+pymysql://root@127.0.0.1:3306/code_analysis"
}
```

### 数据库详细信息

```http
GET /database/info
```

获取数据库详细信息，包括版本、用户、表信息等。

**响应示例:**

```json
{
  "status": "success",
  "message": "数据库信息获取成功",
  "database_info": {
    "version": "8.0.33",
    "current_user": "root@localhost",
    "current_database": "code_analysis",
    "connection_id": "123",
    "charset": "utf8mb4",
    "collation": "utf8mb4_0900_ai_ci",
    "timezone": "SYSTEM",
    "tables": ["users", "projects", "analysis_results"],
    "table_count": 3
  }
}
```

### 获取仓库文件列表

```http
GET /api/repository/files/{task_id}
```

根据任务 ID 获取仓库的文件列表信息。

**路径参数:**

- `task_id`: 任务 ID

**查询参数:**

- `include_statistics`: 是否包含统计信息 (默认: true)
- `status_filter`: 按分析状态过滤 (success, failed)
- `language_filter`: 按编程语言过滤
- `limit`: 限制返回文件数量 (1-1000)
- `offset`: 跳过的文件数量 (默认: 0)

**成功响应示例:**

```json
{
  "status": "success",
  "message": "文件列表获取成功",
  "task_id": "task_123",
  "total_files": 150,
  "filtered_files": 150,
  "returned_files": 50,
  "files": [
    {
      "id": 1,
      "task_id": "task_123",
      "file_path": "src/main.py",
      "file_name": "main.py",
      "file_type": "py",
      "language": "python",
      "analysis_status": "success",
      "analysis_timestamp": "2024-01-01T12:00:00.000000",
      "created_at": "2024-01-01T10:00:00.000000",
      "updated_at": "2024-01-01T12:00:00.000000"
    }
  ],
  "statistics": {
    "by_language": { "python": 50, "javascript": 30 },
    "by_status": { "success": 70, "failed": 10 },
    "by_file_type": { "py": 50, "js": 30 },
    "total_size": 0
  },
  "pagination": {
    "limit": 50,
    "offset": 0,
    "has_more": true
  }
}
```

### 获取文件分析项详细内容

```http
GET /api/repository/analysis-items/{file_analysis_id}
```

根据文件分析 ID 获取该文件的所有分析项详细内容。

**路径参数:**

- `file_analysis_id`: 文件分析 ID

**查询参数:**

- `include_statistics`: 是否包含统计信息 (默认: true)
- `language_filter`: 按编程语言过滤
- `has_code_only`: 仅返回包含代码的分析项 (默认: false)
- `limit`: 限制返回分析项数量 (1-1000)
- `offset`: 跳过的分析项数量 (默认: 0)

**成功响应示例:**

```json
{
  "status": "success",
  "message": "分析项列表获取成功",
  "file_analysis_id": 123,
  "total_items": 25,
  "filtered_items": 25,
  "returned_items": 10,
  "items": [
    {
      "id": 1,
      "file_analysis_id": 123,
      "search_target_id": 5,
      "title": "函数定义: calculate_sum",
      "description": "计算两个数字的和",
      "source": "src/utils.py",
      "language": "python",
      "code": "def calculate_sum(a, b):\n    return a + b",
      "start_line": 10,
      "end_line": 11,
      "created_at": "2024-01-01T12:00:00.000000"
    }
  ],
  "statistics": {
    "by_language": { "python": 20, "javascript": 5 },
    "by_search_target": { "5": 15, "none": 10 },
    "total_code_lines": 150,
    "has_code_items": 20,
    "has_description_items": 22
  },
  "pagination": {
    "limit": 10,
    "offset": 0,
    "has_more": true
  }
}
```

**404 响应示例:**

```json
{
  "status": "success",
  "message": "未找到file_analysis_id为 123 的分析项记录",
  "file_analysis_id": 123,
  "total_items": 0,
  "items": [],
  "statistics": {
    "by_language": {},
    "by_search_target": {},
    "total_code_lines": 0,
    "has_code_items": 0,
    "has_description_items": 0
  }
}
```

### 查询仓库信息

```http
GET /api/repository/repositories?name={name}
```

根据仓库名称查询仓库信息，支持模糊匹配和精确匹配。

**查询参数:**

- `name`: 仓库名称（必填）
- `exact_match`: 是否精确匹配 (默认: false)
- `include_statistics`: 是否包含统计信息 (默认: true)
- `include_tasks`: 是否包含分析任务信息 (默认: true)
- `limit`: 限制返回仓库数量 (1-100)
- `offset`: 跳过的仓库数量 (默认: 0)

**模糊匹配成功响应示例:**

```json
{
  "status": "success",
  "message": "仓库列表获取成功",
  "search_name": "test",
  "total_repositories": 3,
  "filtered_repositories": 3,
  "returned_repositories": 3,
  "repositories": [
    {
      "id": 1,
      "name": "test-project",
      "full_name": "user/test-project",
      "url": "https://github.com/user/test-project",
      "description": "A test project for demonstration",
      "language": "python",
      "created_at": "2024-01-01T10:00:00.000000",
      "updated_at": "2024-01-01T12:00:00.000000",
      "total_tasks": 3,
      "tasks": [
        {
          "id": 8,
          "repository_id": 1,
          "status": "completed",
          "start_time": "2024-01-01T08:00:00.000000",
          "end_time": "2024-01-01T08:25:00.000000",
          "total_files": 120,
          "successful_files": 118,
          "failed_files": 2,
          "analysis_config": {
            "mode": "quick"
          }
        },
        {
          "id": 10,
          "repository_id": 1,
          "status": "completed",
          "start_time": "2024-01-01T10:00:00.000000",
          "end_time": "2024-01-01T10:30:00.000000",
          "total_files": 150,
          "successful_files": 145,
          "failed_files": 5,
          "analysis_config": {
            "mode": "full"
          }
        },
        {
          "id": 12,
          "repository_id": 1,
          "status": "running",
          "start_time": "2024-01-01T11:00:00.000000",
          "end_time": null,
          "total_files": 200,
          "successful_files": 180,
          "failed_files": 0,
          "analysis_config": null
        }
      ]
    }
  ],
  "statistics": {
    "by_language": { "python": 2, "javascript": 1 },
    "has_description": 3,
    "has_url": 2,
    "total_repositories": 3
  },
  "pagination": {
    "limit": 10,
    "offset": 0,
    "has_more": false
  }
}
```

**精确匹配成功响应示例:**

```json
{
  "status": "success",
  "message": "仓库信息获取成功",
  "search_name": "test-project",
  "repository": {
    "id": 1,
    "name": "test-project",
    "full_name": "user/test-project",
    "url": "https://github.com/user/test-project",
    "description": "A test project for demonstration",
    "language": "python",
    "created_at": "2024-01-01T10:00:00.000000",
    "updated_at": "2024-01-01T12:00:00.000000",
    "total_tasks": 2,
    "tasks": [
      {
        "id": 8,
        "repository_id": 1,
        "status": "completed",
        "start_time": "2024-01-01T08:00:00.000000",
        "end_time": "2024-01-01T08:25:00.000000",
        "total_files": 120,
        "successful_files": 118,
        "failed_files": 2,
        "analysis_config": {
          "mode": "quick"
        }
      },
      {
        "id": 10,
        "repository_id": 1,
        "status": "completed",
        "start_time": "2024-01-01T10:00:00.000000",
        "end_time": "2024-01-01T10:30:00.000000",
        "total_files": 150,
        "successful_files": 145,
        "failed_files": 5,
        "analysis_config": {
          "mode": "full"
        }
      }
    ]
  }
}
```

**404 响应示例:**

```json
{
  "status": "success",
  "message": "未找到名称包含 'nonexistent' 的仓库记录",
  "search_name": "nonexistent",
  "total_repositories": 0,
  "repositories": []
}
```

**使用示例:**

```bash
# 模糊匹配查询包含"test"的仓库（包含任务信息）
GET /api/repository/repositories?name=test

# 精确匹配查询名为"my-project"的仓库（包含任务信息）
GET /api/repository/repositories?name=my-project&exact_match=true

# 查询仓库但不包含任务信息
GET /api/repository/repositories?name=test&include_tasks=false

# 分页查询，跳过前10个，获取接下来的20个
GET /api/repository/repositories?name=project&offset=10&limit=20

# 不包含统计信息和任务信息的查询
GET /api/repository/repositories?name=test&include_statistics=false&include_tasks=false
```

### 获取仓库分析任务

```http
GET /api/repository/analysis-tasks/{repository_id}
```

根据仓库 ID 获取该仓库的所有分析任务信息。

**路径参数:**

- `repository_id`: 仓库 ID

**查询参数:**

- `order_by`: 排序字段 (默认: start_time)
  - 可选值: `start_time`, `end_time`, `status`, `total_files`, `id`
- `order_direction`: 排序方向 (默认: asc)
  - 可选值: `asc`, `desc`

**排序规则:**

- 默认按 `start_time` 升序排列
- 当选择 `end_time` 排序时，NULL 值（运行中任务）会排在最后（ASC）或最前（DESC）
- 支持按任务状态、文件数量等字段排序

**成功响应示例:**

```json
{
  "status": "success",
  "message": "分析任务列表获取成功",
  "repository_id": 1,
  "total_tasks": 5,
  "tasks": [
    {
      "id": 8,
      "repository_id": 1,
      "status": "completed",
      "start_time": "2024-01-01T08:00:00.000000",
      "end_time": "2024-01-01T08:25:00.000000",
      "total_files": 120,
      "successful_files": 118,
      "failed_files": 2,
      "analysis_config": {
        "mode": "quick",
        "include_tests": false
      }
    },
    {
      "id": 10,
      "repository_id": 1,
      "status": "completed",
      "start_time": "2024-01-01T10:00:00.000000",
      "end_time": "2024-01-01T10:30:00.000000",
      "total_files": 150,
      "successful_files": 145,
      "failed_files": 5,
      "analysis_config": {
        "mode": "full",
        "include_tests": true
      }
    },
    {
      "id": 9,
      "repository_id": 1,
      "status": "running",
      "start_time": "2024-01-01T11:00:00.000000",
      "end_time": null,
      "total_files": 200,
      "successful_files": 180,
      "failed_files": 0,
      "analysis_config": null
    }
  ],
  "statistics": {
    "by_status": {
      "completed": 3,
      "running": 1,
      "failed": 1
    },
    "total_files": 750,
    "total_successful_files": 720,
    "total_failed_files": 30,
    "average_success_rate": 96.0,
    "latest_task": {
      "id": 9,
      "status": "running",
      "start_time": "2024-01-01T11:00:00.000000",
      "end_time": null
    },
    "running_tasks": 1
  }
}
```

**404 响应示例:**

```json
{
  "status": "success",
  "message": "未找到repository_id为 999 的分析任务记录",
  "repository_id": 999,
  "total_tasks": 0,
  "tasks": [],
  "statistics": {
    "by_status": {},
    "total_files": 0,
    "total_successful_files": 0,
    "total_failed_files": 0,
    "average_success_rate": 0,
    "latest_task": null,
    "running_tasks": 0
  }
}
```

**使用示例:**

```bash
# 默认排序（按start_time升序）
GET /api/repository/analysis-tasks/1

# 按结束时间升序排序（NULL值排在最后）
GET /api/repository/analysis-tasks/1?order_by=end_time&order_direction=asc

# 按结束时间降序排序（NULL值排在最前）
GET /api/repository/analysis-tasks/1?order_by=end_time&order_direction=desc

# 按状态排序
GET /api/repository/analysis-tasks/1?order_by=status&order_direction=asc

# 按文件数量降序排序
GET /api/repository/analysis-tasks/1?order_by=total_files&order_direction=desc
```

### 根路径

```http
GET /
```

返回 API 服务的基本信息和文档链接。

## 项目结构

```
backend/
├── main.py              # 主应用文件
├── config.py            # 配置文件
├── database.py          # 数据库连接模块
├── models.py            # 数据库模型定义
├── services.py          # 业务服务层
├── routers.py           # API路由定义
├── run.py               # 启动脚本
├── requirements.txt     # 依赖包列表
└── README.md           # 项目说明
```

## 开发说明

- 使用 FastAPI 框架构建 RESTful API
- 支持自动生成 OpenAPI 文档
- 配置了 CORS 中间件支持跨域请求
- 使用环境变量进行配置管理
- 开发模式下支持热重载

## 下一步计划

- [x] 数据库连接和测试接口
- [x] 数据库模型定义
- [x] 仓库文件列表接口
- [x] 文件分析项详细内容接口
- [x] 仓库信息查询接口
- [x] 分析任务查询接口
- [ ] 用户认证和授权
- [ ] 项目管理接口
- [ ] 文件上传和处理
- [ ] 搜索和查询接口
