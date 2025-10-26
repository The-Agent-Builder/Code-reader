"""
业务服务层
"""

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from models import FileAnalysis, AnalysisItem, Repository, AnalysisTask, TaskReadme
from typing import Optional

from database import SessionLocal
import logging
from datetime import datetime, timezone
import zipfile
import httpx
from utils.makdown_utils.mermaid_to_svg import MermaidToSvgConverter
logger = logging.getLogger(__name__)


class FileAnalysisService:
    """文件分析服务类"""

    @staticmethod
    def get_files_by_task_id(
        task_id: int,
        db: Session = None,
        language: str = None,
        analysis_version: str = None,
        status: str = None,
        include_code_content: bool = False,
    ) -> dict:
        """
        根据task_id获取文件列表

        Args:
            task_id: 任务ID
            db: 数据库会话（可选）
            language: 编程语言过滤器（可选）
            analysis_version: 分析版本过滤器（可选）
            status: 状态过滤器（可选）
            include_code_content: 是否返回代码内容（可选，默认False）

        Returns:
            dict: 包含文件列表的字典
        """
        # 如果没有传入数据库会话，创建新的会话
        if db is None:
            db = SessionLocal()
            should_close = True
        else:
            should_close = False

        try:
            # 构建查询条件
            query = db.query(FileAnalysis).filter(FileAnalysis.task_id == task_id)

            # 添加过滤条件
            if language:
                query = query.filter(FileAnalysis.language == language)
            if analysis_version:
                query = query.filter(FileAnalysis.analysis_version == analysis_version)
            if status:
                query = query.filter(FileAnalysis.status == status)

            # 执行查询并排序
            files = query.order_by(FileAnalysis.file_path).all()

            if not files:
                return {
                    "status": "success",
                    "message": f"未找到task_id为 {task_id} 的文件记录",
                    "task_id": task_id,
                    "total_files": 0,
                    "files": [],
                }

            # 转换为字典格式
            file_list = [file.to_dict(include_code_content=include_code_content) for file in files]

            logger.info(f"成功获取task_id {task_id} 的文件列表，共 {len(files)} 个文件")

            return {
                "status": "success",
                "message": "文件列表获取成功",
                "task_id": task_id,
                "total_files": len(files),
                "files": file_list,
            }

        except SQLAlchemyError as e:
            logger.error(f"数据库查询失败: {str(e)}")
            return {"status": "error", "message": "数据库查询失败", "task_id": task_id, "error": str(e)}
        except Exception as e:
            logger.error(f"获取文件列表时发生未知错误: {str(e)}")
            return {"status": "error", "message": "获取文件列表时发生未知错误", "task_id": task_id, "error": str(e)}
        finally:
            if should_close:
                db.close()

    @staticmethod
    def get_file_analysis_by_id_and_task_id(file_id: int, task_id: int, db: Session = None) -> dict:
        """
        根据文件分析ID和任务ID获取单条文件分析记录

        Args:
            file_id: 文件分析记录ID
            task_id: 任务ID
            db: 数据库会话（可选）

        Returns:
            dict: 包含完整文件分析记录的字典
        """
        should_close = False
        if db is None:
            db = next(get_db())
            should_close = True

        try:
            # 查询指定ID和任务ID的文件分析记录
            file_analysis = (
                db.query(FileAnalysis).filter(FileAnalysis.id == file_id, FileAnalysis.task_id == task_id).first()
            )

            if not file_analysis:
                return {
                    "status": "success",
                    "message": f"未找到ID为 {file_id} 且任务ID为 {task_id} 的文件分析记录",
                    "file_id": file_id,
                    "task_id": task_id,
                    "file_analysis": None,
                }

            # 转换为字典格式，包含所有字段（包括代码内容）
            file_data = file_analysis.to_dict(include_code_content=True)

            logger.info(f"成功获取文件分析记录 ID: {file_id}, 任务ID: {task_id}")

            return {
                "status": "success",
                "message": "文件分析记录获取成功",
                "file_id": file_id,
                "task_id": task_id,
                "file_analysis": file_data,
            }

        except SQLAlchemyError as e:
            logger.error(f"数据库查询失败: {str(e)}")
            return {
                "status": "error",
                "message": "数据库查询失败",
                "file_id": file_id,
                "task_id": task_id,
                "error": str(e),
            }
        except Exception as e:
            logger.error(f"获取文件分析记录时发生未知错误: {str(e)}")
            return {
                "status": "error",
                "message": "获取文件分析记录时发生未知错误",
                "file_id": file_id,
                "task_id": task_id,
                "error": str(e),
            }
        finally:
            if should_close:
                db.close()

    @staticmethod
    def _calculate_statistics(files: list) -> dict:
        """
        计算文件统计信息

        Args:
            files: 文件列表

        Returns:
            dict: 统计信息
        """
        statistics = {"by_language": {}, "by_status": {}, "by_file_type": {}, "total_size": 0}

        for file in files:
            # 按编程语言统计
            language = file.language or "unknown"
            statistics["by_language"][language] = statistics["by_language"].get(language, 0) + 1

            # 按分析状态统计
            status = file.status or "unknown"
            statistics["by_status"][status] = statistics["by_status"].get(status, 0) + 1

            # 按文件类型统计 - 从文件路径中提取
            import os

            file_extension = os.path.splitext(file.file_path)[1].lstrip(".") if file.file_path else "unknown"
            file_type = file_extension or "unknown"
            statistics["by_file_type"][file_type] = statistics["by_file_type"].get(file_type, 0) + 1

            # 注意：实际表中没有file_size字段，所以不统计文件大小
            # statistics["total_size"] += 0

        return statistics

    @staticmethod
    def create_file_analysis(file_data: dict, db: Session = None) -> dict:
        """
        创建新的文件分析记录

        Args:
            file_data: 文件分析数据字典
            db: 数据库会话（可选）

        Returns:
            dict: 包含创建结果的字典
        """
        if db is None:
            db = SessionLocal()
            should_close = True
        else:
            should_close = False

        try:
            # 验证task_id是否存在
            task = db.query(AnalysisTask).filter(AnalysisTask.id == file_data["task_id"]).first()
            if not task:
                return {
                    "status": "error",
                    "message": f"分析任务ID {file_data['task_id']} 不存在",
                    "task_id": file_data["task_id"],
                }

            # 创建新文件分析记录
            new_file_analysis = FileAnalysis(
                task_id=file_data["task_id"],
                file_path=file_data["file_path"],
                language=file_data.get("language"),
                analysis_version=file_data.get("analysis_version", "1.0"),
                status=file_data.get("status", "pending"),
                code_lines=file_data.get("code_lines", 0),
                code_content=file_data.get("code_content"),
                file_analysis=file_data.get("file_analysis"),
                dependencies=file_data.get("dependencies"),
                error_message=file_data.get("error_message"),
            )

            db.add(new_file_analysis)
            db.commit()
            db.refresh(new_file_analysis)

            logger.info(f"成功创建文件分析记录: ID {new_file_analysis.id}, 任务ID {new_file_analysis.task_id}")

            return {
                "status": "success",
                "message": "文件分析记录创建成功",
                "file_analysis": new_file_analysis.to_dict(include_code_content=True),
            }

        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"数据库操作失败: {str(e)}")
            return {
                "status": "error",
                "message": "数据库操作失败",
                "error": str(e),
            }
        except Exception as e:
            db.rollback()
            logger.error(f"创建文件分析记录时发生未知错误: {str(e)}")
            return {
                "status": "error",
                "message": "创建文件分析记录时发生未知错误",
                "error": str(e),
            }
        finally:
            if should_close:
                db.close()

    @staticmethod
    def update_file_analysis(file_id: int, update_data: dict, db: Session = None) -> dict:
        """
        更新文件分析记录信息

        Args:
            file_id: 文件分析ID
            update_data: 更新数据字典
            db: 数据库会话（可选）

        Returns:
            dict: 包含更新结果的字典
        """
        if db is None:
            db = SessionLocal()
            should_close = True
        else:
            should_close = False

        try:
            # 查询要更新的文件分析记录
            file_analysis = db.query(FileAnalysis).filter(FileAnalysis.id == file_id).first()

            if not file_analysis:
                return {
                    "status": "error",
                    "message": f"未找到ID为 {file_id} 的文件分析记录",
                    "file_id": file_id,
                }

            # 如果要更新task_id，检查是否存在
            if "task_id" in update_data:
                task = db.query(AnalysisTask).filter(AnalysisTask.id == update_data["task_id"]).first()
                if not task:
                    return {
                        "status": "error",
                        "message": f"分析任务ID {update_data['task_id']} 不存在",
                        "task_id": update_data["task_id"],
                    }

            # 更新字段
            for field, value in update_data.items():
                if hasattr(file_analysis, field):
                    setattr(file_analysis, field, value)

            db.commit()
            db.refresh(file_analysis)

            logger.info(f"成功更新文件分析记录ID {file_id} 的信息")

            return {
                "status": "success",
                "message": "文件分析记录信息更新成功",
                "file_analysis": file_analysis.to_dict(include_code_content=True),
            }

        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"数据库操作失败: {str(e)}")
            return {
                "status": "error",
                "message": "数据库操作失败",
                "file_id": file_id,
                "error": str(e),
            }
        except Exception as e:
            db.rollback()
            logger.error(f"更新文件分析记录时发生未知错误: {str(e)}")
            return {
                "status": "error",
                "message": "更新文件分析记录时发生未知错误",
                "file_id": file_id,
                "error": str(e),
            }
        finally:
            if should_close:
                db.close()

    @staticmethod
    def delete_file_analysis(file_id: int, db: Session = None) -> dict:
        """
        删除文件分析记录（硬删除，会级联删除相关的分析项记录）

        Args:
            file_id: 文件分析ID
            db: 数据库会话（可选）

        Returns:
            dict: 包含删除结果的字典
        """
        if db is None:
            db = SessionLocal()
            should_close = True
        else:
            should_close = False

        try:
            # 查询要删除的文件分析记录
            file_analysis = db.query(FileAnalysis).filter(FileAnalysis.id == file_id).first()

            if not file_analysis:
                return {
                    "status": "error",
                    "message": f"未找到ID为 {file_id} 的文件分析记录",
                    "file_id": file_id,
                }

            # 保存文件分析数据用于返回
            file_data = file_analysis.to_dict(include_code_content=True)

            # 物理删除记录（会级联删除相关的分析项记录）
            db.delete(file_analysis)
            db.commit()

            logger.info(f"成功删除文件分析记录ID {file_id}")

            return {
                "status": "success",
                "message": "文件分析记录已删除",
                "file_id": file_id,
                "deleted_file_analysis": file_data,
            }

        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"数据库操作失败: {str(e)}")
            return {
                "status": "error",
                "message": "数据库操作失败",
                "file_id": file_id,
                "error": str(e),
            }
        except Exception as e:
            db.rollback()
            logger.error(f"删除文件分析记录时发生未知错误: {str(e)}")
            return {
                "status": "error",
                "message": "删除文件分析记录时发生未知错误",
                "file_id": file_id,
                "error": str(e),
            }
        finally:
            if should_close:
                db.close()


