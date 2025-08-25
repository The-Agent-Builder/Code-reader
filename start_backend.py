#!/usr/bin/env python3
"""
后端API服务启动脚本
"""

import sys
import os
import subprocess
from pathlib import Path


def check_requirements():
    """检查依赖包是否安装"""
    try:
        import fastapi
        import sqlalchemy
        import pymysql
        import pydantic

        print("✅ 所有依赖包已安装")
        return True
    except ImportError as e:
        print(f"❌ 缺少依赖包: {e}")
        print("请运行: pip install -r backend/requirements.txt")
        return False


def check_database():
    """检查数据库连接"""
    try:
        from src.utils.db import get_engine

        engine = get_engine()
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        print("✅ 数据库连接正常")
        return True
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        print("请检查 .env 文件中的数据库配置")
        return False


def main():
    """主函数"""
    print("🚀 启动后端API服务...")

    # 检查依赖
    if not check_requirements():
        sys.exit(1)

    # 检查数据库
    if not check_database():
        print("⚠️  数据库连接失败，但仍可启动服务（部分功能可能不可用）")

    # 获取配置
    from backend.config import config

    host = config.HOST
    port = config.PORT

    print(f"📡 服务地址: http://{host}:{port}")
    print(f"📚 API文档: http://{host}:{port}/docs")
    print("按 Ctrl+C 停止服务")
    print("-" * 50)

    # 启动服务
    try:
        subprocess.run(
            [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", host, "--port", str(port), "--reload"]
        )
    except KeyboardInterrupt:
        print("\n👋 服务已停止")


if __name__ == "__main__":
    main()
