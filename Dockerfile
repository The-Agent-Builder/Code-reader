# 多阶段构建 Dockerfile
# 阶段1: 构建前端
FROM swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/library/node:20-alpine3.22 AS frontend-builder

WORKDIR /app/frontend

# 复制前端依赖文件
COPY frontend/package.json frontend/pnpm-lock.yaml ./

# 安装pnpm并配置存储目录
RUN npm install -g pnpm@latest

# 设置pnpm配置优化构建速度
ENV PNPM_HOME="/pnpm"
ENV PATH="$PNPM_HOME:$PATH"

# 安装前端依赖（包括开发依赖，构建时需要）
RUN pnpm config set store-dir .pnpm-store && \
    pnpm install --frozen-lockfile

# 复制前端源代码（排除 node_modules）
COPY frontend/src ./src
COPY frontend/index.html ./
COPY frontend/vite.config.ts ./
COPY frontend/*.json ./

# 构建前端应用
RUN pnpm run build

# 阶段2: 准备后端环境
FROM swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/python:3.11-slim AS backend-base

# 设置工作目录
WORKDIR /app

# 更换为国内镜像源并安装系统依赖
RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources \
    && apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 安装 uv
RUN pip install uv

# 复制项目配置文件
COPY pyproject.toml uv.lock ./

# 使用 uv 安装 Python 依赖
RUN uv sync --frozen

# 阶段3: 最终运行环境
FROM swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/python:3.11-slim AS runtime

# 安装运行时系统依赖
# 更新源并安装基础工具
RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources \
    && apt-get update \
    && apt-get install -y curl gnupg2 \
    && rm -rf /var/lib/apt/lists/*

# 添加 NodeSource 仓库并安装所有依赖
RUN curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_20.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list \
    && apt-get update \
    && apt-get install -y \
    git \
    nginx \
    supervisor \
    nodejs \
    # Chrome Headless Shell 所需依赖
    ca-certificates \
    fonts-liberation \
    libappindicator3-1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libc6 \
    libcairo2 \
    libcups2 \
    libdbus-1-3 \
    libexpat1 \
    libfontconfig1 \
    libgbm1 \
    libgcc1 \
    libglib2.0-0 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libstdc++6 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libxrender1 \
    libxss1 \
    libxtst6 \
    lsb-release \
    wget \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# 安装 uv
RUN pip install uv

# 安装 mermaid-cli
RUN npm install -g @mermaid-js/mermaid-cli

# 安装 Chrome Headless Shell（用于 mermaid 渲染）
RUN npx puppeteer browsers install chrome-headless-shell

# 创建 Puppeteer 配置文件，允许在 root 下运行，并设置更大的viewport
RUN echo '{\
  "args": [\
    "--no-sandbox",\
    "--disable-setuid-sandbox",\
    "--disable-dev-shm-usage",\
    "--disable-gpu"\
  ],\
  "defaultViewport": {\
    "width": 20480,\
    "height": 20480,\
    "deviceScaleFactor": 3\
  }\
}' > /root/puppeteer-config.json

# 设置工作目录
WORKDIR /app

# 从 backend-base 阶段复制 Python 环境
COPY --from=backend-base /app/.venv /app/.venv

# 复制项目文件
COPY pyproject.toml uv.lock ./
COPY backend/ ./backend/
COPY src/ ./src/
COPY sql/ ./sql/

# 从前端构建阶段复制构建产物
COPY --from=frontend-builder /app/frontend/build /var/www/html

# 配置 Nginx
COPY docker/nginx.conf /etc/nginx/sites-available/default
RUN rm -f /etc/nginx/sites-enabled/default && \
    ln -s /etc/nginx/sites-available/default /etc/nginx/sites-enabled/

# 配置 Supervisor
COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# 创建必要的目录和日志目录
RUN mkdir -p /app/data/repos /app/data/results /app/data/vectorstores \
    /var/log/supervisor /var/log/nginx

# 设置环境变量
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app"

# 暴露端口（只暴露前端端口80，后端8000端口仅内部使用）
EXPOSE 80

# 启动 Supervisor
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]

