"""
API路由定义
"""

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from database import get_db
from services import FileAnalysisService, AnalysisItemService, RepositoryService, AnalysisTaskService
from typing import Optional

# 创建路由器
repository_router = APIRouter(prefix="/api/repository", tags=["仓库管理"])


@repository_router.get("/files/{task_id}")
async def get_repository_files(
    task_id: str,
    db: Session = Depends(get_db),
    include_statistics: bool = Query(True, description="是否包含统计信息"),
    status_filter: Optional[str] = Query(None, description="按分析状态过滤: success, failed"),
    language_filter: Optional[str] = Query(None, description="按编程语言过滤"),
    limit: Optional[int] = Query(None, description="限制返回文件数量", ge=1, le=1000),
    offset: Optional[int] = Query(0, description="跳过的文件数量", ge=0),
):
    """
    获取指定任务ID的仓库文件列表

    Args:
        task_id: 任务ID
        db: 数据库会话
        include_statistics: 是否包含统计信息
        status_filter: 状态过滤器
        language_filter: 语言过滤器
        limit: 限制返回数量
        offset: 偏移量

    Returns:
        JSON响应包含文件列表和统计信息
    """
    try:
        # 获取文件列表
        result = FileAnalysisService.get_files_by_task_id(task_id, db)

        if result["status"] == "error":
            return JSONResponse(status_code=500, content=result)

        # 如果没有找到文件
        if result["total_files"] == 0:
            return JSONResponse(status_code=404, content=result)

        files = result["files"]

        # 应用过滤器
        if status_filter:
            files = [f for f in files if f.get("analysis_status") == status_filter]

        if language_filter:
            files = [f for f in files if f.get("language") == language_filter]

        # 应用分页
        total_filtered = len(files)
        if offset:
            files = files[offset:]
        if limit:
            files = files[:limit]

        # 构建响应
        response_data = {
            "status": "success",
            "message": "文件列表获取成功",
            "task_id": task_id,
            "total_files": result["total_files"],
            "filtered_files": total_filtered,
            "returned_files": len(files),
            "files": files,
        }

        # 添加分页信息
        if limit or offset:
            response_data["pagination"] = {
                "limit": limit,
                "offset": offset,
                "has_more": offset + len(files) < total_filtered,
            }

        # 添加统计信息
        if include_statistics:
            response_data["statistics"] = result["statistics"]

        return JSONResponse(status_code=200, content=response_data)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": "获取文件列表时发生未知错误", "task_id": task_id, "error": str(e)},
        )


@repository_router.get("/analysis-items/{file_analysis_id}")
async def get_file_analysis_items(
    file_analysis_id: int,
    db: Session = Depends(get_db),
    include_statistics: bool = Query(True, description="是否包含统计信息"),
    language_filter: Optional[str] = Query(None, description="按编程语言过滤"),
    has_code_only: bool = Query(False, description="仅返回包含代码的分析项"),
    limit: Optional[int] = Query(None, description="限制返回分析项数量", ge=1, le=1000),
    offset: Optional[int] = Query(0, description="跳过的分析项数量", ge=0),
):
    """
    获取指定文件分析ID的分析项详细内容

    Args:
        file_analysis_id: 文件分析ID
        db: 数据库会话
        include_statistics: 是否包含统计信息
        language_filter: 语言过滤器
        has_code_only: 仅返回包含代码的项目
        limit: 限制返回数量
        offset: 偏移量

    Returns:
        JSON响应包含分析项列表和统计信息
    """
    try:
        # 获取分析项列表
        result = AnalysisItemService.get_analysis_items_by_file_id(file_analysis_id, db)

        if result["status"] == "error":
            return JSONResponse(status_code=500, content=result)

        # 如果没有找到分析项
        if result["total_items"] == 0:
            return JSONResponse(status_code=404, content=result)

        items = result["items"]

        # 应用过滤器
        if language_filter:
            items = [item for item in items if item.get("language") == language_filter]

        if has_code_only:
            items = [item for item in items if item.get("code")]

        # 应用分页
        total_filtered = len(items)
        if offset:
            items = items[offset:]
        if limit:
            items = items[:limit]

        # 构建响应
        response_data = {
            "status": "success",
            "message": "分析项列表获取成功",
            "file_analysis_id": file_analysis_id,
            "total_items": result["total_items"],
            "filtered_items": total_filtered,
            "returned_items": len(items),
            "items": items,
        }

        # 添加分页信息
        if limit or offset:
            response_data["pagination"] = {
                "limit": limit,
                "offset": offset,
                "has_more": offset + len(items) < total_filtered,
            }

        # 添加统计信息
        if include_statistics:
            response_data["statistics"] = result["statistics"]

        return JSONResponse(status_code=200, content=response_data)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "获取分析项列表时发生未知错误",
                "file_analysis_id": file_analysis_id,
                "error": str(e),
            },
        )


