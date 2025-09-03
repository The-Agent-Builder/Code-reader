"""
SQLAlchemy 数据库会话与引擎
- 从环境变量读取数据库连接信息
- 提供全局的 engine 与 SessionLocal
"""

from __future__ import annotations

import os
from typing import Optional
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

from .logger import logger

# 确保加载 .env 文件
load_dotenv(override=True)

# 全局 Base
Base = declarative_base()


def _build_db_url() -> str:
    """根据环境变量构建数据库URL (SQLAlchemy URL)。

    支持的环境变量：
    - DB_DIALECT (默认: mysql+pymysql)
    - DB_HOST (默认: localhost)
    - DB_PORT (默认: 3306)
    - DB_NAME (默认: code_analysis)
    - DB_USER (默认: root)
    - DB_PASSWORD (默认: 空)
    - DB_PARAMS (附加参数串，如 charset=utf8mb4)
    """
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

    return f"{dialect}://{auth}@{host}:{port}/{name}?{params}"


_engine = None
_SessionLocal = None


def _set_timezone(dbapi_connection, connection_record):
    """设置数据库连接的时区为 UTC+8"""
    try:
        # 对于 pymysql 连接器，直接执行 SQL
        cursor = dbapi_connection.cursor()
        cursor.execute("SET time_zone = '+08:00'")
        cursor.close()
        logger.info("数据库连接时区已设置为 UTC+8")
    except Exception as e:
        logger.error(f"设置数据库时区失败: {str(e)}")
        # 尝试备用方法
        try:
            cursor = dbapi_connection.cursor()
            cursor.execute("SET SESSION time_zone = '+08:00'")
            cursor.close()
            logger.info("使用 SESSION 方式设置数据库时区为 UTC+8")
        except Exception as e2:
            logger.error(f"备用时区设置也失败: {str(e2)}")


def get_engine(echo: Optional[bool] = None):
    """获取或创建SQLAlchemy Engine"""
    global _engine
    if _engine is None:
        db_url = _build_db_url()
        echo_flag = bool(int(os.getenv("DB_ECHO", "0"))) if echo is None else echo
        pool_size = int(os.getenv("DB_POOL_SIZE", "5"))
        max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "10"))
        logger.info(f"Creating SQLAlchemy engine for: {db_url.split('@')[-1]}")
        _engine = create_engine(
            db_url, echo=echo_flag, pool_pre_ping=True, pool_size=pool_size, max_overflow=max_overflow
        )

        # 添加时区设置事件监听器
        event.listen(_engine, "connect", _set_timezone)
        logger.info("已添加数据库时区设置监听器 (UTC+8)")
    return _engine


def get_session():
    """获取会话工厂 (sessionmaker)"""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine(), autoflush=False, autocommit=False)
    return _SessionLocal


def init_db():
    """创建所有表（如果不存在）"""
    engine = get_engine()
    Base.metadata.create_all(engine)
    logger.info("数据库表初始化完成")
