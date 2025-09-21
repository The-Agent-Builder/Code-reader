#!/bin/bash

# AI 代码库领航员 Docker 构建脚本

set -e

echo "🚀 开始构建 AI 代码库领航员 Docker 镜像..."

# 检查必要文件
echo "📋 检查必要文件..."
if [ ! -f "Dockerfile" ]; then
    echo "❌ 错误: 找不到 Dockerfile"
    exit 1
fi

if [ ! -f "docker-compose.yml" ]; then
    echo "❌ 错误: 找不到 docker-compose.yml"
    exit 1
fi

if [ ! -f ".env.example" ]; then
    echo "❌ 错误: 找不到 .env.example"
    exit 1
fi

# 检查环境变量文件
if [ ! -f ".env" ]; then
    echo "⚠️  警告: 找不到 .env 文件，将复制 .env.example"
    cp .env.example .env
    echo "📝 请编辑 .env 文件，配置必要的环境变量"
fi

# 创建必要的目录
echo "📁 创建必要的目录..."
mkdir -p data/repos data/results data/vectorstores
mkdir -p docker/logs

# 构建镜像
echo "🔨 构建 Docker 镜像..."
docker-compose build --no-cache

echo "✅ Docker 镜像构建完成!"

# 提示用户下一步操作
echo ""
echo "🎉 构建完成! 接下来你可以:"
echo "1. 编辑 .env 文件配置环境变量"
echo "2. 运行 'docker-compose up -d' 启动服务"
echo "3. 访问 http://localhost 查看前端"
echo "4. 访问 http://localhost/docs 查看后端API文档"
echo ""
echo "📖 更多信息请查看 README.md"