class AnalysisItemService:
    """分析项服务类"""

    @staticmethod
    def get_analysis_items_by_file_id(
        file_analysis_id: int, db: Session = None, target_type: str = None, language: str = None
    ) -> dict:
        """
        根据file_analysis_id获取分析项列表

        Args:
            file_analysis_id: 文件分析ID
            db: 数据库会话（可选）
            target_type: 目标类型过滤器（可选）
            language: 编程语言过滤器（可选）

        Returns:
            dict: 包含分析项列表的字典，按start_line升序排序
        """
        # 如果没有传入数据库会话，创建新的会话
        if db is None:
            db = SessionLocal()
            should_close = True
        else:
            should_close = False

        try:
            # 构建查询条件
            query = db.query(AnalysisItem).filter(AnalysisItem.file_analysis_id == file_analysis_id)

            # 添加过滤条件
            if target_type:
                query = query.filter(AnalysisItem.target_type == target_type)
            if language:
                query = query.filter(AnalysisItem.language == language)

            # 执行查询并按start_line升序排序
            items = query.order_by(AnalysisItem.start_line.asc(), AnalysisItem.created_at).all()

            if not items:
                return {
                    "status": "success",
                    "message": f"未找到file_analysis_id为 {file_analysis_id} 的分析项记录",
                    "file_analysis_id": file_analysis_id,
                    "total_items": 0,
                    "items": [],
                }

            # 转换为字典格式
            item_list = [item.to_dict() for item in items]

            logger.info(f"成功获取file_analysis_id {file_analysis_id} 的分析项列表，共 {len(items)} 个项目")

            return {
                "status": "success",
                "message": "分析项列表获取成功",
                "file_analysis_id": file_analysis_id,
                "total_items": len(items),
                "items": item_list,
            }

        except SQLAlchemyError as e:
            logger.error(f"数据库查询失败: {str(e)}")
            return {
                "status": "error",
                "message": "数据库查询失败",
                "file_analysis_id": file_analysis_id,
                "error": str(e),
            }
        except Exception as e:
            logger.error(f"获取分析项列表时发生未知错误: {str(e)}")
            return {
                "status": "error",
                "message": "获取分析项列表时发生未知错误",
                "file_analysis_id": file_analysis_id,
                "error": str(e),
            }
        finally:
            if should_close:
                db.close()

    @staticmethod
    def _calculate_item_statistics(items: list) -> dict:
        """
        计算分析项统计信息

        Args:
            items: 分析项列表

        Returns:
            dict: 统计信息
        """
        statistics = {
            "by_language": {},
            "by_search_target": {},
            "total_code_lines": 0,
            "has_code_items": 0,
            "has_description_items": 0,
        }

        for item in items:
            # 按编程语言统计
            language = item.language or "unknown"
            statistics["by_language"][language] = statistics["by_language"].get(language, 0) + 1

            # 按检索目标统计
            target_id = item.search_target_id or "none"
            statistics["by_search_target"][str(target_id)] = statistics["by_search_target"].get(str(target_id), 0) + 1

            # 统计代码行数
            if item.start_line and item.end_line:
                code_lines = item.end_line - item.start_line + 1
                statistics["total_code_lines"] += code_lines

            # 统计有代码的项目
            if item.code:
                statistics["has_code_items"] += 1

            # 统计有描述的项目
            if item.description:
                statistics["has_description_items"] += 1

        return statistics

    @staticmethod
    def create_analysis_item(item_data: dict, db: Session = None) -> dict:
        """
        创建新的分析项记录

        Args:
            item_data: 分析项数据字典
            db: 数据库会话（可选）

        Returns:
            dict: 包含创建结果的字典
        """
        if db is None:
            db = SessionLocal()
            should_close = True
        else:
            should_close = False

        try:
            # 验证file_analysis_id是否存在
            file_analysis = db.query(FileAnalysis).filter(FileAnalysis.id == item_data["file_analysis_id"]).first()
            if not file_analysis:
                return {
                    "status": "error",
                    "message": f"文件分析ID {item_data['file_analysis_id']} 不存在",
                    "file_analysis_id": item_data["file_analysis_id"],
                }

            # 创建新分析项记录
            new_item = AnalysisItem(
                file_analysis_id=item_data["file_analysis_id"],
                title=item_data["title"],
                description=item_data.get("description"),
                target_type=item_data.get("target_type"),
                target_name=item_data.get("target_name"),
                source=item_data.get("source"),
                language=item_data.get("language"),
                code=item_data.get("code"),
                start_line=item_data.get("start_line"),
                end_line=item_data.get("end_line"),
            )

            db.add(new_item)
            db.commit()
            db.refresh(new_item)

            logger.info(f"成功创建分析项记录: ID {new_item.id}, 文件分析ID {new_item.file_analysis_id}")

            return {
                "status": "success",
                "message": "分析项记录创建成功",
                "analysis_item": new_item.to_dict(),
            }

        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"数据库操作失败: {str(e)}")
            return {
                "status": "error",
                "message": "数据库操作失败",
                "error": str(e),
            }
        except Exception as e:
            db.rollback()
            logger.error(f"创建分析项记录时发生未知错误: {str(e)}")
            return {
                "status": "error",
                "message": "创建分析项记录时发生未知错误",
                "error": str(e),
            }
        finally:
            if should_close:
                db.close()

    @staticmethod
    def update_analysis_item(item_id: int, update_data: dict, db: Session = None) -> dict:
        """
        更新分析项记录信息

        Args:
            item_id: 分析项ID
            update_data: 更新数据字典
            db: 数据库会话（可选）

        Returns:
            dict: 包含更新结果的字典
        """
        if db is None:
            db = SessionLocal()
            should_close = True
        else:
            should_close = False

        try:
            # 查询要更新的分析项记录
            item = db.query(AnalysisItem).filter(AnalysisItem.id == item_id).first()

            if not item:
                return {
                    "status": "error",
                    "message": f"未找到ID为 {item_id} 的分析项记录",
                    "item_id": item_id,
                }

            # 如果要更新file_analysis_id，检查是否存在
            if "file_analysis_id" in update_data:
                file_analysis = (
                    db.query(FileAnalysis).filter(FileAnalysis.id == update_data["file_analysis_id"]).first()
                )
                if not file_analysis:
                    return {
                        "status": "error",
                        "message": f"文件分析ID {update_data['file_analysis_id']} 不存在",
                        "file_analysis_id": update_data["file_analysis_id"],
                    }

            # 更新字段
            for field, value in update_data.items():
                if hasattr(item, field):
                    setattr(item, field, value)

            db.commit()
            db.refresh(item)

            logger.info(f"成功更新分析项记录ID {item_id} 的信息")

            return {
                "status": "success",
                "message": "分析项记录信息更新成功",
                "analysis_item": item.to_dict(),
            }

        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"数据库操作失败: {str(e)}")
            return {
                "status": "error",
                "message": "数据库操作失败",
                "item_id": item_id,
                "error": str(e),
            }
        except Exception as e:
            db.rollback()
            logger.error(f"更新分析项记录时发生未知错误: {str(e)}")
            return {
                "status": "error",
                "message": "更新分析项记录时发生未知错误",
                "item_id": item_id,
                "error": str(e),
            }
        finally:
            if should_close:
                db.close()

    @staticmethod
    def delete_analysis_item(item_id: int, db: Session = None) -> dict:
        """
        删除分析项记录（硬删除）

        Args:
            item_id: 分析项ID
            db: 数据库会话（可选）

        Returns:
            dict: 包含删除结果的字典
        """
        if db is None:
            db = SessionLocal()
            should_close = True
        else:
            should_close = False

        try:
            # 查询要删除的分析项记录
            item = db.query(AnalysisItem).filter(AnalysisItem.id == item_id).first()

            if not item:
                return {
                    "status": "error",
                    "message": f"未找到ID为 {item_id} 的分析项记录",
                    "item_id": item_id,
                }

            # 保存分析项数据用于返回
            item_data = item.to_dict()

            # 物理删除记录
            db.delete(item)
            db.commit()

            logger.info(f"成功删除分析项记录ID {item_id}")

            return {
                "status": "success",
                "message": "分析项记录已删除",
                "item_id": item_id,
                "deleted_analysis_item": item_data,
            }

        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"数据库操作失败: {str(e)}")
            return {
                "status": "error",
                "message": "数据库操作失败",
                "item_id": item_id,
                "error": str(e),
            }
        except Exception as e:
            db.rollback()
            logger.error(f"删除分析项记录时发生未知错误: {str(e)}")
            return {
                "status": "error",
                "message": "删除分析项记录时发生未知错误",
                "item_id": item_id,
                "error": str(e),
            }
        finally:
            if should_close:
                db.close()