@repository_router.get("/repositories")
async def get_repositories_by_name(
    name: str = Query(..., description="仓库名称（支持模糊匹配）"),
    db: Session = Depends(get_db),
    exact_match: bool = Query(False, description="是否精确匹配"),
    include_statistics: bool = Query(True, description="是否包含统计信息"),
    include_tasks: bool = Query(True, description="是否包含分析任务信息"),
    limit: Optional[int] = Query(None, description="限制返回仓库数量", ge=1, le=100),
    offset: Optional[int] = Query(0, description="跳过的仓库数量", ge=0),
):
    """
    根据仓库名称查询仓库信息

    Args:
        name: 仓库名称
        db: 数据库会话
        exact_match: 是否精确匹配
        include_statistics: 是否包含统计信息
        include_tasks: 是否包含分析任务信息
        limit: 限制返回数量
        offset: 偏移量

    Returns:
        JSON响应包含仓库信息
    """
    try:
        if exact_match:
            # 精确匹配查询
            result = RepositoryService.get_repository_by_exact_name(name, db, include_tasks)

            if result["status"] == "error":
                return JSONResponse(status_code=500, content=result)

            if not result.get("repository"):
                return JSONResponse(status_code=404, content=result)

            return JSONResponse(status_code=200, content=result)

        else:
            # 模糊匹配查询
            result = RepositoryService.get_repository_by_name(name, db, include_tasks)

            if result["status"] == "error":
                return JSONResponse(status_code=500, content=result)

            if result["total_repositories"] == 0:
                return JSONResponse(status_code=404, content=result)

            repositories = result["repositories"]

            # 应用分页
            total_filtered = len(repositories)
            if offset:
                repositories = repositories[offset:]
            if limit:
                repositories = repositories[:limit]

            # 构建响应
            response_data = {
                "status": "success",
                "message": "仓库列表获取成功",
                "search_name": name,
                "total_repositories": result["total_repositories"],
                "filtered_repositories": total_filtered,
                "returned_repositories": len(repositories),
                "repositories": repositories,
            }

            # 添加分页信息
            if limit or offset:
                response_data["pagination"] = {
                    "limit": limit,
                    "offset": offset,
                    "has_more": offset + len(repositories) < total_filtered,
                }

            # 添加统计信息
            if include_statistics:
                response_data["statistics"] = result["statistics"]

            return JSONResponse(status_code=200, content=response_data)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "查询仓库信息时发生未知错误",
                "search_name": name,
                "error": str(e),
            },
        )


@repository_router.get("/analysis-tasks/{repository_id}")
async def get_analysis_tasks_by_repository(
    repository_id: int,
    db: Session = Depends(get_db),
    order_by: str = Query("start_time", description="排序字段: start_time, end_time, status, total_files, id"),
    order_direction: str = Query("asc", description="排序方向: asc, desc"),
):
    """
    根据仓库ID获取分析任务列表

    Args:
        repository_id: 仓库ID
        db: 数据库会话
        order_by: 排序字段
        order_direction: 排序方向

    Returns:
        JSON响应包含分析任务列表和统计信息
    """
    try:
        # 获取分析任务列表
        result = AnalysisTaskService.get_tasks_by_repository_id(repository_id, db, order_by, order_direction)

        if result["status"] == "error":
            return JSONResponse(status_code=500, content=result)

        # 如果没有找到分析任务
        if result["total_tasks"] == 0:
            return JSONResponse(status_code=404, content=result)

        return JSONResponse(status_code=200, content=result)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "获取分析任务列表时发生未知错误",
                "repository_id": repository_id,
                "error": str(e),
            },
        )
