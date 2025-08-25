"""
业务服务层
"""

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from models import FileAnalysis, AnalysisItem, Repository, AnalysisTask

from database import SessionLocal
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class FileAnalysisService:
    """文件分析服务类"""

    @staticmethod
    def get_files_by_task_id(task_id: str, db: Session = None) -> dict:
        """
        根据task_id获取文件列表

        Args:
            task_id: 任务ID
            db: 数据库会话（可选）

        Returns:
            dict: 包含文件列表和统计信息的字典
        """
        # 如果没有传入数据库会话，创建新的会话
        if db is None:
            db = SessionLocal()
            should_close = True
        else:
            should_close = False

        try:
            # 查询指定task_id的所有文件分析记录
            files = (
                db.query(FileAnalysis).filter(FileAnalysis.task_id == task_id).order_by(FileAnalysis.file_path).all()
            )

            if not files:
                return {
                    "status": "success",
                    "message": f"未找到task_id为 {task_id} 的文件记录",
                    "task_id": task_id,
                    "total_files": 0,
                    "files": [],
                    "statistics": {"by_language": {}, "by_status": {}, "by_file_type": {}, "total_size": 0},
                }

            # 转换为字典格式
            file_list = [file.to_dict() for file in files]

            # 统计信息
            statistics = FileAnalysisService._calculate_statistics(files)

            logger.info(f"成功获取task_id {task_id} 的文件列表，共 {len(files)} 个文件")

            return {
                "status": "success",
                "message": "文件列表获取成功",
                "task_id": task_id,
                "total_files": len(files),
                "files": file_list,
                "statistics": statistics,
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


class AnalysisItemService:
    """分析项服务类"""

    @staticmethod
    def get_analysis_items_by_file_id(file_analysis_id: int, db: Session = None) -> dict:
        """
        根据file_analysis_id获取分析项列表

        Args:
            file_analysis_id: 文件分析ID
            db: 数据库会话（可选）

        Returns:
            dict: 包含分析项列表和统计信息的字典
        """
        # 如果没有传入数据库会话，创建新的会话
        if db is None:
            db = SessionLocal()
            should_close = True
        else:
            should_close = False

        try:
            # 查询指定file_analysis_id的所有分析项记录
            items = (
                db.query(AnalysisItem)
                .filter(AnalysisItem.file_analysis_id == file_analysis_id)
                .order_by(AnalysisItem.start_line, AnalysisItem.created_at)
                .all()
            )

            if not items:
                return {
                    "status": "success",
                    "message": f"未找到file_analysis_id为 {file_analysis_id} 的分析项记录",
                    "file_analysis_id": file_analysis_id,
                    "total_items": 0,
                    "items": [],
                    "statistics": {
                        "by_language": {},
                        "by_search_target": {},
                        "total_code_lines": 0,
                        "has_code_items": 0,
                        "has_description_items": 0,
                    },
                }

            # 转换为字典格式
            item_list = [item.to_dict() for item in items]

            # 统计信息
            statistics = AnalysisItemService._calculate_item_statistics(items)

            logger.info(f"成功获取file_analysis_id {file_analysis_id} 的分析项列表，共 {len(items)} 个项目")

            return {
                "status": "success",
                "message": "分析项列表获取成功",
                "file_analysis_id": file_analysis_id,
                "total_items": len(items),
                "items": item_list,
                "statistics": statistics,
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
    def _calculate_repository_statistics(repositories: list) -> dict:
        """
        计算仓库统计信息

        Args:
            repositories: 仓库列表

        Returns:
            dict: 统计信息
        """
        statistics = {
            "by_language": {},
            "has_description": 0,
            "has_url": 0,
            "total_repositories": len(repositories),
        }

        for repo in repositories:
            # 按编程语言统计
            language = repo.language or "unknown"
            statistics["by_language"][language] = statistics["by_language"].get(language, 0) + 1

            # 统计有描述的仓库
            if repo.description:
                statistics["has_description"] += 1

            # 统计有URL的仓库
            if repo.url:
                statistics["has_url"] += 1

        return statistics


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
            valid_order_fields = ["start_time", "end_time", "status", "total_files", "id"]
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

            # 统计文件数
            if task.total_files:
                statistics["total_files"] += task.total_files
            if task.successful_files:
                statistics["total_successful_files"] += task.successful_files
            if task.failed_files:
                statistics["total_failed_files"] += task.failed_files

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