class RepositoryService:
    """仓库服务类"""

    @staticmethod
    def get_repository_by_name(name: str, db: Session = None, include_tasks: bool = True) -> dict:
        """
        根据仓库名称获取仓库信息

        Args:
            name: 仓库名称
            db: 数据库会话（可选）
            include_tasks: 是否包含分析任务信息

        Returns:
            dict: 包含仓库信息的字典
        """
        # 如果没有传入数据库会话，创建新的会话
        if db is None:
            db = SessionLocal()
            should_close = True
        else:
            should_close = False

        try:
            # 查询指定名称的仓库记录（支持模糊匹配）
            repositories = (
                db.query(Repository)
                .filter(Repository.name.like(f"%{name}%"))
                .order_by(Repository.created_at.desc())
                .all()
            )

            # 如果需要包含任务信息，手动查询每个仓库的任务
            if include_tasks:
                for repo in repositories:
                    tasks = (
                        db.query(AnalysisTask)
                        .filter(AnalysisTask.repository_id == repo.id)
                        .order_by(AnalysisTask.start_time.asc())
                        .all()
                    )
                    # 手动设置任务列表
                    repo.analysis_tasks = tasks

            if not repositories:
                return {
                    "status": "success",
                    "message": f"未找到名称包含 '{name}' 的仓库记录",
                    "search_name": name,
                    "total_repositories": 0,
                    "repositories": [],
                }

            # 转换为字典格式
            repository_list = [repo.to_dict(include_tasks=include_tasks) for repo in repositories]

            # 统计信息
            statistics = RepositoryService._calculate_repository_statistics(repositories)

            logger.info(f"成功获取名称包含 '{name}' 的仓库列表，共 {len(repositories)} 个仓库")

            return {
                "status": "success",
                "message": "仓库列表获取成功",
                "search_name": name,
                "total_repositories": len(repositories),
                "repositories": repository_list,
                "statistics": statistics,
            }

        except SQLAlchemyError as e:
            logger.error(f"数据库查询失败: {str(e)}")
            return {
                "status": "error",
                "message": "数据库查询失败",
                "search_name": name,
                "error": str(e),
            }
        except Exception as e:
            logger.error(f"获取仓库列表时发生未知错误: {str(e)}")
            return {
                "status": "error",
                "message": "获取仓库列表时发生未知错误",
                "search_name": name,
                "error": str(e),
            }
        finally:
            if should_close:
                db.close()

    @staticmethod
    def get_repository_by_exact_name(name: str, db: Session = None, include_tasks: bool = True) -> dict:
        """
        根据精确仓库名称获取仓库信息

        Args:
            name: 仓库名称（精确匹配）
            db: 数据库会话（可选）
            include_tasks: 是否包含分析任务信息

        Returns:
            dict: 包含仓库信息的字典
        """
        if db is None:
            db = SessionLocal()
            should_close = True
        else:
            should_close = False

        try:
            # 精确查询指定名称的仓库记录
            repository = db.query(Repository).filter(Repository.name == name).first()

            # 如果需要包含任务信息，手动查询任务
            if include_tasks and repository:
                tasks = (
                    db.query(AnalysisTask)
                    .filter(AnalysisTask.repository_id == repository.id)
                    .order_by(AnalysisTask.start_time.asc())
                    .all()
                )
                # 手动设置任务列表
                repository.analysis_tasks = tasks

            if not repository:
                return {
                    "status": "success",
                    "message": f"未找到名称为 '{name}' 的仓库记录",
                    "search_name": name,
                    "repository": None,
                }

            logger.info(f"成功获取仓库 '{name}' 的信息")

            return {
                "status": "success",
                "message": "仓库信息获取成功",
                "search_name": name,
                "repository": repository.to_dict(include_tasks=include_tasks),
            }

        except SQLAlchemyError as e:
            logger.error(f"数据库查询失败: {str(e)}")
            return {
                "status": "error",
                "message": "数据库查询失败",
                "search_name": name,
                "error": str(e),
            }
        except Exception as e:
            logger.error(f"获取仓库信息时发生未知错误: {str(e)}")
            return {
                "status": "error",
                "message": "获取仓库信息时发生未知错误",
                "search_name": name,
                "error": str(e),
            }
        finally:
            if should_close:
                db.close()

    @staticmethod
    def get_repository_by_name_or_full_name(
        name: Optional[str] = None, full_name: Optional[str] = None, db: Session = None, include_tasks: bool = True
    ) -> dict:
        """
        根据仓库名称或完整仓库名获取仓库信息

        Args:
            name: 仓库名称（精确匹配，可选）
            full_name: 完整仓库名（精确匹配，可选）
            db: 数据库会话（可选）
            include_tasks: 是否包含分析任务信息

        Returns:
            dict: 包含仓库信息的字典
        """
        if db is None:
            db = SessionLocal()
            should_close = True
        else:
            should_close = False

        try:
            # 验证参数
            if not name and not full_name:
                return {
                    "status": "error",
                    "message": "必须提供 name 或 full_name 参数",
                    "repository": None,
                }

            # 构建查询条件
            repository = None
            search_field = ""
            search_value = ""

            if full_name:
                # 优先使用 full_name 查询
                repository = db.query(Repository).filter(Repository.full_name == full_name).first()
                search_field = "full_name"
                search_value = full_name
            elif name:
                # 使用 name 查询
                repository = db.query(Repository).filter(Repository.name == name).first()
                search_field = "name"
                search_value = name

            # 如果需要包含任务信息，手动查询任务
            if include_tasks and repository:
                tasks = (
                    db.query(AnalysisTask)
                    .filter(AnalysisTask.repository_id == repository.id)
                    .order_by(AnalysisTask.start_time.asc())
                    .all()
                )
                # 手动设置任务列表
                repository.analysis_tasks = tasks

            if not repository:
                return {
                    "status": "success",
                    "message": f"未找到 {search_field} 为 '{search_value}' 的仓库记录",
                    "search_field": search_field,
                    "search_value": search_value,
                    "repository": None,
                }

            logger.info(f"成功获取仓库信息，{search_field}: '{search_value}'")

            return {
                "status": "success",
                "message": "仓库信息获取成功",
                "search_field": search_field,
                "search_value": search_value,
                "repository": repository.to_dict(include_tasks=include_tasks),
            }

        except SQLAlchemyError as e:
            logger.error(f"数据库查询失败: {str(e)}")
            return {
                "status": "error",
                "message": "数据库查询失败",
                "search_field": search_field if "search_field" in locals() else "unknown",
                "search_value": search_value if "search_value" in locals() else "unknown",
                "error": str(e),
            }
        except Exception as e:
            logger.error(f"获取仓库信息时发生未知错误: {str(e)}")
            return {
                "status": "error",
                "message": "获取仓库信息时发生未知错误",
                "search_field": search_field if "search_field" in locals() else "unknown",
                "search_value": search_value if "search_value" in locals() else "unknown",
                "error": str(e),
            }
        finally:
            if should_close:
                db.close()

    @staticmethod
    def get_repository_by_id(repository_id: int, db: Session = None, include_tasks: bool = True) -> dict:
        """
        根据仓库ID获取仓库信息

        Args:
            repository_id: 仓库ID
            db: 数据库会话（可选）
            include_tasks: 是否包含分析任务信息

        Returns:
            dict: 包含仓库信息的字典
        """
        if db is None:
            db = SessionLocal()
            should_close = True
        else:
            should_close = False

        try:
            # 查询指定ID的仓库记录
            repository = db.query(Repository).filter(Repository.id == repository_id).first()

            # 如果需要包含任务信息，手动查询任务
            if include_tasks and repository:
                tasks = (
                    db.query(AnalysisTask)
                    .filter(AnalysisTask.repository_id == repository.id)
                    .order_by(AnalysisTask.start_time.desc())
                    .all()
                )
                # 手动设置任务列表
                repository.analysis_tasks = tasks

            if not repository:
                return {
                    "status": "success",
                    "message": f"未找到ID为 {repository_id} 的仓库记录",
                    "repository_id": repository_id,
                    "repository": None,
                }

            logger.info(f"成功获取仓库ID {repository_id} 的信息")

            return {
                "status": "success",
                "message": "仓库信息获取成功",
                "repository_id": repository_id,
                "repository": repository.to_dict(include_tasks=include_tasks),
            }

        except SQLAlchemyError as e:
            logger.error(f"数据库查询失败: {str(e)}")
            return {
                "status": "error",
                "message": "数据库查询失败",
                "repository_id": repository_id,
                "error": str(e),
            }
        except Exception as e:
            logger.error(f"获取仓库信息时发生未知错误: {str(e)}")
            return {
                "status": "error",
                "message": "获取仓库信息时发生未知错误",
                "repository_id": repository_id,
                "error": str(e),
            }
        finally:
            if should_close:
                db.close()

    @staticmethod
    def create_repository(repository_data: dict, db: Session = None) -> dict:
        """
        创建新仓库

        Args:
            repository_data: 仓库数据字典
            db: 数据库会话（可选）

        Returns:
            dict: 包含创建结果的字典
        """
        if db is None:
            db = SessionLocal()
            should_close = True
        else:
            should_close = False

        try:
            # 检查是否已存在相同local_path的仓库
            existing_repo = (
                db.query(Repository).filter(Repository.local_path == repository_data.get("local_path")).first()
            )

            if existing_repo:
                return {
                    "status": "error",
                    "message": "该本地路径的仓库已存在",
                    "existing_repository": existing_repo.to_dict(include_tasks=False),
                }

            # 创建新仓库记录
            current_time = datetime.now(timezone.utc)
            new_repository = Repository(
                user_id=repository_data.get("user_id", 1),  # 默认用户ID为1
                name=repository_data["name"],
                full_name=repository_data.get("full_name"),
                local_path=repository_data["local_path"],
                status=repository_data.get("status", 1),
                created_at=current_time,
                updated_at=current_time,
            )

            db.add(new_repository)
            db.commit()
            db.refresh(new_repository)

            logger.info(f"成功创建仓库: {new_repository.name} (ID: {new_repository.id})")

            return {
                "status": "success",
                "message": "仓库创建成功",
                "repository": new_repository.to_dict(include_tasks=False),
            }

        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"数据库操作失败: {str(e)}")
            return {
                "status": "error",
                "message": "数据库操作失败",
                "error": str(e),
            }
        except Exception as e:
            db.rollback()
            logger.error(f"创建仓库时发生未知错误: {str(e)}")
            return {
                "status": "error",
                "message": "创建仓库时发生未知错误",
                "error": str(e),
            }
        finally:
            if should_close:
                db.close()

    @staticmethod
    def _calculate_repository_statistics(repositories: list) -> dict:
        """
        计算仓库统计信息

        Args:
            repositories: 仓库列表

        Returns:
            dict: 统计信息
        """
        statistics = {
            "by_status": {"active": 0, "deleted": 0},
            "by_user": {},
            "total_repositories": len(repositories),
            "has_full_name": 0,
        }

        for repo in repositories:
            # 按状态统计
            if repo.status == 1:
                statistics["by_status"]["active"] += 1
            else:
                statistics["by_status"]["deleted"] += 1

            # 按用户统计
            user_id = str(repo.user_id)
            statistics["by_user"][user_id] = statistics["by_user"].get(user_id, 0) + 1

            # 统计有完整名称的仓库
            if repo.full_name:
                statistics["has_full_name"] += 1

        return statistics

    @staticmethod
    def update_repository(repository_id: int, update_data: dict, db: Session = None) -> dict:
        """
        更新仓库信息

        Args:
            repository_id: 仓库ID
            update_data: 更新数据字典
            db: 数据库会话（可选）

        Returns:
            dict: 包含更新结果的字典
        """
        if db is None:
            db = SessionLocal()
            should_close = True
        else:
            should_close = False

        try:
            # 查询要更新的仓库
            repository = db.query(Repository).filter(Repository.id == repository_id).first()

            if not repository:
                return {
                    "status": "error",
                    "message": f"未找到ID为 {repository_id} 的仓库记录",
                    "repository_id": repository_id,
                }

            # 如果要更新local_path，检查是否与其他仓库冲突
            if "local_path" in update_data and update_data["local_path"] != repository.local_path:
                existing_repo = (
                    db.query(Repository)
                    .filter(Repository.local_path == update_data["local_path"], Repository.id != repository_id)
                    .first()
                )

                if existing_repo:
                    return {
                        "status": "error",
                        "message": "该本地路径已被其他仓库使用",
                        "conflicting_repository": existing_repo.to_dict(include_tasks=False),
                    }

            # 更新字段
            for field, value in update_data.items():
                if hasattr(repository, field):
                    setattr(repository, field, value)

            db.commit()
            db.refresh(repository)

            logger.info(f"成功更新仓库ID {repository_id} 的信息")

            return {
                "status": "success",
                "message": "仓库信息更新成功",
                "repository": repository.to_dict(include_tasks=False),
            }

        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"数据库操作失败: {str(e)}")
            return {
                "status": "error",
                "message": "数据库操作失败",
                "repository_id": repository_id,
                "error": str(e),
            }
        except Exception as e:
            db.rollback()
            logger.error(f"更新仓库信息时发生未知错误: {str(e)}")
            return {
                "status": "error",
                "message": "更新仓库信息时发生未知错误",
                "repository_id": repository_id,
                "error": str(e),
            }
        finally:
            if should_close:
                db.close()

    @staticmethod
    def get_repositories_list(
        user_id: int = None,
        status: int = None,
        order_by: str = "created_at",
        order_direction: str = "desc",
        page: int = 1,
        page_size: int = 10,
        db: Session = None,
    ) -> dict:
        """
        获取仓库列表，支持筛选、排序和分页

        Args:
            user_id: 用户ID筛选（可选）
            status: 状态筛选（可选）
            order_by: 排序字段，默认为created_at
            order_direction: 排序方向，asc或desc，默认为desc
            page: 页码，从1开始，默认为1
            page_size: 每页数量，默认为10
            db: 数据库会话（可选）

        Returns:
            dict: 包含仓库列表和分页信息的字典
        """
        if db is None:
            db = SessionLocal()
            should_close = True
        else:
            should_close = False

        try:
            # 验证排序字段
            valid_order_fields = ["id", "user_id", "name", "full_name", "status", "created_at", "updated_at"]
            if order_by not in valid_order_fields:
                return {
                    "status": "error",
                    "message": f"无效的排序字段: {order_by}，支持的字段: {', '.join(valid_order_fields)}",
                }

            # 验证排序方向
            if order_direction.lower() not in ["asc", "desc"]:
                return {
                    "status": "error",
                    "message": "排序方向必须是 'asc' 或 'desc'",
                }

            # 验证分页参数
            if page < 1:
                return {
                    "status": "error",
                    "message": "页码必须大于0",
                }

            if page_size < 1 or page_size > 100:
                return {
                    "status": "error",
                    "message": "每页数量必须在1-100之间",
                }

            # 构建基础查询
            query = db.query(Repository)

            # 添加筛选条件
            if user_id is not None:
                query = query.filter(Repository.user_id == user_id)

            if status is not None:
                query = query.filter(Repository.status == status)

            # 获取总数
            total_count = query.count()

            # 添加排序
            order_field = getattr(Repository, order_by)
            if order_direction.lower() == "asc":
                query = query.order_by(order_field.asc())
            else:
                query = query.order_by(order_field.desc())

            # 添加分页
            offset = (page - 1) * page_size
            repositories = query.offset(offset).limit(page_size).all()

            # 计算分页信息
            total_pages = (total_count + page_size - 1) // page_size
            has_next = page < total_pages
            has_prev = page > 1

            # 转换为字典格式
            repositories_data = [repo.to_dict(include_tasks=False) for repo in repositories]

            logger.info(f"成功获取仓库列表，总数: {total_count}，当前页: {page}/{total_pages}")

            return {
                "status": "success",
                "message": "仓库列表获取成功",
                "data": {
                    "repositories": repositories_data,
                    "pagination": {
                        "current_page": page,
                        "page_size": page_size,
                        "total_count": total_count,
                        "total_pages": total_pages,
                        "has_next": has_next,
                        "has_prev": has_prev,
                    },
                    "filters": {
                        "user_id": user_id,
                        "status": status,
                    },
                    "sorting": {
                        "order_by": order_by,
                        "order_direction": order_direction,
                    },
                },
            }

        except SQLAlchemyError as e:
            logger.error(f"数据库查询失败: {str(e)}")
            return {
                "status": "error",
                "message": "数据库查询失败",
                "error": str(e),
            }
        except Exception as e:
            logger.error(f"获取仓库列表时发生未知错误: {str(e)}")
            return {
                "status": "error",
                "message": "获取仓库列表时发生未知错误",
                "error": str(e),
            }
        finally:
            if should_close:
                db.close()

    @staticmethod
    def get_repository_by_id(repository_id: int, db: Session = None, include_tasks: bool = True) -> dict:
        """
        根据仓库ID获取仓库信息

        Args:
            repository_id: 仓库ID
            db: 数据库会话（可选）
            include_tasks: 是否包含分析任务信息

        Returns:
            dict: 包含仓库信息的字典
        """
        if db is None:
            db = SessionLocal()
            should_close = True
        else:
            should_close = False

        try:
            # 查询指定ID的仓库记录
            repository = db.query(Repository).filter(Repository.id == repository_id).first()

            # 如果需要包含任务信息，手动查询任务
            if include_tasks and repository:
                tasks = (
                    db.query(AnalysisTask)
                    .filter(AnalysisTask.repository_id == repository.id)
                    .order_by(AnalysisTask.start_time.desc())
                    .all()
                )
                # 手动设置任务列表
                repository.analysis_tasks = tasks

            if not repository:
                return {
                    "status": "success",
                    "message": f"未找到ID为 {repository_id} 的仓库记录",
                    "repository_id": repository_id,
                    "repository": None,
                }

            logger.info(f"成功获取仓库ID {repository_id} 的信息")

            return {
                "status": "success",
                "message": "仓库信息获取成功",
                "repository_id": repository_id,
                "repository": repository.to_dict(include_tasks=include_tasks),
            }

        except SQLAlchemyError as e:
            logger.error(f"数据库查询失败: {str(e)}")
            return {
                "status": "error",
                "message": "数据库查询失败",
                "repository_id": repository_id,
                "error": str(e),
            }
        except Exception as e:
            logger.error(f"获取仓库信息时发生未知错误: {str(e)}")
            return {
                "status": "error",
                "message": "获取仓库信息时发生未知错误",
                "repository_id": repository_id,
                "error": str(e),
            }
        finally:
            if should_close:
                db.close()

    @staticmethod
    def delete_repository(repository_id: int, db: Session = None, soft_delete: bool = True) -> dict:
        """
        删除仓库（支持软删除和硬删除）

        Args:
            repository_id: 仓库ID
            db: 数据库会话（可选）
            soft_delete: 是否软删除（True=设置status为0，False=物理删除）

        Returns:
            dict: 包含删除结果的字典
        """
        if db is None:
            db = SessionLocal()
            should_close = True
        else:
            should_close = False

        try:
            # 查询要删除的仓库
            repository = db.query(Repository).filter(Repository.id == repository_id).first()

            if not repository:
                return {
                    "status": "error",
                    "message": f"未找到ID为 {repository_id} 的仓库记录",
                    "repository_id": repository_id,
                }

            if soft_delete:
                # 软删除：设置status为0
                repository.status = 0
                db.commit()

                logger.info(f"成功软删除仓库ID {repository_id}")

                return {
                    "status": "success",
                    "message": "仓库已标记为删除状态",
                    "repository_id": repository_id,
                    "delete_type": "soft",
                    "repository": repository.to_dict(include_tasks=False),
                }
            else:
                # 硬删除：物理删除记录（注意：会级联删除相关的分析任务和文件分析记录）
                repository_data = repository.to_dict(include_tasks=False)
                db.delete(repository)
                db.commit()

                logger.info(f"成功硬删除仓库ID {repository_id}")

                return {
                    "status": "success",
                    "message": "仓库已物理删除",
                    "repository_id": repository_id,
                    "delete_type": "hard",
                    "deleted_repository": repository_data,
                }

        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"数据库操作失败: {str(e)}")
            return {
                "status": "error",
                "message": "数据库操作失败",
                "repository_id": repository_id,
                "error": str(e),
            }
        except Exception as e:
            db.rollback()
            logger.error(f"删除仓库时发生未知错误: {str(e)}")
            return {
                "status": "error",
                "message": "删除仓库时发生未知错误",
                "repository_id": repository_id,
                "error": str(e),
            }
        finally:
            if should_close:
                db.close()


