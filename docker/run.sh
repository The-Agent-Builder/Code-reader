#!/bin/bash

# AI 代码库领航员 Docker 运行脚本
# 用于启动包含前端和后端的 Docker 容器

set -e

echo "🚀 启动 AI 代码库领航员服务..."

# 检查是否在项目根目录
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ 错误: 请在项目根目录运行此脚本"
    exit 1
fi

# 检查 Docker 是否运行
if ! docker info &> /dev/null; then
    echo "❌ 错误: Docker 未运行，请先启动 Docker"
    exit 1
fi

# 检查环境变量文件
if [ ! -f ".env" ]; then
    echo "⚠️  警告: 未找到 .env 文件，将使用默认配置"
    echo "建议复制 .env.example 为 .env 并配置相关参数"
fi

# 停止已存在的容器
echo "🛑 停止已存在的容器..."
docker-compose down

# 启动服务
echo "🔄 启动服务..."
docker-compose up -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "📊 检查服务状态..."
docker-compose ps

# 检查健康状态
echo "🏥 检查健康状态..."
for i in {1..30}; do
    if curl -f http://localhost/health &> /dev/null; then
        echo "✅ 服务启动成功!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ 服务启动超时，请检查日志"
        docker-compose logs
        exit 1
    fi
    echo "等待服务启动... ($i/30)"
    sleep 2
done

# 显示访问信息
echo ""
echo "🎉 服务启动成功!"
echo ""
echo "📱 访问地址:"
echo "  前端应用: http://localhost"
echo "  API文档:  http://localhost/docs"
echo "  健康检查: http://localhost/health"
echo ""
echo "📋 管理命令:"
echo "  查看日志: docker-compose logs -f"
echo "  停止服务: docker-compose down"
echo "  重启服务: docker-compose restart"
echo ""
echo "📖 更多信息请查看 README.md"
