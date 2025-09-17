# AI 代码库领航员 Docker 部署指南

本目录包含了 AI 代码库领航员项目的 Docker 部署配置，支持同时运行前端和后端服务。

## 🏗️ 架构说明

- **前端**: React + Vite 应用，构建后通过 Nginx 提供静态文件服务
- **后端**: FastAPI 应用，使用 uv 管理 Python 依赖，通过 uvicorn 运行
- **反向代理**: Nginx 作为反向代理，处理前端静态文件和后端 API 路由
- **进程管理**: Supervisor 管理 Nginx 和后端服务进程

## 📁 文件结构

```
docker/
├── README.md           # 本文档
├── Dockerfile          # 多阶段构建配置
├── docker-compose.yml  # Docker Compose 配置
├── nginx.conf          # Nginx 配置文件
├── supervisord.conf    # Supervisor 配置文件
├── build.sh           # 构建脚本
└── run.sh             # 运行脚本
```

## 🚀 快速开始

### 1. 准备环境

确保已安装：
- Docker (>= 20.10)
- Docker Compose (>= 2.0)

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑环境变量文件
vim .env
```

重要配置项：
- `GITHUB_TOKEN`: GitHub API 令牌
- `OPENAI_API_KEY`: OpenAI API 密钥
- `DB_*`: 数据库连接配置

### 3. 构建和运行

#### 方式一：使用脚本（推荐）

```bash
# 构建镜像
chmod +x docker/build.sh
./docker/build.sh

# 启动服务
chmod +x docker/run.sh
./docker/run.sh
```

#### 方式二：使用 Docker Compose

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

### 4. 访问服务

- **前端应用**: http://localhost
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost/health

## 🔧 配置说明

### 端口映射

- `80`: Nginx (前端 + API 代理)
- `8000`: 后端 FastAPI 服务

### 数据持久化

以下目录会被持久化：
- `./data/repos`: Git 仓库存储
- `./data/results`: 分析结果存储
- `./data/vectorstores`: 向量数据库存储

### 环境变量

主要环境变量说明：

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `APP_HOST` | 后端服务监听地址 | `0.0.0.0` |
| `APP_PORT` | 后端服务端口 | `8000` |
| `DB_HOST` | 数据库地址 | `127.0.0.1` |
| `DB_PORT` | 数据库端口 | `3306` |
| `DB_NAME` | 数据库名称 | `code_analysis` |
| `GITHUB_TOKEN` | GitHub API 令牌 | - |
| `OPENAI_API_KEY` | OpenAI API 密钥 | - |

## 🛠️ 常用命令

```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 重启服务
docker-compose restart

# 停止服务
docker-compose down

# 重新构建并启动
docker-compose up --build -d

# 进入容器
docker-compose exec app bash

# 查看资源使用情况
docker stats
```

## 🐛 故障排除

### 1. 服务启动失败

```bash
# 查看详细日志
docker-compose logs app

# 检查配置文件
docker-compose config
```

### 2. 前端无法访问

- 检查 Nginx 配置是否正确
- 确认前端构建是否成功
- 查看 Nginx 日志：`docker-compose logs app | grep nginx`

### 3. 后端 API 无法访问

- 检查后端服务是否正常启动
- 确认环境变量配置是否正确
- 查看后端日志：`docker-compose logs app | grep backend`

### 4. 数据库连接失败

- 检查数据库配置是否正确
- 确认数据库服务是否可访问
- 测试数据库连接：访问 http://localhost/database/test

## 📊 监控和日志

### 健康检查

服务提供健康检查端点：
- http://localhost/health
- http://localhost/database/test

### 日志位置

容器内日志位置：
- Supervisor: `/var/log/supervisor/`
- Nginx: `/var/log/supervisor/nginx.*.log`
- 后端: `/var/log/supervisor/backend.*.log`

### 性能监控

```bash
# 查看容器资源使用
docker stats

# 查看容器详细信息
docker-compose exec app top
```

## 🔒 安全注意事项

1. **环境变量**: 不要将包含敏感信息的 `.env` 文件提交到版本控制
2. **网络安全**: 生产环境建议使用 HTTPS
3. **数据库安全**: 使用强密码，限制数据库访问权限
4. **API 安全**: 配置适当的 CORS 策略

## 📈 生产部署建议

1. **使用外部数据库**: 不建议在容器中运行数据库
2. **配置 HTTPS**: 使用 Let's Encrypt 或其他 SSL 证书
3. **设置资源限制**: 在 docker-compose.yml 中配置内存和 CPU 限制
4. **备份策略**: 定期备份数据目录和数据库
5. **监控告警**: 配置服务监控和告警机制