class TaskReadmeService:
    """任务README服务类"""

    @staticmethod
    def create_task_readme(readme_data: dict, db: Session = None) -> dict:
        """
        创建任务README记录

        Args:
            readme_data: README数据字典
            db: 数据库会话（可选）

        Returns:
            dict: 包含创建结果的字典
        """
        if db is None:
            db = SessionLocal()
            should_close = True
        else:
            should_close = False

        try:
            # 验证task_id是否存在
            task = db.query(AnalysisTask).filter(AnalysisTask.id == readme_data["task_id"]).first()
            if not task:
                return {
                    "status": "error",
                    "message": f"任务ID {readme_data['task_id']} 不存在",
                    "task_id": readme_data["task_id"],
                }
            converter = MermaidToSvgConverter(use_cli=True)
            try:
                rendered_content = converter.convert_markdown(readme_data["content"])
            except Exception as e:
                logger.error(f"转换Markdown时发生错误: {str(e)}")
                rendered_content = readme_data["content"]
            # 创建新的README记录
            new_readme = TaskReadme(
                task_id=readme_data["task_id"],
                content=readme_data["content"],
                rendered_content=rendered_content,
            )

            db.add(new_readme)
            db.commit()
            db.refresh(new_readme)

            logger.info(f"成功创建任务README记录，ID: {new_readme.id}")

            return {
                "status": "success",
                "message": "任务README创建成功",
                "readme": new_readme.to_dict(),
            }

        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"数据库操作失败: {str(e)}")
            return {
                "status": "error",
                "message": "数据库操作失败",
                "error": str(e),
            }
        except Exception as e:
            db.rollback()
            logger.error(f"创建任务README记录时发生未知错误: {str(e)}")
            return {
                "status": "error",
                "message": "创建任务README记录时发生未知错误",
                "error": str(e),
            }
        finally:
            if should_close:
                db.close()

    @staticmethod
    def get_task_readme_by_id(readme_id: int, db: Session = None) -> dict:
        """
        根据README ID获取README记录

        Args:
            readme_id: README ID
            db: 数据库会话（可选）

        Returns:
            dict: 包含README信息的字典
        """
        if db is None:
            db = SessionLocal()
            should_close = True
        else:
            should_close = False

        try:
            readme = db.query(TaskReadme).filter(TaskReadme.id == readme_id).first()

            if not readme:
                return {
                    "status": "success",
                    "message": f"未找到ID为 {readme_id} 的README记录",
                    "readme_id": readme_id,
                    "readme": None,
                }

            logger.info(f"成功获取README ID {readme_id} 的信息")

            return {
                "status": "success",
                "message": "README信息获取成功",
                "readme_id": readme_id,
                "readme": readme.to_dict(),
            }

        except SQLAlchemyError as e:
            logger.error(f"数据库操作失败: {str(e)}")
            return {
                "status": "error",
                "message": "数据库操作失败",
                "readme_id": readme_id,
                "error": str(e),
            }
        except Exception as e:
            logger.error(f"获取README记录时发生未知错误: {str(e)}")
            return {
                "status": "error",
                "message": "获取README记录时发生未知错误",
                "readme_id": readme_id,
                "error": str(e),
            }
        finally:
            if should_close:
                db.close()

    @staticmethod
    def get_task_readme_by_task_id(task_id: int, db: Session = None) -> dict:
        """
        根据任务ID获取README记录

        Args:
            task_id: 任务ID
            db: 数据库会话（可选）

        Returns:
            dict: 包含README信息的字典
        """
        if db is None:
            db = SessionLocal()
            should_close = True
        else:
            should_close = False

        try:
            # 验证任务是否存在
            task = db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
            if not task:
                return {
                    "status": "error",
                    "message": f"任务ID {task_id} 不存在",
                    "task_id": task_id,
                }

            # 查询该任务的README记录（按创建时间倒序，获取最新的）
            readme = (
                db.query(TaskReadme)
                .filter(TaskReadme.task_id == task_id)
                .order_by(TaskReadme.created_at.desc())
                .first()
            )

            if not readme:
                return {
                    "status": "success",
                    "message": f"未找到任务ID为 {task_id} 的README记录",
                    "task_id": task_id,
                    "readme": None,
                }

            logger.info(f"成功获取任务ID {task_id} 的README信息")

            return {
                "status": "success",
                "message": "README信息获取成功",
                "task_id": task_id,
                "readme": readme.to_dict(),
            }

        except SQLAlchemyError as e:
            logger.error(f"数据库操作失败: {str(e)}")
            return {
                "status": "error",
                "message": "数据库操作失败",
                "task_id": task_id,
                "error": str(e),
            }
        except Exception as e:
            logger.error(f"获取README记录时发生未知错误: {str(e)}")
            return {
                "status": "error",
                "message": "获取README记录时发生未知错误",
                "task_id": task_id,
                "error": str(e),
            }
        finally:
            if should_close:
                db.close()

    @staticmethod
    def update_task_readme(readme_id: int, readme_data: dict, db: Session = None) -> dict:
        """
        更新任务README记录

        Args:
            readme_id: README ID
            readme_data: 更新数据字典
            db: 数据库会话（可选）

        Returns:
            dict: 包含更新结果的字典
        """
        if db is None:
            db = SessionLocal()
            should_close = True
        else:
            should_close = False

        try:
            # 查询要更新的README记录
            readme = db.query(TaskReadme).filter(TaskReadme.id == readme_id).first()

            if not readme:
                return {
                    "status": "error",
                    "message": f"未找到ID为 {readme_id} 的README记录",
                    "readme_id": readme_id,
                }

            # 如果提供了task_id，验证任务是否存在
            if "task_id" in readme_data:
                task = db.query(AnalysisTask).filter(AnalysisTask.id == readme_data["task_id"]).first()
                if not task:
                    return {
                        "status": "error",
                        "message": f"任务ID {readme_data['task_id']} 不存在",
                        "task_id": readme_data["task_id"],
                    }

            # 更新字段
            for field, value in readme_data.items():
                if hasattr(readme, field):
                    setattr(readme, field, value)

            db.commit()
            db.refresh(readme)

            logger.info(f"成功更新README记录ID {readme_id}")

            return {
                "status": "success",
                "message": "README记录更新成功",
                "readme_id": readme_id,
                "readme": readme.to_dict(),
            }

        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"数据库操作失败: {str(e)}")
            return {
                "status": "error",
                "message": "数据库操作失败",
                "readme_id": readme_id,
                "error": str(e),
            }
        except Exception as e:
            db.rollback()
            logger.error(f"更新README记录时发生未知错误: {str(e)}")
            return {
                "status": "error",
                "message": "更新README记录时发生未知错误",
                "readme_id": readme_id,
                "error": str(e),
            }
        finally:
            if should_close:
                db.close()

    @staticmethod
    def delete_task_readme(readme_id: int, db: Session = None) -> dict:
        """
        删除任务README记录

        Args:
            readme_id: README ID
            db: 数据库会话（可选）

        Returns:
            dict: 包含删除结果的字典
        """
        if db is None:
            db = SessionLocal()
            should_close = True
        else:
            should_close = False

        try:
            # 查询要删除的README记录
            readme = db.query(TaskReadme).filter(TaskReadme.id == readme_id).first()

            if not readme:
                return {
                    "status": "error",
                    "message": f"未找到ID为 {readme_id} 的README记录",
                    "readme_id": readme_id,
                }

            # 保存README数据用于返回
            readme_data = readme.to_dict()

            # 物理删除记录
            db.delete(readme)
            db.commit()

            logger.info(f"成功删除README记录ID {readme_id}")

            return {
                "status": "success",
                "message": "README记录已删除",
                "readme_id": readme_id,
                "deleted_readme": readme_data,
            }

        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"数据库操作失败: {str(e)}")
            return {
                "status": "error",
                "message": "数据库操作失败",
                "readme_id": readme_id,
                "error": str(e),
            }
        except Exception as e:
            db.rollback()
            logger.error(f"删除README记录时发生未知错误: {str(e)}")
            return {
                "status": "error",
                "message": "删除README记录时发生未知错误",
                "readme_id": readme_id,
                "error": str(e),
            }
        finally:
            if should_close:
                db.close()


