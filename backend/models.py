"""
数据库模型定义
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

from datetime import datetime, timezone

Base = declarative_base()


class FileAnalysis(Base):
    """
    文件分析表模型 - 根据实际数据库表结构定义
    """

    __tablename__ = "file_analyses"

    id = Column(Integer, primary_key=True, index=True, comment="文件分析ID")
    task_id = Column(Integer, index=True, nullable=False, comment="任务ID")
    file_path = Column(String(1024), nullable=False, comment="文件路径")
    language = Column(String(64), comment="编程语言")
    analysis_version = Column(String(32), default="1.0", comment="分析版本")
    status = Column(String(32), default="pending", comment="分析状态: pending/success/failed")
    code_lines = Column(Integer, default=0, comment="代码行数")
    code_content = Column(Text, comment="代码内容")
    file_analysis = Column(Text, comment="文件分析结果")
    dependencies = Column(Text, comment="依赖模块列表")
    analysis_timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), comment="分析时间")
    error_message = Column(Text, comment="错误信息")

    def __repr__(self):
        return f"<FileAnalysis(id={self.id}, task_id={self.task_id}, file_path='{self.file_path}')>"

    def to_dict(self, include_code_content: bool = False):
        """转换为字典格式"""
        # 从文件路径中提取文件名和文件类型
        import os

        file_name = os.path.basename(self.file_path) if self.file_path else ""
        file_extension = os.path.splitext(file_name)[1].lstrip(".") if file_name else ""

        result = {
            "id": self.id,
            "task_id": self.task_id,
            "file_path": self.file_path,
            "file_name": file_name,  # 从路径中提取
            "file_type": file_extension,  # 从文件名中提取
            "language": self.language,
            "analysis_version": self.analysis_version,
            "status": self.status,
            "code_lines": self.code_lines,
            "file_analysis": self.file_analysis,
            "dependencies": self.dependencies,
            "analysis_timestamp": self.analysis_timestamp.isoformat() if self.analysis_timestamp else None,
            "error_message": self.error_message,
        }

        # 根据参数决定是否包含代码内容
        if include_code_content:
            result["code_content"] = self.code_content

        return result


class AnalysisItem(Base):
    """
    分析项表模型 - 根据实际数据库表结构定义
    """

    __tablename__ = "analysis_items"

    id = Column(Integer, primary_key=True, index=True, comment="分析项ID")
    file_analysis_id = Column(Integer, index=True, nullable=False, comment="文件分析ID")
    title = Column(String(512), nullable=False, comment="标题")
    description = Column(Text, comment="描述")
    target_type = Column(String(32), comment="目标类型：file/class/function")
    target_name = Column(String(255), comment="目标名称（类名/函数名）")
    source = Column(String(1024), comment="源码位置")
    language = Column(String(64), comment="编程语言")
    code = Column(Text, comment="代码片段")
    start_line = Column(Integer, comment="起始行号")
    end_line = Column(Integer, comment="结束行号")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), comment="创建时间")
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        comment="更新时间",
    )

    def __repr__(self):
        return f"<AnalysisItem(id={self.id}, file_analysis_id={self.file_analysis_id}, title='{self.title}')>"

    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "file_analysis_id": self.file_analysis_id,
            "title": self.title,
            "description": self.description,
            "target_type": self.target_type,
            "target_name": self.target_name,
            "source": self.source,
            "language": self.language,
            "code": self.code,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Repository(Base):
    """
    仓库表模型 - 根据实际数据库表结构定义
    """

    __tablename__ = "repositories"

    id = Column(Integer, primary_key=True, index=True, comment="仓库ID")
    user_id = Column(Integer, nullable=False, comment="上传用户ID")
    name = Column(String(255), nullable=False, index=True, comment="仓库名称")
    full_name = Column(String(255), comment="完整仓库名")
    local_path = Column(String(1024), nullable=False, comment="本地仓库路径")
    status = Column(Integer, default=1, comment="状态：1=存在，0=已删除")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), comment="创建时间")
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        comment="更新时间",
    )

    # 注意：analysis_tasks 属性会在服务层动态设置

    def __repr__(self):
        return f"<Repository(id={self.id}, name='{self.name}', full_name='{self.full_name}')>"

    def to_dict(self, include_tasks=False):
        """转换为字典格式"""
        result = {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "full_name": self.full_name,
            "local_path": self.local_path,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        # 如果需要包含任务信息
        if include_tasks and hasattr(self, "analysis_tasks"):
            result["tasks"] = [task.to_dict() for task in self.analysis_tasks]
            result["total_tasks"] = len(self.analysis_tasks)

        return result


class AnalysisTask(Base):
    """
    分析任务表模型 - 根据实际数据库表结构定义
    """

    __tablename__ = "analysis_tasks"

    id = Column(Integer, primary_key=True, index=True, comment="任务ID")
    repository_id = Column(Integer, ForeignKey("repositories.id"), index=True, nullable=False, comment="仓库ID")
    total_files = Column(Integer, default=0, comment="总文件数")
    successful_files = Column(Integer, default=0, comment="成功分析文件数")
    failed_files = Column(Integer, default=0, comment="失败文件数")
    code_lines = Column(Integer, default=0, comment="代码行数")
    module_count = Column(Integer, default=0, comment="模块数量")
    status = Column(String(32), default="pending", index=True, comment="任务状态: pending/running/completed/failed")
    start_time = Column(DateTime, default=lambda: datetime.now(timezone.utc), comment="开始时间")
    end_time = Column(DateTime, comment="结束时间")
    task_index = Column(String(255), index=True, comment="任务索引")

    # 注意：repository 关系可以通过 repository_id 外键访问

    def __repr__(self):
        return f"<AnalysisTask(id={self.id}, repository_id={self.repository_id}, status='{self.status}')>"

    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "repository_id": self.repository_id,
            "total_files": self.total_files,
            "successful_files": self.successful_files,
            "failed_files": self.failed_files,
            "code_lines": self.code_lines,
            "module_count": self.module_count,
            "status": self.status,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "task_index": self.task_index,
        }
