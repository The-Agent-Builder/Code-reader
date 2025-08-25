"""
SQLAlchemy ORM 模型定义
"""

from __future__ import annotations

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from ..utils.db import Base


class Repository(Base):
    __tablename__ = "repositories"

    # 基本标识信息
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    url = Column(String(512), nullable=False)
    clone_url = Column(String(512), nullable=True)
    ssh_url = Column(String(512), nullable=True)

    # 描述信息
    description = Column(Text, nullable=True)
    readme = Column(Text, nullable=True)

    # 主要编程语言
    primary_language = Column(String(64), nullable=True)
    language = Column(String(64), nullable=True)  # 兼容旧版

    # 语言分布 (JSON格式存储)
    languages = Column(JSON, nullable=True)

    # 社交统计
    stars = Column(String(20), nullable=True)
    stargazers_count = Column(Integer, nullable=True)
    forks = Column(String(20), nullable=True)
    forks_count = Column(Integer, nullable=True)
    watchers = Column(String(20), nullable=True)
    watchers_count = Column(Integer, nullable=True)
    open_issues_count = Column(Integer, nullable=True)

    # 仓库属性
    size = Column(Integer, nullable=True)
    default_branch = Column(String(64), nullable=True)
    license = Column(String(255), nullable=True)

    # 状态标志
    archived = Column(Boolean, default=False)
    disabled = Column(Boolean, default=False)
    private = Column(Boolean, default=False)
    fork = Column(Boolean, default=False)

    # 主题标签 (JSON数组格式)
    topics = Column(JSON, nullable=True)

    # 时间信息
    repo_created_at = Column(DateTime, nullable=True)
    repo_updated_at = Column(DateTime, nullable=True)
    last_updated = Column(String(64), nullable=True)

    # 数据来源
    source = Column(String(64), default="GitHub API")

    # 系统时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    analyses = relationship("AnalysisTask", back_populates="repository")


class AnalysisTask(Base):
    __tablename__ = "analysis_tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    repository_id = Column(Integer, ForeignKey("repositories.id"), nullable=False)
    status = Column(String(32), default="running")
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    total_files = Column(Integer, default=0)
    successful_files = Column(Integer, default=0)
    failed_files = Column(Integer, default=0)
    analysis_config = Column(JSON, nullable=True)

    repository = relationship("Repository", back_populates="analyses")
    files = relationship("FileAnalysis", back_populates="task")


class FileAnalysis(Base):
    __tablename__ = "file_analyses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("analysis_tasks.id"), nullable=False)
    file_path = Column(String(1024), nullable=False)
    language = Column(String(64), nullable=True)
    analysis_timestamp = Column(DateTime, default=datetime.utcnow)
    status = Column(String(32), default="success")
    error_message = Column(Text, nullable=True)

    task = relationship("AnalysisTask", back_populates="files")
    targets = relationship("SearchTarget", back_populates="file_analysis")
    items = relationship("AnalysisItem", back_populates="file_analysis")


class SearchTarget(Base):
    __tablename__ = "search_targets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_analysis_id = Column(Integer, ForeignKey("file_analyses.id"), nullable=False)
    target_type = Column(String(32), nullable=False)  # file/class/function
    target_name = Column(String(255), nullable=True)
    target_identifier = Column(String(512), nullable=False)

    file_analysis = relationship("FileAnalysis", back_populates="targets")
    items = relationship("AnalysisItem", back_populates="search_target")


class AnalysisItem(Base):
    __tablename__ = "analysis_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_analysis_id = Column(Integer, ForeignKey("file_analyses.id"), nullable=False)
    search_target_id = Column(Integer, ForeignKey("search_targets.id"), nullable=True)
    title = Column(String(512), nullable=False)
    description = Column(Text, nullable=True)
    source = Column(String(1024), nullable=True)
    language = Column(String(64), nullable=True)
    code = Column(Text, nullable=True)
    start_line = Column(Integer, nullable=True)
    end_line = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    file_analysis = relationship("FileAnalysis", back_populates="items")
    search_target = relationship("SearchTarget", back_populates="items")