class AnalysisTaskService:
    """分析任务服务类"""

    @staticmethod
    def get_tasks_by_repository_id(
        repository_id: int, db: Session = None, order_by: str = "start_time", order_direction: str = "asc"
    ) -> dict:
        """
        根据repository_id获取分析任务列表

        Args:
            repository_id: 仓库ID
            db: 数据库会话（可选）
            order_by: 排序字段 (start_time, end_time, status, total_files)
            order_direction: 排序方向 (asc, desc)

        Returns:
            dict: 包含分析任务列表和统计信息的字典
        """
        # 如果没有传入数据库会话，创建新的会话
        if db is None:
            db = SessionLocal()
            should_close = True
        else:
            should_close = False

        try:
            # 验证排序字段
            valid_order_fields = [
                "start_time",
                "end_time",
                "status",
                "total_files",
                "successful_files",
                "failed_files",
                "code_lines",
                "module_count",
                "id",
            ]
            if order_by not in valid_order_fields:
                order_by = "start_time"

            # 验证排序方向
            if order_direction.lower() not in ["asc", "desc"]:
                order_direction = "asc"

            # 获取排序字段属性
            order_field = getattr(AnalysisTask, order_by)

            # 查询指定repository_id的所有分析任务记录
            query = db.query(AnalysisTask).filter(AnalysisTask.repository_id == repository_id)

            # 处理排序，特别处理end_time的NULL值
            if order_by == "end_time":
                if order_direction.lower() == "asc":
                    # MySQL中NULL值在ASC排序时排在前面，我们希望排在后面
                    # 使用ISNULL函数让NULL值排在最后
                    from sqlalchemy import text

                    query = query.order_by(text("ISNULL(end_time), end_time ASC"))
                else:
                    # DESC排序时NULL值自然排在前面，这是我们想要的
                    query = query.order_by(order_field.desc())
            else:
                # 其他字段正常排序
                if order_direction.lower() == "asc":
                    query = query.order_by(order_field.asc())
                else:
                    query = query.order_by(order_field.desc())

            tasks = query.all()

            if not tasks:
                return {
                    "status": "success",
                    "message": f"未找到repository_id为 {repository_id} 的分析任务记录",
                    "repository_id": repository_id,
                    "total_tasks": 0,
                    "tasks": [],
                    "statistics": {
                        "by_status": {},
                        "total_files": 0,
                        "total_successful_files": 0,
                        "total_failed_files": 0,
                        "average_success_rate": 0,
                        "latest_task": None,
                        "running_tasks": 0,
                    },
                }

            # 转换为字典格式
            task_list = [task.to_dict() for task in tasks]

            # 统计信息
            statistics = AnalysisTaskService._calculate_task_statistics(tasks)

            logger.info(f"成功获取repository_id {repository_id} 的分析任务列表，共 {len(tasks)} 个任务")

            return {
                "status": "success",
                "message": "分析任务列表获取成功",
                "repository_id": repository_id,
                "total_tasks": len(tasks),
                "tasks": task_list,
                "statistics": statistics,
            }

        except SQLAlchemyError as e:
            logger.error(f"数据库查询失败: {str(e)}")
            return {
                "status": "error",
                "message": "数据库查询失败",
                "repository_id": repository_id,
                "error": str(e),
            }
        except Exception as e:
            logger.error(f"获取分析任务列表时发生未知错误: {str(e)}")
            return {
                "status": "error",
                "message": "获取分析任务列表时发生未知错误",
                "repository_id": repository_id,
                "error": str(e),
            }
        finally:
            if should_close:
                db.close()

    @staticmethod
    def _calculate_task_statistics(tasks: list) -> dict:
        """
        计算分析任务统计信息

        Args:
            tasks: 分析任务列表

        Returns:
            dict: 统计信息
        """
        statistics = {
            "by_status": {},
            "total_files": 0,
            "total_successful_files": 0,
            "total_failed_files": 0,
            "total_code_lines": 0,
            "total_module_count": 0,
            "average_success_rate": 0,
            "latest_task": None,
            "running_tasks": 0,
        }

        if not tasks:
            return statistics

        total_success_rate = 0
        tasks_with_files = 0

        for task in tasks:
            # 按状态统计
            status = task.status or "unknown"
            statistics["by_status"][status] = statistics["by_status"].get(status, 0) + 1

            # 统计文件数和其他指标
            if task.total_files:
                statistics["total_files"] += task.total_files
            if task.successful_files:
                statistics["total_successful_files"] += task.successful_files
            if task.failed_files:
                statistics["total_failed_files"] += task.failed_files
            if task.code_lines:
                statistics["total_code_lines"] += task.code_lines
            if task.module_count:
                statistics["total_module_count"] += task.module_count

            # 计算成功率
            if task.total_files and task.total_files > 0:
                success_rate = (task.successful_files or 0) / task.total_files * 100
                total_success_rate += success_rate
                tasks_with_files += 1

            # 统计运行中的任务
            if status in ["pending", "running"]:
                statistics["running_tasks"] += 1

        # 计算平均成功率
        if tasks_with_files > 0:
            statistics["average_success_rate"] = round(total_success_rate / tasks_with_files, 2)

        # 最新任务信息（按start_time找最新的）
        if tasks:
            latest_task = max(
                tasks, key=lambda t: t.start_time if t.start_time else datetime.min.replace(tzinfo=timezone.utc)
            )
            statistics["latest_task"] = {
                "id": latest_task.id,
                "status": latest_task.status,
                "start_time": latest_task.start_time.isoformat() if latest_task.start_time else None,
                "end_time": latest_task.end_time.isoformat() if latest_task.end_time else None,
            }

        return statistics

    @staticmethod
    def create_analysis_task(task_data: dict,external_file_path: str, db: Session = None) -> dict:
        """
        创建新的分析任务

        Args:
            task_data: 任务数据字典
            db: 数据库会话（可选）

        Returns:
            dict: 包含创建结果的字典
        """
        # 延迟导入避免循环依赖
        import service.task_service as TaskService
        
        if db is None:
            db = SessionLocal()
            should_close = True
        else:
            should_close = False

        try:
            # 验证repository_id是否存在
            repository = db.query(Repository).filter(Repository.id == task_data["repository_id"]).first()
            if not repository:
                return {
                    "status": "error",
                    "message": f"仓库ID {task_data['repository_id']} 不存在",
                    "repository_id": task_data["repository_id"],
                }

            # 检查是否有pending或running状态的任务
            existing_pending_tasks = (
                db.query(AnalysisTask).filter(AnalysisTask.status.in_(["pending", "running"])).count()
            )

            # 创建新任务记录
            # 如果传入了start_time，使用传入的时间；否则使用当前时间
            start_time = task_data.get("start_time")
            if start_time is None:
                start_time = datetime.now(timezone.utc)
            elif isinstance(start_time, str):
                # 如果是字符串，尝试解析为datetime对象
                try:
                    start_time = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                except ValueError:
                    start_time = datetime.now(timezone.utc)

            # 根据队列情况决定任务状态
            # 如果有pending或running任务，新任务自动设为pending状态
            task_status = "pending"
            if existing_pending_tasks == 0:
                # 如果没有其他任务在队列中，可以直接设为running状态
                task_status = task_data.get("status", "running")

            new_task = AnalysisTask(
                repository_id=task_data["repository_id"],
                total_files=task_data.get("total_files", 0),
                successful_files=task_data.get("successful_files", 0),
                failed_files=task_data.get("failed_files", 0),
                code_lines=task_data.get("code_lines", 0),
                module_count=task_data.get("module_count", 0),
                status=task_status,
                start_time=start_time,
                end_time=task_data.get("end_time"),
                task_index=task_data.get("task_index"),
            )

            db.add(new_task)
            db.commit()
            db.refresh(new_task)
            
            # 创建同步包装函数来运行异步任务
            def run_task_sync(task_id,external_file_path):
                import asyncio
                asyncio.run(TaskService.run_task(task_id,external_file_path,))
            
            import threading
            threading.Thread(target=run_task_sync, args=(new_task.id,external_file_path), daemon=True).start()

            logger.info(f"成功创建分析任务: ID {new_task.id}, 仓库ID {new_task.repository_id}, 状态: {task_status}")

            # 返回结果包含队列信息
            result = {
                "status": "success",
                "message": "分析任务创建成功",
                "task": new_task.to_dict(),
                "queue_info": {
                    "is_queued": task_status == "pending",
                    "queue_position": existing_pending_tasks + 1 if task_status == "pending" else 0,
                    "total_pending": existing_pending_tasks + (1 if task_status == "pending" else 0),
                },
            }

            return result

        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"数据库操作失败: {str(e)}")
            return {
                "status": "error",
                "message": "数据库操作失败",
                "error": str(e),
            }
        except Exception as e:
            db.rollback()
            logger.error(f"创建分析任务时发生未知错误: {str(e)}")
            return {
                "status": "error",
                "message": "创建分析任务时发生未知错误",
                "error": str(e),
            }
        finally:
            if should_close:
                db.close()

    @staticmethod
    def update_analysis_task(task_id: int, update_data: dict, db: Session = None) -> dict:
        """
        更新分析任务信息

        Args:
            task_id: 任务ID
            update_data: 更新数据字典
            db: 数据库会话（可选）

        Returns:
            dict: 包含更新结果的字典
        """
        if db is None:
            db = SessionLocal()
            should_close = True
        else:
            should_close = False

        try:
            # 查询要更新的任务
            task = db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()

            if not task:
                return {
                    "status": "error",
                    "message": f"未找到ID为 {task_id} 的分析任务记录",
                    "task_id": task_id,
                }

            # 如果要更新repository_id，检查是否存在
            if "repository_id" in update_data:
                repository = db.query(Repository).filter(Repository.id == update_data["repository_id"]).first()
                if not repository:
                    return {
                        "status": "error",
                        "message": f"仓库ID {update_data['repository_id']} 不存在",
                        "repository_id": update_data["repository_id"],
                    }

            # 更新字段
            for field, value in update_data.items():
                if hasattr(task, field):
                    # 特殊处理日期时间字段
                    if field in ["start_time", "end_time"] and isinstance(value, str):
                        try:
                            # 解析ISO格式的日期时间字符串
                            # 处理带有Z后缀的ISO格式（UTC时间）
                            if value.endswith("Z"):
                                value = value[:-1] + "+00:00"
                            # 解析为datetime对象
                            parsed_datetime = datetime.fromisoformat(value)
                            setattr(task, field, parsed_datetime)
                            logger.info(f"成功解析日期时间字段 {field}: {value} -> {parsed_datetime}")
                        except ValueError as e:
                            logger.error(f"日期时间格式解析失败: {field}={value}, 错误: {str(e)}")
                            # 如果解析失败，跳过这个字段
                            continue
                    else:
                        setattr(task, field, value)

            db.commit()
            db.refresh(task)

            logger.info(f"成功更新分析任务ID {task_id} 的信息")

            return {
                "status": "success",
                "message": "分析任务信息更新成功",
                "task": task.to_dict(),
            }

        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"数据库操作失败: {str(e)}")
            return {
                "status": "error",
                "message": "数据库操作失败",
                "task_id": task_id,
                "error": str(e),
            }
        except Exception as e:
            db.rollback()
            logger.error(f"更新分析任务时发生未知错误: {str(e)}")
            return {
                "status": "error",
                "message": "更新分析任务时发生未知错误",
                "task_id": task_id,
                "error": str(e),
            }
        finally:
            if should_close:
                db.close()

    @staticmethod
    def delete_analysis_task(task_id: int, db: Session = None) -> dict:
        """
        删除分析任务（硬删除，会级联删除相关的文件分析记录）

        Args:
            task_id: 任务ID
            db: 数据库会话（可选）

        Returns:
            dict: 包含删除结果的字典
        """
        if db is None:
            db = SessionLocal()
            should_close = True
        else:
            should_close = False

        try:
            # 查询要删除的任务
            task = db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()

            if not task:
                return {
                    "status": "error",
                    "message": f"未找到ID为 {task_id} 的分析任务记录",
                    "task_id": task_id,
                }

            # 保存任务数据用于返回
            task_data = task.to_dict()

            # 物理删除记录（会级联删除相关的文件分析记录）
            db.delete(task)
            db.commit()

            logger.info(f"成功删除分析任务ID {task_id}")

            return {
                "status": "success",
                "message": "分析任务已删除",
                "task_id": task_id,
                "deleted_task": task_data,
            }

        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"数据库操作失败: {str(e)}")
            return {
                "status": "error",
                "message": "数据库操作失败",
                "task_id": task_id,
                "error": str(e),
            }
        except Exception as e:
            db.rollback()
            logger.error(f"删除分析任务时发生未知错误: {str(e)}")
            return {
                "status": "error",
                "message": "删除分析任务时发生未知错误",
                "task_id": task_id,
                "error": str(e),
            }
        finally:
            if should_close:
                db.close()

    @staticmethod
    def can_start_task(task_id: int, db: Session = None) -> dict:
        """
        判断指定任务是否可以开启

        判断条件：
        1. 当前没有状态为 running 的任务
        2. 指定的 task_id 在状态为 pending 的任务中是 start_time 最早的

        Args:
            task_id: 要判断的任务ID
            db: 数据库会话（可选）

        Returns:
            dict: 包含判断结果的字典
        """
        if db is None:
            db = SessionLocal()
            should_close = True
        else:
            should_close = False

        try:
            # 检查是否存在 running 状态的任务
            running_tasks_count = db.query(AnalysisTask).filter(AnalysisTask.status == "running").count()

            if running_tasks_count > 0:
                return {
                    "status": "success",
                    "message": "当前有正在运行的任务，无法开启新任务",
                    "task_id": task_id,
                    "can_start": False,
                    "reason": "有正在运行的任务",
                    "running_tasks_count": running_tasks_count,
                }

            # 查找指定的任务
            target_task = db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()

            if not target_task:
                return {
                    "status": "error",
                    "message": f"未找到ID为 {task_id} 的任务",
                    "task_id": task_id,
                    "can_start": False,
                }

            # 检查任务状态是否为 pending
            if target_task.status != "pending":
                return {
                    "status": "success",
                    "message": f"任务状态为 {target_task.status}，不是 pending 状态",
                    "task_id": task_id,
                    "can_start": False,
                    "reason": f"任务状态不是pending，当前状态：{target_task.status}",
                    "current_status": target_task.status,
                }

            # 查找所有 pending 状态的任务，按 start_time 升序排列
            pending_tasks = (
                db.query(AnalysisTask)
                .filter(AnalysisTask.status == "pending")
                .order_by(AnalysisTask.start_time.asc())
                .all()
            )

            if not pending_tasks:
                return {
                    "status": "success",
                    "message": "没有pending状态的任务",
                    "task_id": task_id,
                    "can_start": False,
                    "reason": "没有pending状态的任务",
                }

            # 检查指定任务是否是最早的 pending 任务
            earliest_task = pending_tasks[0]

            if earliest_task.id == task_id:
                return {
                    "status": "success",
                    "message": "任务可以开启",
                    "task_id": task_id,
                    "can_start": True,
                    "reason": "没有运行中的任务且该任务是最早的pending任务",
                    "earliest_start_time": earliest_task.start_time.isoformat() if earliest_task.start_time else None,
                    "pending_tasks_count": len(pending_tasks),
                }
            else:
                return {
                    "status": "success",
                    "message": "任务不能开启，不是最早的pending任务",
                    "task_id": task_id,
                    "can_start": False,
                    "reason": "不是最早的pending任务",
                    "earliest_task_id": earliest_task.id,
                    "earliest_start_time": earliest_task.start_time.isoformat() if earliest_task.start_time else None,
                    "current_task_start_time": target_task.start_time.isoformat() if target_task.start_time else None,
                    "pending_tasks_count": len(pending_tasks),
                }

        except Exception as e:
            logger.error(f"判断任务是否可以开启时发生错误: {str(e)}")
            return {
                "status": "error",
                "message": f"判断任务是否可以开启时发生错误: {str(e)}",
                "task_id": task_id,
                "can_start": False,
            }
        finally:
            if should_close:
                db.close()

    @staticmethod
    def get_queue_status(db: Session = None) -> dict:
        """
        获取任务队列状态

        Args:
            db: 数据库会话（可选）

        Returns:
            dict: 包含队列状态信息的字典
        """
        if db is None:
            db = SessionLocal()
            should_close = True
        else:
            should_close = False

        try:
            # 获取所有pending状态的任务，按创建时间排序
            pending_tasks = (
                db.query(AnalysisTask)
                .filter(AnalysisTask.status == "pending")
                .order_by(AnalysisTask.start_time.asc())
                .all()
            )

            # 获取正在运行的任务数量
            running_tasks = db.query(AnalysisTask).filter(AnalysisTask.status == "running").count()

            # 计算队列信息
            total_pending = len(pending_tasks)

            # 预估等待时间（假设每个任务平均需要15分钟）
            average_task_duration = 15  # 分钟
            estimated_wait_time = total_pending * average_task_duration

            # 如果有正在运行的任务，减少等待时间
            if running_tasks > 0:
                estimated_wait_time = max(0, estimated_wait_time - (running_tasks * 5))

            logger.info(f"队列状态查询成功: pending={total_pending}, running={running_tasks}")

            return {
                "status": "success",
                "message": "队列状态获取成功",
                "queue_info": {
                    "total_pending": total_pending,
                    "running_tasks": running_tasks,
                    "estimated_wait_time_minutes": estimated_wait_time,
                    "has_queue": total_pending > 0,
                    "pending_task_ids": [task.id for task in pending_tasks],
                },
            }

        except SQLAlchemyError as e:
            logger.error(f"数据库操作失败: {str(e)}")
            return {
                "status": "error",
                "message": "数据库操作失败",
                "error": str(e),
            }
        except Exception as e:
            logger.error(f"获取队列状态时发生未知错误: {str(e)}")
            return {
                "status": "error",
                "message": "获取队列状态时发生未知错误",
                "error": str(e),
            }
        finally:
            if should_close:
                db.close()

    @staticmethod
    def get_task_by_id(task_id: int, db: Session = None) -> dict:
        """
        根据任务ID获取分析任务详细信息
        
        Args:
            task_id: 分析任务ID
            db: 数据库会话（可选）
            
        Returns:
            dict: 包含任务详细信息的字典
        """
        if db is None:
            db = SessionLocal()
            should_close = True
        else:
            should_close = False
            
        try:
            # 查询任务
            task = db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
            
            if not task:
                return {
                    "status": "error",
                    "message": f"未找到ID为 {task_id} 的分析任务",
                    "task_id": task_id,
                }
            
            # 转换为字典格式
            task_dict = task.to_dict()
            
            return {
                "status": "success", 
                "message": "获取任务信息成功",
                "task": task_dict,
                "task_id": task_id,
            }
            
        except Exception as e:
            logger.error(f"获取任务信息时发生错误: {str(e)}")
            return {
                "status": "error",
                "message": "获取任务信息时发生未知错误",
                "task_id": task_id,
                "error": str(e),
            }
        finally:
            if should_close:
                db.close()


