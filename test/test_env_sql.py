"""
测试 .env 中配置的 MySQL 连接是否成功
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

# 加载 .env 文件
load_dotenv()


def build_db_url():
    """构建数据库连接 URL"""
    dialect = os.getenv("DB_DIALECT", "mysql+pymysql")
    host = os.getenv("DB_HOST", "127.0.0.1")
    port = os.getenv("DB_PORT", "3306")
    name = os.getenv("DB_NAME", "code_analysis")
    user = os.getenv("DB_USER", "root")
    password = os.getenv("DB_PASSWORD", "")
    params = os.getenv("DB_PARAMS", "charset=utf8mb4")

    auth = user
    if password:
        auth += f":{password}"

    url = f"{dialect}://{auth}@{host}:{port}/{name}?{params}"
    return url


def test_connection():
    """测试数据库连接"""
    print("🔍 测试 MySQL 连接配置...")
    print("=" * 50)

    # 显示配置信息（隐藏密码）
    print("📋 当前配置:")
    print(f"  DB_DIALECT: {os.getenv('DB_DIALECT', 'mysql+pymysql')}")
    print(f"  DB_HOST: {os.getenv('DB_HOST', '127.0.0.1')}")
    print(f"  DB_PORT: {os.getenv('DB_PORT', '3306')}")
    print(f"  DB_NAME: {os.getenv('DB_NAME', 'code_analysis')}")
    print(f"  DB_USER: {os.getenv('DB_USER', 'root')}")
    password = os.getenv("DB_PASSWORD", "")
    if password:
        masked_password = (
            password[:2] + "*" * (len(password) - 4) + password[-2:] if len(password) > 4 else "*" * len(password)
        )
        print(f"  DB_PASSWORD: {masked_password}")
    else:
        print(f"  DB_PASSWORD: (空)")
    print(f"  DB_PARAMS: {os.getenv('DB_PARAMS', 'charset=utf8mb4')}")
    print(f"  DB_ECHO: {os.getenv('DB_ECHO', '0')}")
    print(f"  DB_POOL_SIZE: {os.getenv('DB_POOL_SIZE', '5')}")
    print(f"  DB_MAX_OVERFLOW: {os.getenv('DB_MAX_OVERFLOW', '10')}")
    print()

    try:
        # 构建连接 URL
        db_url = build_db_url()
        print(f"🔗 连接 URL: {db_url.split('@')[0]}@***")
        print()

        # 创建引擎
        print("🚀 创建 SQLAlchemy 引擎...")
        engine = create_engine(
            db_url,
            pool_pre_ping=True,
            pool_size=int(os.getenv("DB_POOL_SIZE", "5")),
            max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "10")),
            echo=(os.getenv("DB_ECHO", "0") == "1"),
        )

        # 测试连接
        print("🔌 测试数据库连接...")
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1 as test_value"))
            test_value = result.fetchone()[0]
            print(f"✅ 连接成功! 测试查询返回: {test_value}")

        # 测试会话
        print("📝 测试 SQLAlchemy 会话...")
        SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
        with SessionLocal() as session:
            result = session.execute(text("SELECT VERSION() as mysql_version"))
            mysql_version = result.fetchone()[0]
            print(f"✅ 会话测试成功! MySQL 版本: {mysql_version}")

        # 测试数据库是否存在
        print("🗄️ 检查数据库和表...")
        with SessionLocal() as session:
            # 检查数据库
            result = session.execute(text("SELECT DATABASE() as current_db"))
            current_db = result.fetchone()[0]
            print(f"📂 当前数据库: {current_db}")

            # 检查表是否存在
            result = session.execute(
                text(
                    """
                SELECT TABLE_NAME
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA = DATABASE()
                ORDER BY TABLE_NAME
            """
                )
            )
            tables = [row[0] for row in result.fetchall()]

            if tables:
                print(f"📋 现有表 ({len(tables)} 个):")
                for table in tables:
                    print(f"  - {table}")
            else:
                print("⚠️ 数据库中暂无表，可能需要运行初始化脚本")

        print()
        print("🎉 所有测试通过! MySQL 连接配置正确")
        return True

    except ImportError as e:
        print(f"❌ 缺少依赖库: {e}")
        print("💡 请安装: pip install sqlalchemy pymysql python-dotenv")
        return False

    except SQLAlchemyError as e:
        print(f"❌ 数据库连接失败: {e}")
        print()
        print("🔧 可能的解决方案:")
        print("1. 检查 MySQL 服务是否启动")
        print("2. 验证数据库连接信息 (host, port, user, password)")
        print("3. 确认数据库 'code_analysis' 是否存在")
        print("4. 检查用户权限")
        print("5. 如果使用云数据库，检查防火墙/安全组设置")
        return False

    except Exception as e:
        print(f"❌ 未知错误: {e}")
        return False


def test_project_db_utils():
    """测试项目中的数据库工具"""
    print("\n" + "=" * 50)
    print("🔧 测试项目数据库工具...")

    try:
        from src.utils.db import get_engine, get_session, init_db

        print("📦 导入项目数据库工具成功")

        # 测试引擎
        engine = get_engine()
        print("✅ 获取引擎成功")

        # 测试会话工厂
        SessionLocal = get_session()
        print("✅ 获取会话工厂成功")

        # 测试会话
        with SessionLocal() as session:
            result = session.execute(text("SELECT 1"))
            print("✅ 会话测试成功")

        # 测试初始化数据库
        print("🏗️ 测试数据库初始化...")
        init_db()
        print("✅ 数据库初始化成功")

        print("🎉 项目数据库工具测试通过!")
        return True

    except Exception as e:
        print(f"❌ 项目数据库工具测试失败: {e}")
        return False


if __name__ == "__main__":
    print("🧪 MySQL 连接测试")
    print("=" * 50)

    # 检查 .env 文件是否存在
    env_file = project_root / ".env"
    if not env_file.exists():
        print(f"⚠️ 未找到 .env 文件: {env_file}")
        print("请在项目根目录创建 .env 文件并配置数据库连接信息")
        sys.exit(1)

    print(f"📁 .env 文件位置: {env_file}")
    print()

    # 基础连接测试
    success1 = test_connection()

    # 项目工具测试
    success2 = test_project_db_utils()

    print("\n" + "=" * 50)
    if success1 and success2:
        print("🎉 所有测试通过! 数据库配置正确，可以正常使用")
        sys.exit(0)
    else:
        print("❌ 部分测试失败，请检查配置")
        sys.exit(1)
