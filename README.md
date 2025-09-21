# GitHub 代码仓库解析工具

基于 [PocketFlow](https://github.com/The-Pocket/PocketFlow) 构建的智能 GitHub 代码仓库分析平台，使用 LLM 技术自动解析代码结构，提供现代化的 Web 界面展示分析结果。

## 🚀 功能特性

- **智能代码解析**: 使用 LLM 技术自动识别和分析函数、类的结构和功能
- **多语言支持**: 支持 Python、JavaScript、TypeScript、Java、C++、Go、Rust 等主流编程语言
- **现代化 Web 界面**: 基于 React + TypeScript 构建的响应式前端界面
- **实时分析展示**: 动态加载分析结果，支持文件浏览和代码查看
- **RAG 增强**: 可选的向量化存储，提供更准确的上下文分析
- **全文搜索**: 支持按函数名、类名、描述等多维度搜索代码元素
- **结果导出**: 支持 Markdown 和 JSON 格式导出分析结果
- **批量处理**: 支持并行处理多个文件，提高分析效率

## 📋 系统要求

- **后端**: Python 3.8+
- **前端**: Node.js 16+ 和 npm/yarn
- Git
- 足够的磁盘空间用于克隆仓库
- 稳定的网络连接

## ⚡ 快速开始

### Docker 部署（推荐）

使用 Docker 可以一键部署前后端服务，无需配置复杂的环境：

```bash
# 1. 克隆项目
git clone <your-repo-url>
cd Code-reader

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置必要的 API 密钥

# 3. 构建并启动服务
chmod +x docker/build.sh docker/run.sh
./docker/build.sh
./docker/run.sh

# 4. 访问服务
# 前端: http://localhost
# API文档: http://localhost/docs
```

### 本地开发部署

如果需要本地开发，可以分别启动前后端：

```bash
# 1. 克隆项目
git clone <your-repo-url>
cd Code-reader

# 2. 安装后端依赖
cd backend
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入你的 API 密钥

# 4. 启动后端API服务
python main.py

# 5. 在新终端启动前端
cd ../frontend
npm install
npm start
```

现在访问 http://localhost:3000 (现代界面) 开始使用！

## 🛠️ 安装部署

### 1. 克隆项目

```bash
git clone <your-repo-url>
cd GitHub_analysis
```

### 2. 后端环境配置

#### 安装 Python 依赖

```bash
cd backend
pip install -r requirements.txt
```

#### 配置环境变量

复制 `.env.example` 到 `.env` 并配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件，配置以下参数：

```env
# GitHub API 配置
GITHUB_TOKEN=your_github_token

# OpenAI API 配置
OPENAI_API_KEY=your_openai_api_key
OPENAI_BASE_URL=https://api.openai.com/v1
OpenAI_MODEL=gpt-3.5-turbo

# RAG 服务配置（可选）
RAG_BASE_URL=http://your-rag-service

# 应用配置
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=True

# 本地存储配置
LOCAL_REPO_PATH=./data/repos
RESULTS_PATH=./data/results
VECTORSTORE_PATH=./data/vectorstores
```

### 3. 前端环境配置

#### 安装 Node.js 依赖

```bash
cd frontend
npm install
# 或使用 yarn
yarn install
```

### 4. 验证配置

运行配置测试脚本验证环境变量配置是否正确：

```bash
cd backend
python test_config.py
```

如果配置正确，你会看到类似以下的输出：

```
🎉 所有测试通过! 配置正确。
```

> 💡 **提示**: 详细的配置管理指南请参考 [CONFIGURATION.md](CONFIGURATION.md)

### 5. 启动服务

#### 方式一：完整 Web 应用（推荐）

**启动后端 API 服务**

```bash
# 进入后端目录
cd backend
python main.py
```

后端 API 服务将在 http://localhost:8000 启动

**启动前端服务**

```bash
# 在另一个终端窗口，进入前端目录
cd frontend
npm start
# 或使用 yarn
yarn start
```

前端应用将在 http://localhost:3000 启动

**访问应用**

打开浏览器访问 http://localhost:3000 使用现代化的 Web 界面。

#### 方式二：仅后端 API 服务

```bash
cd backend
python main.py
```

访问 http://localhost:8000/docs 查看 API 文档，或使用 API 端点进行开发。

## 📖 使用指南

### Web 界面使用

1. **访问首页**: 打开浏览器访问 http://localhost:3000
2. **上传项目**:
   - 输入 GitHub 仓库地址
   - 或上传本地代码文件
3. **配置分析参数**:
   - 选择批处理大小（影响分析速度和详细程度）
   - 选择是否启用向量化（提供更好的上下文分析）
   - 选择是否强制重新分析
4. **开始分析**: 点击"开始分析"按钮
5. **实时进度**: 查看分析进度和状态更新
6. **浏览结果**:
   - 项目概览和关键指标
   - 文件树浏览器
   - 源代码查看
   - AI 分析结果展示

### API 使用

后端提供了完整的 RESTful API，可以通过 HTTP 请求进行代码分析。

#### 查看 API 文档

访问 http://localhost:8000/docs 查看完整的 API 文档（Swagger UI）。

#### 主要 API 端点

**获取仓库信息**

```bash
curl "http://localhost:8000/api/repository/repositories?name=PocketFlow"
```

**获取文件列表**

```bash
curl "http://localhost:8000/api/repository/files/{task_id}"
```

**获取文件分析结果**

```bash
curl "http://localhost:8000/api/repository/analysis-items/{file_analysis_id}"
```

**健康检查**

```bash
curl "http://localhost:8000/api/health"
```

## 🏗️ 架构设计

项目采用前后端分离架构，基于 PocketFlow 框架构建后端分析引擎：

```
前端 (React + TypeScript)
         ↓ HTTP API
后端 (FastAPI + PocketFlow)
         ↓
GitHub API → Git Clone → 向量化 → LLM 解析 → 数据库存储
     ↓           ↓         ↓         ↓         ↓
  仓库信息    本地克隆   知识库构建  代码分析   结构化数据
```

### 技术栈

#### 前端

- **React 18**: 现代化前端框架
- **TypeScript**: 类型安全的 JavaScript
- **Tailwind CSS**: 实用优先的 CSS 框架
- **Lucide React**: 现代图标库
- **React Router**: 客户端路由

#### 后端

- **FastAPI**: 高性能 Python Web 框架
- **PocketFlow**: 异步流程编排框架
- **SQLAlchemy**: Python ORM
- **SQLite**: 轻量级数据库
- **LangChain**: LLM 应用框架

### 核心组件

- **GitHubInfoFetchNode**: 获取仓库基本信息
- **GitCloneNode**: 克隆仓库到本地
- **VectorizeRepoNode**: 构建向量知识库（可选）
- **CodeParsingBatchNode**: 并行解析代码文件
- **SaveResultsNode**: 保存分析结果到数据库

### 目录结构

```
GitHub_analysis/
├── frontend/           # React 前端应用
│   ├── src/
│   │   ├── components/ # React 组件
│   │   ├── pages/      # 页面组件
│   │   ├── services/   # API 服务
│   │   ├── utils/      # 工具函数
│   │   └── types/      # TypeScript 类型
│   ├── public/         # 静态资源
│   └── package.json    # 前端依赖
├── backend/            # FastAPI 后端服务
│   ├── src/
│   │   ├── utils/      # 工具模块
│   │   ├── nodes/      # PocketFlow 节点
│   │   ├── flows/      # 分析流程
│   │   └── api/        # API 路由
│   ├── tests/          # 后端测试用例
│   ├── data/           # 数据存储
│   ├── logs/           # 日志文件
│   ├── main.py         # 后端服务入口
│   └── requirements.txt # 后端依赖
└── README.md           # 项目文档
```

## 🔧 开发环境

### 开发模式启动

**后端开发模式**

```bash
cd backend
# 启用调试模式（支持热重载）
python main.py --debug
```

**前端开发模式**

```bash
cd frontend
npm start
# 或
yarn start
```

前端开发服务器支持热重载，修改代码后会自动刷新页面。

### 构建生产版本

**前端构建**

```bash
cd frontend
npm run build
# 或
yarn build
```

构建后的文件将在 `frontend/build` 目录中。

## 🔧 配置说明

### 环境变量

| 变量名            | 说明                | 默认值                    |
| ----------------- | ------------------- | ------------------------- |
| `GITHUB_TOKEN`    | GitHub API Token    | 必需                      |
| `OPENAI_API_KEY`  | OpenAI API Key      | 必需                      |
| `OPENAI_BASE_URL` | OpenAI API 基础 URL | https://api.openai.com/v1 |
| `OpenAI_MODEL`    | 使用的模型名称      | gpt-3.5-turbo             |
| `APP_HOST`        | 后端服务器主机      | 0.0.0.0                   |
| `APP_PORT`        | 后端服务器端口      | 8000                      |
| `DEBUG`           | 调试模式            | False                     |

### 分析参数建议

- **批处理大小**:

  - **5**: 快速分析，适合大型仓库的初步了解
  - **10**: 推荐设置，平衡速度和质量
  - **15**: 详细分析，适合中小型仓库
  - **20**: 完整分析，适合小型仓库或重要项目

- **向量化**: 启用后可提供更准确的上下文分析，但会增加处理时间

## 🚨 注意事项

1. **API 限制**: 注意 GitHub API 和 OpenAI API 的调用限制
2. **存储空间**: 确保有足够的磁盘空间存储克隆的仓库
3. **网络连接**: 需要稳定的网络连接访问 GitHub 和 OpenAI API
4. **私有仓库**: 需要相应的 GitHub Token 权限访问私有仓库

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 🙏 致谢

- [PocketFlow](https://github.com/The-Pocket/PocketFlow) - 核心流程框架
- [FastAPI](https://fastapi.tiangolo.com/) - 后端 Web 框架
- [React](https://reactjs.org/) - 前端框架
- [TypeScript](https://www.typescriptlang.org/) - 类型安全的 JavaScript
- [Tailwind CSS](https://tailwindcss.com/) - CSS 框架
- [LangChain](https://langchain.com/) - LLM 应用框架