class UploadService:
    """文件上传服务类"""

    @staticmethod
    async def upload_repository_files(files: list, repository_name: str, db: Session = None) -> dict:
        """
        上传整个仓库文件夹到本地存储

        Args:
            files: 上传的文件列表（包含完整文件夹结构）
            repository_name: 仓库名称
            db: 数据库会话（可选）

        Returns:
            dict: 包含上传结果和文件夹结构分析的字典
        """
        import os
        import shutil
        import hashlib
        from pathlib import Path
        from config import settings

        should_close = False
        if db is None:
            db = SessionLocal()
            should_close = True

        try:
            # 验证仓库名称
            if not repository_name or not repository_name.strip():
                return {
                    "status": "error",
                    "message": "仓库名称不能为空",
                    "repository_name": repository_name,
                }

            # 清理仓库名称，移除特殊字符
            clean_repo_name = "".join(c for c in repository_name if c.isalnum() or c in ("-", "_", ".")).strip()
            if not clean_repo_name:
                return {
                    "status": "error",
                    "message": "仓库名称包含无效字符",
                    "repository_name": repository_name,
                }

            # 计算文件内容的MD5哈希值来生成唯一的目录名
            # 添加时间戳和随机数确保每次上传都生成不同的MD5
            import time
            import random

            md5_hash = hashlib.md5()

            # 添加当前时间戳（纳秒级精度）
            timestamp = str(time.time_ns())
            md5_hash.update(timestamp.encode("utf-8"))

            # 添加随机数增加唯一性
            random_num = str(random.randint(100000, 999999))
            md5_hash.update(random_num.encode("utf-8"))

            # 先读取所有文件内容来计算MD5，并缓存内容以避免重复读取
            file_contents = []
            for file in files:
                content = await file.read()
                file_contents.append((file.filename, content))
                md5_hash.update(content)
                # 注意：不再尝试重置文件指针，而是使用缓存的内容

            # 生成MD5目录名
            md5_dir_name = md5_hash.hexdigest()
            logger.info(f"生成MD5目录名: {md5_dir_name} (基于时间戳: {timestamp}, 随机数: {random_num})")

            # 创建本地存储目录，使用MD5作为目录名
            repo_path = Path(settings.LOCAL_REPO_PATH) / md5_dir_name

            # 如果目录已存在，先删除
            if repo_path.exists():
                logger.info(f"删除已存在的MD5目录: {repo_path}")
                shutil.rmtree(repo_path)

            repo_path.mkdir(parents=True, exist_ok=True)

            # 保存上传的文件并分析文件夹结构
            saved_files = []
            failed_files = []
            folder_structure = {}
            file_types = {}
            total_size = 0

            logger.info(f"开始处理 {len(files)} 个文件的上传")

            # 检测根文件夹名称（用于移除重复嵌套）
            root_folder_name = None
            if files:
                # 从第一个文件路径中提取根文件夹名称
                first_file_path = files[0].filename
                if first_file_path and "/" in first_file_path:
                    root_folder_name = first_file_path.split("/")[0]
                    logger.info(f"检测到根文件夹: {root_folder_name}")

            # 打印前几个文件的详细信息用于调试
            for i, (filename, content) in enumerate(file_contents[:5]):
                logger.info(f"文件 {i}: filename={filename}, content_size={len(content)} bytes")

            # 使用缓存的文件内容进行处理，避免重复读取
            for i, (filename, cached_content) in enumerate(file_contents):
                try:
                    # 获取文件的相对路径（前端上传时会保持目录结构）
                    file_path = filename
                    if not file_path:
                        logger.warning("跳过空文件名的文件")
                        continue

                    # 移除根文件夹路径，避免重复嵌套
                    if root_folder_name and file_path.startswith(root_folder_name + "/"):
                        relative_file_path = file_path[len(root_folder_name) + 1 :]
                    else:
                        relative_file_path = file_path

                    # 如果处理后路径为空，跳过
                    if not relative_file_path:
                        logger.warning(f"处理后路径为空，跳过文件: {file_path}")
                        continue

                    logger.debug(f"处理文件: {file_path} -> {relative_file_path}")

                    # 创建完整的文件路径
                    full_file_path = repo_path / relative_file_path

                    logger.debug(f"完整文件路径: {full_file_path}")

                    # 确保父目录存在
                    full_file_path.parent.mkdir(parents=True, exist_ok=True)

                    # 使用缓存的文件内容，避免重复读取
                    content = cached_content
                    file_size = len(content)

                    with open(full_file_path, "wb") as f:
                        f.write(content)

                    # 分析文件信息
                    file_extension = full_file_path.suffix.lower().lstrip(".")
                    if not file_extension:
                        file_extension = "no_extension"

                    # 统计文件类型
                    file_types[file_extension] = file_types.get(file_extension, 0) + 1
                    total_size += file_size

                    # 分析文件夹结构（使用处理后的相对路径）
                    path_parts = Path(relative_file_path).parts
                    current_level = folder_structure
                    for part in path_parts[:-1]:  # 排除文件名，只处理文件夹
                        if part not in current_level:
                            current_level[part] = {}
                        current_level = current_level[part]

                    saved_files.append(
                        {
                            "filename": filename,
                            "size": file_size,
                            "path": str(full_file_path.relative_to(repo_path)),
                            "extension": file_extension,
                            "relative_path": relative_file_path,  # 使用处理后的路径
                            "original_path": file_path,  # 保留原始路径用于调试
                        }
                    )

                    logger.debug(f"成功保存文件: {relative_file_path} ({file_size} bytes)")

                except Exception as e:
                    logger.error(f"保存文件失败 {filename}: {str(e)}")
                    failed_files.append({"filename": filename, "error": str(e)})

            # 检查是否有文件成功保存
            if not saved_files:
                return {
                    "status": "error",
                    "message": "没有文件成功保存",
                    "repository_name": repository_name,
                    "failed_files": failed_files,
                }

            # 检查仓库是否已存在于数据库中（使用MD5目录名作为唯一标识）
            existing_repo = db.query(Repository).filter(Repository.local_path == str(repo_path)).first()

            current_time = datetime.now(timezone.utc)

            if existing_repo:
                # 更新现有仓库信息
                existing_repo.name = clean_repo_name  # 更新仓库名称
                existing_repo.full_name = md5_dir_name  # 直接使用MD5信息
                existing_repo.status = 1  # 设置为存在状态
                existing_repo.updated_at = current_time
                repository = existing_repo
                logger.info(f"更新已存在的仓库记录: {existing_repo.id}")
            else:
                # 创建新的仓库记录，使用MD5目录名作为唯一标识
                repository = Repository(
                    user_id=1,  # 默认用户ID
                    name=clean_repo_name,  # 使用原始仓库名称
                    full_name=md5_dir_name,  # 直接使用MD5信息
                    local_path=str(repo_path),  # 使用MD5目录路径
                    status=1,
                    created_at=current_time,
                    updated_at=current_time,
                )
                db.add(repository)
                logger.info(f"创建新的仓库记录，MD5目录: {md5_dir_name}")

            # 提交数据库更改
            db.commit()
            db.refresh(repository)

            # 生成文件夹统计信息
            folder_stats = UploadService._analyze_folder_structure(folder_structure, file_types, total_size)

            logger.info(
                f"成功上传仓库 '{clean_repo_name}'，共保存 {len(saved_files)} 个文件，总大小 {total_size} bytes"
            )

            # 自动压缩并上传到README API
            compress_upload_result = None
            try:
                logger.info(f"开始自动压缩并上传md5文件夹: {md5_dir_name}")

                # 创建临时zip文件
                import tempfile
                import os
                temp_dir = tempfile.gettempdir()
                zip_path = os.path.join(temp_dir, f"{md5_dir_name}.zip")
                

                # 压缩文件夹
                compress_success = UploadService.create_zip_from_folder(str(repo_path), zip_path)

                if compress_success:
                    # 上传到README API
                    upload_result = await UploadService.upload_zip_to_readme_api(
                        zip_path,
                        settings.README_API_BASE_URL
                    )

                    if upload_result["success"]:
                        logger.info(f"✅ 自动上传到README API成功: {upload_result}")
                        compress_upload_result = {
                            "status": "success",
                            "message": "自动压缩并上传成功",
                            "upload_data": upload_result["data"]
                        }
                    else:
                        logger.warning(f"⚠️ 自动上传到README API失败: {upload_result['message']}")
                        compress_upload_result = {
                            "status": "error",
                            "message": f"自动上传失败: {upload_result['message']}"
                        }
                else:
                    logger.warning("⚠️ 自动压缩失败")
                    compress_upload_result = {
                        "status": "error",
                        "message": "自动压缩失败"
                    }

                # 清理临时文件
                try:
                    import os
                    os.unlink(zip_path)
                except Exception as cleanup_error:
                    logger.warning(f"清理临时文件失败: {cleanup_error}")

            except Exception as auto_upload_error:
                logger.error(f"自动压缩上传过程中发生错误: {auto_upload_error}")
                compress_upload_result = {
                    "status": "error",
                    "message": f"自动压缩上传失败: {str(auto_upload_error)}"
                }

            return {
                "status": "success",
                "message": "仓库文件夹上传成功",
                "repository_name": clean_repo_name,
                "repository_id": repository.id,
                "local_path": str(repo_path),
                "md5_directory_name": md5_dir_name,  # 添加MD5目录名信息
                "upload_summary": {
                    "total_files_uploaded": len(files),
                    "successful_files": len(saved_files),
                    "failed_files": len(failed_files),
                    "total_size_bytes": total_size,
                    "total_size_formatted": UploadService._format_file_size(total_size),
                },
                "folder_structure": folder_structure,
                "file_analysis": folder_stats,
                "sample_files": saved_files[:10],  # 前10个文件的详情
                "errors": failed_files if failed_files else None,
                "auto_compress_upload": compress_upload_result,  # 添加自动压缩上传结果
            }

        except Exception as e:
            logger.error(f"上传仓库文件时发生错误: {str(e)}")
            return {
                "status": "error",
                "message": "上传仓库文件时发生未知错误",
                "repository_name": repository_name,
                "error": str(e),
            }
        finally:
            if should_close:
                db.close()

    @staticmethod
    def _analyze_folder_structure(folder_structure: dict, file_types: dict, total_size: int) -> dict:
        """
        分析文件夹结构和文件类型统计

        Args:
            folder_structure: 文件夹结构字典
            file_types: 文件类型统计
            total_size: 总文件大小

        Returns:
            dict: 分析结果
        """
        # 分类文件类型
        code_extensions = {
            "py",
            "js",
            "ts",
            "jsx",
            "tsx",
            "java",
            "cpp",
            "c",
            "h",
            "hpp",
            "cs",
            "php",
            "rb",
            "go",
            "rs",
            "swift",
            "kt",
            "scala",
            "r",
            "vue",
            "html",
            "htm",
            "css",
            "scss",
            "sass",
            "less",
        }

        config_extensions = {
            "json",
            "yml",
            "yaml",
            "xml",
            "ini",
            "conf",
            "config",
            "toml",
            "env",
            "properties",
            "cfg",
            "settings",
        }

        doc_extensions = {"md", "txt", "rst", "adoc", "doc", "docx", "pdf"}

        image_extensions = {"png", "jpg", "jpeg", "gif", "svg", "webp", "ico", "bmp"}

        # 统计各类文件
        code_files = sum(count for ext, count in file_types.items() if ext in code_extensions)
        config_files = sum(count for ext, count in file_types.items() if ext in config_extensions)
        doc_files = sum(count for ext, count in file_types.items() if ext in doc_extensions)
        image_files = sum(count for ext, count in file_types.items() if ext in image_extensions)
        other_files = sum(file_types.values()) - (code_files + config_files + doc_files + image_files)

        # 计算文件夹深度
        max_depth = UploadService._calculate_folder_depth(folder_structure)

        return {
            "file_type_summary": {
                "code_files": code_files,
                "config_files": config_files,
                "documentation_files": doc_files,
                "image_files": image_files,
                "other_files": other_files,
            },
            "file_extensions": dict(sorted(file_types.items(), key=lambda x: x[1], reverse=True)),
            "folder_depth": max_depth,
            "folder_count": UploadService._count_folders(folder_structure),
            "is_likely_code_project": code_files > 0 and (code_files + config_files) > len(file_types) * 0.3,
        }

    @staticmethod
    def _calculate_folder_depth(folder_structure: dict, current_depth: int = 0) -> int:
        """计算文件夹最大深度"""
        if not folder_structure:
            return current_depth

        max_depth = current_depth
        for subfolder in folder_structure.values():
            if isinstance(subfolder, dict):
                depth = UploadService._calculate_folder_depth(subfolder, current_depth + 1)
                max_depth = max(max_depth, depth)

        return max_depth

    @staticmethod
    def _count_folders(folder_structure: dict) -> int:
        """计算文件夹总数"""
        count = len(folder_structure)
        for subfolder in folder_structure.values():
            if isinstance(subfolder, dict):
                count += UploadService._count_folders(subfolder)
        return count

    @staticmethod
    def _format_file_size(size_bytes: int) -> str:
        """格式化文件大小"""
        if size_bytes == 0:
            return "0 B"

        size_names = ["B", "KB", "MB", "GB", "TB"]
        import math

        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return f"{s} {size_names[i]}"

    @staticmethod
    def create_zip_from_folder(folder_path: str, zip_path: str) -> bool:
        """
        将文件夹压缩成zip文件

        Args:
            folder_path: 要压缩的文件夹路径
            zip_path: 输出的zip文件路径

        Returns:
            bool: 是否成功创建zip文件
        """
        try:
            import os

            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(folder_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        # 计算相对路径，避免包含完整的绝对路径
                        arcname = os.path.relpath(file_path, folder_path)
                        zipf.write(file_path, arcname)

            logger.info(f"✅ 成功创建zip文件: {zip_path}")
            return True

        except Exception as e:
            logger.error(f"❌ 创建zip文件失败: {e}")
            return False

    @staticmethod
    async def upload_zip_to_readme_api(zip_path: str, readme_api_base_url: str) -> dict:
        """
        将zip文件上传到README API服务

        Args:
            zip_path: zip文件路径
            readme_api_base_url: README API的基础URL

        Returns:
            dict: 上传结果
        """
        try:
            import os

            if not os.path.exists(zip_path):
                return {
                    "success": False,
                    "message": f"Zip文件不存在: {zip_path}"
                }

            upload_url = f"{readme_api_base_url}/api/upload/zip"

            async with httpx.AsyncClient(timeout=300.0) as client:
                with open(zip_path, 'rb') as f:
                    files = {
                        'file': (os.path.basename(zip_path), f, 'application/zip')
                    }

                    logger.info(f"🚀 开始上传zip文件到: {upload_url}")
                    response = await client.post(upload_url, files=files)

                    if response.status_code == 200:
                        result = response.json()
                        logger.info(f"✅ zip文件上传成功: {result}")
                        return {
                            "success": True,
                            "message": "上传成功",
                            "data": result
                        }
                    else:
                        error_msg = f"HTTP {response.status_code}: {response.text}"
                        logger.error(f"❌ zip文件上传失败: {error_msg}")
                        return {
                            "success": False,
                            "message": error_msg
                        }

        except Exception as e:
            logger.error(f"❌ 上传zip文件时出错: {e}")
            return {
                "success": False,
                "message": f"上传失败: {str(e)}"
            }
