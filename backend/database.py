"""
数据库连接模块
"""

from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from config import settings
import logging
from contextlib import asynccontextmanager

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建数据库引擎
engine = create_engine(
    settings.database_url,
    echo=settings.DB_ECHO,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_pre_ping=True,  # 连接池预检查
    pool_recycle=3600,  # 连接回收时间（秒）
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基础模型类
Base = declarative_base()


def get_db():
    """
    获取数据库会话
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@asynccontextmanager
async def get_db_async():
    """
    异步获取数据库会话
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def test_database_connection():
    """
    测试数据库连接

    Returns:
        dict: 连接测试结果
    """
    try:
        # 创建数据库连接
        with engine.connect() as connection:
            # 执行简单的查询测试连接
            result = connection.execute(text("SELECT 1 as test_value"))
            test_value = result.fetchone()

            # 获取数据库版本信息
            version_result = connection.execute(text("SELECT VERSION() as version"))
            version_info = version_result.fetchone()

            # 获取当前数据库名
            db_name_result = connection.execute(text("SELECT DATABASE() as db_name"))
            db_name = db_name_result.fetchone()

            logger.info("数据库连接测试成功")

            return {
                "status": "success",
                "message": "数据库连接正常",
                "connection_test": test_value[0] if test_value else None,
                "database_version": version_info[0] if version_info else "未知",
                "database_name": db_name[0] if db_name else "未知",
                "database_url": f"{settings.DB_DIALECT}://{settings.DB_USER}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}",
                "pool_size": settings.DB_POOL_SIZE,
                "max_overflow": settings.DB_MAX_OVERFLOW,
            }

    except SQLAlchemyError as e:
        logger.error(f"数据库连接失败: {str(e)}")
        return {
            "status": "error",
            "message": "数据库连接失败",
            "error": str(e),
            "database_url": f"{settings.DB_DIALECT}://{settings.DB_USER}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}",
        }
    except Exception as e:
        logger.error(f"数据库连接测试出现未知错误: {str(e)}")
        return {
            "status": "error",
            "message": "数据库连接测试出现未知错误",
            "error": str(e),
        }


async def get_database_info():
    """
    获取数据库详细信息

    Returns:
        dict: 数据库信息
    """
    try:
        with engine.connect() as connection:
            # 获取数据库基本信息
            queries = {
                "version": "SELECT VERSION() as value",
                "current_user": "SELECT USER() as value",
                "current_database": "SELECT DATABASE() as value",
                "connection_id": "SELECT CONNECTION_ID() as value",
                "charset": "SELECT @@character_set_database as value",
                "collation": "SELECT @@collation_database as value",
                "timezone": "SELECT @@time_zone as value",
            }

            info = {}
            for key, query in queries.items():
                try:
                    result = connection.execute(text(query))
                    row = result.fetchone()
                    info[key] = row[0] if row else "未知"
                except Exception as e:
                    info[key] = f"查询失败: {str(e)}"

            # 获取表信息
            try:
                tables_result = connection.execute(text("SHOW TABLES"))
                tables = [row[0] for row in tables_result.fetchall()]
                info["tables"] = tables
                info["table_count"] = len(tables)
            except Exception as e:
                info["tables"] = []
                info["table_count"] = 0
                info["tables_error"] = str(e)

            return {
                "status": "success",
                "message": "数据库信息获取成功",
                "database_info": info,
            }

    except Exception as e:
        logger.error(f"获取数据库信息失败: {str(e)}")
        return {
            "status": "error",
            "message": "获取数据库信息失败",
            "error": str(e),
        }
