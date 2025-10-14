# 前端 Dockerfile - 用于独立部署前端应用
FROM node:20-alpine AS builder

WORKDIR /app

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

# 复制前端源代码
COPY frontend/src ./src
COPY frontend/index.html ./
COPY frontend/vite.config.ts ./
COPY frontend/*.json ./

# 构建前端应用
RUN pnpm run build

# 生产环境 - 使用 nginx 提供静态文件服务
FROM nginx:alpine

# 复制构建产物到 nginx 目录
COPY --from=builder /app/build /usr/share/nginx/html

# 复制 nginx 配置文件（如果需要自定义配置）
# COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

# 暴露端口
EXPOSE 80

# 启动 nginx
CMD ["nginx", "-g", "daemon off;"]
