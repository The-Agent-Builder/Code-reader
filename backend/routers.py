"""
API路由定义
"""

from fastapi import APIRouter, Depends, Query, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from database import get_db
from services import FileAnalysisService, AnalysisItemService, RepositoryService, AnalysisTaskService, UploadService
from models import AnalysisTask, Repository
from typing import Optional, List
from pydantic import BaseModel, Field
import logging

# 设置logger
logger = logging.getLogger(__name__)


# Pydantic模型定义
class RepositoryCreate(BaseModel):
    """创建仓库的请求模型"""

    user_id: Optional[int] = Field(default=1, description="用户ID，默认为1")
    name: str = Field(..., min_length=1, max_length=255, description="仓库名称")
    full_name: Optional[str] = Field(None, max_length=255, description="完整仓库名")
    local_path: str = Field(..., min_length=1, max_length=1024, description="本地仓库路径")
    status: Optional[int] = Field(default=1, description="状态：1=存在，0=已删除")


class RepositoryUpdate(BaseModel):
    """更新仓库的请求模型"""

    user_id: Optional[int] = Field(None, description="用户ID")
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="仓库名称")
    full_name: Optional[str] = Field(None, max_length=255, description="完整仓库名")
    local_path: Optional[str] = Field(None, min_length=1, max_length=1024, description="本地仓库路径")
    status: Optional[int] = Field(None, description="状态：1=存在，0=已删除")


class AnalysisTaskCreate(BaseModel):
    """创建分析任务的请求模型"""

    repository_id: int = Field(..., description="仓库ID")
    total_files: Optional[int] = Field(default=0, description="总文件数")
    successful_files: Optional[int] = Field(default=0, description="成功分析文件数")
    failed_files: Optional[int] = Field(default=0, description="失败文件数")
    code_lines: Optional[int] = Field(default=0, description="代码行数")
    module_count: Optional[int] = Field(default=0, description="模块数量")
    status: Optional[str] = Field(default="pending", description="任务状态：pending/running/completed/failed")
    start_time: Optional[str] = Field(None, description="开始时间（ISO格式）")
    end_time: Optional[str] = Field(None, description="结束时间（ISO格式）")
    task_index: Optional[str] = Field(None, description="任务索引")


class AnalysisTaskUpdate(BaseModel):
    """更新分析任务的请求模型"""

    repository_id: Optional[int] = Field(None, description="仓库ID")
    total_files: Optional[int] = Field(None, description="总文件数")
    successful_files: Optional[int] = Field(None, description="成功分析文件数")
    failed_files: Optional[int] = Field(None, description="失败文件数")
    code_lines: Optional[int] = Field(None, description="代码行数")
    module_count: Optional[int] = Field(None, description="模块数量")
    status: Optional[str] = Field(None, description="任务状态：pending/running/completed/failed")
    start_time: Optional[str] = Field(None, description="开始时间（ISO格式）")
    end_time: Optional[str] = Field(None, description="结束时间（ISO格式）")
    task_index: Optional[str] = Field(None, description="任务索引")


class FileAnalysisCreate(BaseModel):
    """创建文件分析记录的请求模型"""

    task_id: int = Field(..., description="分析任务ID")
    file_path: str = Field(..., min_length=1, max_length=1024, description="文件路径")
    language: Optional[str] = Field(None, max_length=64, description="编程语言")
    analysis_version: Optional[str] = Field(default="1.0", max_length=32, description="分析版本")
    status: Optional[str] = Field(default="pending", description="分析状态：pending/success/failed")
    code_lines: Optional[int] = Field(default=0, description="代码行数")
    code_content: Optional[str] = Field(None, description="代码内容")
    file_analysis: Optional[str] = Field(None, description="文件分析结果")
    dependencies: Optional[str] = Field(None, description="依赖模块列表")
    error_message: Optional[str] = Field(None, description="错误信息")


class FileAnalysisUpdate(BaseModel):
    """更新文件分析记录的请求模型"""

    task_id: Optional[int] = Field(None, description="分析任务ID")
    file_path: Optional[str] = Field(None, min_length=1, max_length=1024, description="文件路径")
    language: Optional[str] = Field(None, max_length=64, description="编程语言")
    analysis_version: Optional[str] = Field(None, max_length=32, description="分析版本")
    status: Optional[str] = Field(None, description="分析状态：pending/success/failed")
    code_lines: Optional[int] = Field(None, description="代码行数")
    code_content: Optional[str] = Field(None, description="代码内容")
    file_analysis: Optional[str] = Field(None, description="文件分析结果")
    dependencies: Optional[str] = Field(None, description="依赖模块列表")
    error_message: Optional[str] = Field(None, description="错误信息")


class AnalysisItemCreate(BaseModel):
    """创建分析项记录的请求模型"""

    file_analysis_id: int = Field(..., description="文件分析ID")
    title: str = Field(..., min_length=1, max_length=512, description="标题")
    description: Optional[str] = Field(None, description="描述")
    target_type: Optional[str] = Field(None, max_length=32, description="目标类型：file/class/function")
    target_name: Optional[str] = Field(None, max_length=255, description="目标名称（类名/函数名）")
    source: Optional[str] = Field(None, max_length=1024, description="源码位置")
    language: Optional[str] = Field(None, max_length=64, description="编程语言")
    code: Optional[str] = Field(None, description="代码片段")
    start_line: Optional[int] = Field(None, description="起始行号")
    end_line: Optional[int] = Field(None, description="结束行号")


class AnalysisItemUpdate(BaseModel):
    """更新分析项记录的请求模型"""

    file_analysis_id: Optional[int] = Field(None, description="文件分析ID")
    title: Optional[str] = Field(None, min_length=1, max_length=512, description="标题")
    description: Optional[str] = Field(None, description="描述")
    target_type: Optional[str] = Field(None, max_length=32, description="目标类型：file/class/function")
    target_name: Optional[str] = Field(None, max_length=255, description="目标名称（类名/函数名）")
    source: Optional[str] = Field(None, max_length=1024, description="源码位置")
    language: Optional[str] = Field(None, max_length=64, description="编程语言")
    code: Optional[str] = Field(None, description="代码片段")
    start_line: Optional[int] = Field(None, description="起始行号")
    end_line: Optional[int] = Field(None, description="结束行号")


# 创建路由器
repository_router = APIRouter(prefix="/api/repository", tags=["仓库管理"])


@repository_router.get("/repositories/{repository_id}")
async def get_repository_by_id(
    repository_id: int,
    db: Session = Depends(get_db),
    include_tasks: bool = Query(True, description="是否包含分析任务信息"),
):
    """
    根据仓库ID获取仓库详细信息

    Args:
        repository_id: 仓库ID
        db: 数据库会话
        include_tasks: 是否包含分析任务信息

    Returns:
        JSON响应包含仓库详细信息
    """
    try:
        # 获取仓库信息
        result = RepositoryService.get_repository_by_id(repository_id, db, include_tasks=include_tasks)

        if result["status"] == "error":
            return JSONResponse(status_code=500, content=result)

        if not result.get("repository"):
            return JSONResponse(status_code=404, content=result)

        return JSONResponse(status_code=200, content=result)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "获取仓库信息时发生未知错误",
                "repository_id": repository_id,
                "error": str(e),
            },
        )


@repository_router.get("/repositories")
async def get_repository_by_name(
    name: str = Query(..., description="仓库名称（精确匹配）"),
    db: Session = Depends(get_db),
):
    """
    根据仓库名称精确查询仓库信息

    Args:
        name: 仓库名称（精确匹配）
        db: 数据库会话

    Returns:
        JSON响应包含仓库信息
    """
    try:
        # 精确匹配查询
        result = RepositoryService.get_repository_by_exact_name(name, db, include_tasks=False)

        if result["status"] == "error":
            return JSONResponse(status_code=500, content=result)

        if not result.get("repository"):
            return JSONResponse(status_code=404, content=result)

        return JSONResponse(status_code=200, content=result)

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


@repository_router.post("/repositories")
async def create_repository(
    repository_data: RepositoryCreate,
    db: Session = Depends(get_db),
):
    """
    创建新仓库

    Args:
        repository_data: 仓库创建数据
        db: 数据库会话

    Returns:
        JSON响应包含创建的仓库信息
    """
    try:
        # 转换为字典
        data_dict = repository_data.model_dump()

        # 创建仓库
        result = RepositoryService.create_repository(data_dict, db)

        if result["status"] == "error":
            return JSONResponse(status_code=400, content=result)

        return JSONResponse(status_code=201, content=result)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "创建仓库时发生未知错误",
                "error": str(e),
            },
        )


@repository_router.get("/analysis-tasks/{repository_id}")
async def get_analysis_tasks_by_repository(
    repository_id: int,
    db: Session = Depends(get_db),
    order_by: str = Query(
        "start_time",
        description="排序字段: start_time, end_time, status, total_files, successful_files, failed_files, code_lines, module_count, id",
    ),
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


@repository_router.post("/analysis-tasks")
async def create_analysis_task(
    task_data: AnalysisTaskCreate,
    db: Session = Depends(get_db),
):
    """
    创建新的分析任务

    Args:
        task_data: 分析任务创建数据
        db: 数据库会话

    Returns:
        JSON响应包含创建的分析任务信息
    """
    try:
        # 转换为字典
        data_dict = task_data.model_dump()

        # 创建分析任务
        result = AnalysisTaskService.create_analysis_task(data_dict, db)

        if result["status"] == "error":
            return JSONResponse(status_code=400, content=result)

        return JSONResponse(status_code=201, content=result)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "创建分析任务时发生未知错误",
                "error": str(e),
            },
        )


@repository_router.put("/analysis-tasks/{task_id}")
async def update_analysis_task(
    task_id: int,
    task_data: AnalysisTaskUpdate,
    db: Session = Depends(get_db),
):
    """
    更新分析任务信息

    Args:
        task_id: 分析任务ID
        task_data: 分析任务更新数据
        db: 数据库会话

    Returns:
        JSON响应包含更新后的分析任务信息
    """
    try:
        # 转换为字典，排除None值
        data_dict = task_data.model_dump(exclude_none=True)

        if not data_dict:
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "message": "没有提供要更新的字段",
                    "task_id": task_id,
                },
            )

        # 更新分析任务
        result = AnalysisTaskService.update_analysis_task(task_id, data_dict, db)

        if result["status"] == "error":
            if "未找到" in result["message"]:
                return JSONResponse(status_code=404, content=result)
            else:
                return JSONResponse(status_code=400, content=result)

        return JSONResponse(status_code=200, content=result)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "更新分析任务时发生未知错误",
                "task_id": task_id,
                "error": str(e),
            },
        )


@repository_router.delete("/analysis-tasks/{task_id}")
async def delete_analysis_task(
    task_id: int,
    db: Session = Depends(get_db),
):
    """
    删除分析任务

    Args:
        task_id: 分析任务ID
        db: 数据库会话

    Returns:
        JSON响应包含删除结果
    """
    try:
        # 删除分析任务
        result = AnalysisTaskService.delete_analysis_task(task_id, db)

        if result["status"] == "error":
            if "未找到" in result["message"]:
                return JSONResponse(status_code=404, content=result)
            else:
                return JSONResponse(status_code=500, content=result)

        return JSONResponse(status_code=200, content=result)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "删除分析任务时发生未知错误",
                "task_id": task_id,
                "error": str(e),
            },
        )


@repository_router.get("/analysis-tasks/{task_id}/can-start")
async def can_start_analysis_task(
    task_id: int,
    db: Session = Depends(get_db),
):
    """
    判断分析任务是否可以开启

    判断指定的任务ID是否满足开启条件：
    1. 当前没有状态为 running 的任务
    2. 指定的 task_id 在状态为 pending 的任务中是 start_time 最早的

    Args:
        task_id: 要判断的任务ID
        db: 数据库会话

    Returns:
        JSON响应包含判断结果：
        - can_start: boolean，是否可以开启
        - reason: string，判断原因
        - 其他相关信息
    """
    try:
        # 判断任务是否可以开启
        result = AnalysisTaskService.can_start_task(task_id, db)

        if result["status"] == "error":
            if "未找到" in result["message"]:
                return JSONResponse(status_code=404, content=result)
            else:
                return JSONResponse(status_code=500, content=result)

        return JSONResponse(status_code=200, content=result)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"判断任务是否可以开启时发生错误: {str(e)}",
                "task_id": task_id,
                "can_start": False,
                "error": str(e),
            },
        )


@repository_router.get("/analysis-tasks/queue/status")
async def get_queue_status(
    db: Session = Depends(get_db),
):
    """
    获取任务队列状态

    Args:
        db: 数据库会话

    Returns:
        JSON响应包含队列状态信息
    """
    try:
        # 获取队列状态
        result = AnalysisTaskService.get_queue_status(db)

        if result["status"] == "error":
            return JSONResponse(status_code=500, content=result)

        return JSONResponse(status_code=200, content=result)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "获取队列状态时发生未知错误",
                "error": str(e),
            },
        )


@repository_router.get("/files/{task_id}")
async def get_repository_files(
    task_id: int,
    db: Session = Depends(get_db),
    language: Optional[str] = Query(None, description="按编程语言过滤"),
    analysis_version: Optional[str] = Query(None, description="按分析版本过滤"),
    status: Optional[str] = Query(None, description="按分析状态过滤: pending, success, failed"),
    include_code_content: bool = Query(False, description="是否返回代码内容"),
):
    """
    获取指定任务ID的仓库文件列表

    Args:
        task_id: 任务ID
        db: 数据库会话
        language: 编程语言过滤器
        analysis_version: 分析版本过滤器
        status: 状态过滤器
        include_code_content: 是否返回代码内容

    Returns:
        JSON响应包含文件列表
    """
    try:
        # 获取文件列表
        result = FileAnalysisService.get_files_by_task_id(
            task_id,
            db,
            language=language,
            analysis_version=analysis_version,
            status=status,
            include_code_content=include_code_content,
        )

        if result["status"] == "error":
            return JSONResponse(status_code=500, content=result)

        # 如果没有找到文件
        if result["total_files"] == 0:
            return JSONResponse(status_code=404, content=result)

        return JSONResponse(status_code=200, content=result)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": "获取文件列表时发生未知错误", "task_id": task_id, "error": str(e)},
        )


@repository_router.get("/file-analysis/{file_id}")
async def get_file_analysis_by_id(
    file_id: int,
    task_id: int = Query(..., description="任务ID"),
    db: Session = Depends(get_db),
):
    """
    根据文件分析ID和任务ID获取单条文件分析记录的完整内容

    Args:
        file_id: 文件分析记录ID
        task_id: 任务ID
        db: 数据库会话

    Returns:
        JSON响应包含完整的文件分析记录
    """
    try:
        # 获取文件分析记录
        result = FileAnalysisService.get_file_analysis_by_id_and_task_id(file_id, task_id, db)

        if result["status"] == "error":
            return JSONResponse(status_code=500, content=result)

        # 如果没有找到记录
        if not result.get("file_analysis"):
            return JSONResponse(status_code=404, content=result)

        return JSONResponse(status_code=200, content=result)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "获取文件分析记录时发生未知错误",
                "file_id": file_id,
                "task_id": task_id,
                "error": str(e),
            },
        )


@repository_router.post("/file-analysis")
async def create_file_analysis(
    file_data: FileAnalysisCreate,
    db: Session = Depends(get_db),
):
    """
    创建新的文件分析记录

    Args:
        file_data: 文件分析创建数据
        db: 数据库会话

    Returns:
        JSON响应包含创建的文件分析记录信息
    """
    try:
        # 转换为字典
        data_dict = file_data.model_dump()

        # 创建文件分析记录
        result = FileAnalysisService.create_file_analysis(data_dict, db)

        if result["status"] == "error":
            return JSONResponse(status_code=400, content=result)

        return JSONResponse(status_code=201, content=result)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "创建文件分析记录时发生未知错误",
                "error": str(e),
            },
        )


@repository_router.put("/file-analysis/{file_id}")
async def update_file_analysis(
    file_id: int,
    file_data: FileAnalysisUpdate,
    db: Session = Depends(get_db),
):
    """
    更新文件分析记录信息

    Args:
        file_id: 文件分析记录ID
        file_data: 文件分析更新数据
        db: 数据库会话

    Returns:
        JSON响应包含更新后的文件分析记录信息
    """
    try:
        # 转换为字典，排除None值
        data_dict = file_data.model_dump(exclude_none=True)

        if not data_dict:
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "message": "没有提供要更新的字段",
                    "file_id": file_id,
                },
            )

        # 更新文件分析记录
        result = FileAnalysisService.update_file_analysis(file_id, data_dict, db)

        if result["status"] == "error":
            if "未找到" in result["message"]:
                return JSONResponse(status_code=404, content=result)
            else:
                return JSONResponse(status_code=400, content=result)

        return JSONResponse(status_code=200, content=result)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "更新文件分析记录时发生未知错误",
                "file_id": file_id,
                "error": str(e),
            },
        )


@repository_router.delete("/file-analysis/{file_id}")
async def delete_file_analysis(
    file_id: int,
    db: Session = Depends(get_db),
):
    """
    删除文件分析记录

    Args:
        file_id: 文件分析记录ID
        db: 数据库会话

    Returns:
        JSON响应包含删除结果
    """
    try:
        # 删除文件分析记录
        result = FileAnalysisService.delete_file_analysis(file_id, db)

        if result["status"] == "error":
            if "未找到" in result["message"]:
                return JSONResponse(status_code=404, content=result)
            else:
                return JSONResponse(status_code=500, content=result)

        return JSONResponse(status_code=200, content=result)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "删除文件分析记录时发生未知错误",
                "file_id": file_id,
                "error": str(e),
            },
        )


@repository_router.get("/analysis-items/{file_analysis_id}")
async def get_file_analysis_items(
    file_analysis_id: int,
    db: Session = Depends(get_db),
    target_type: Optional[str] = Query(None, description="按目标类型过滤: file, class, function"),
    language: Optional[str] = Query(None, description="按编程语言过滤"),
):
    """
    获取指定文件分析ID的分析项详细内容

    Args:
        file_analysis_id: 文件分析ID
        db: 数据库会话
        target_type: 目标类型过滤器 (file/class/function)
        language: 编程语言过滤器

    Returns:
        JSON响应包含分析项列表，按start_line升序排序
    """
    try:
        # 获取分析项列表
        result = AnalysisItemService.get_analysis_items_by_file_id(
            file_analysis_id, db, target_type=target_type, language=language
        )

        if result["status"] == "error":
            return JSONResponse(status_code=500, content=result)

        # 如果没有找到分析项
        if result["total_items"] == 0:
            return JSONResponse(status_code=404, content=result)

        return JSONResponse(status_code=200, content=result)

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


@repository_router.post("/analysis-items")
async def create_analysis_item(
    item_data: AnalysisItemCreate,
    db: Session = Depends(get_db),
):
    """
    创建新的分析项记录

    Args:
        item_data: 分析项创建数据
        db: 数据库会话

    Returns:
        JSON响应包含创建的分析项记录信息
    """
    try:
        # 转换为字典
        data_dict = item_data.model_dump()

        # 创建分析项记录
        result = AnalysisItemService.create_analysis_item(data_dict, db)

        if result["status"] == "error":
            return JSONResponse(status_code=400, content=result)

        return JSONResponse(status_code=201, content=result)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "创建分析项记录时发生未知错误",
                "error": str(e),
            },
        )


@repository_router.put("/analysis-items/{item_id}")
async def update_analysis_item(
    item_id: int,
    item_data: AnalysisItemUpdate,
    db: Session = Depends(get_db),
):
    """
    更新分析项记录信息

    Args:
        item_id: 分析项记录ID
        item_data: 分析项更新数据
        db: 数据库会话

    Returns:
        JSON响应包含更新后的分析项记录信息
    """
    try:
        # 转换为字典，排除None值
        data_dict = item_data.model_dump(exclude_none=True)

        if not data_dict:
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "message": "没有提供要更新的字段",
                    "item_id": item_id,
                },
            )

        # 更新分析项记录
        result = AnalysisItemService.update_analysis_item(item_id, data_dict, db)

        if result["status"] == "error":
            if "未找到" in result["message"]:
                return JSONResponse(status_code=404, content=result)
            else:
                return JSONResponse(status_code=400, content=result)

        return JSONResponse(status_code=200, content=result)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "更新分析项记录时发生未知错误",
                "item_id": item_id,
                "error": str(e),
            },
        )


@repository_router.delete("/analysis-items/{item_id}")
async def delete_analysis_item(
    item_id: int,
    db: Session = Depends(get_db),
):
    """
    删除分析项记录

    Args:
        item_id: 分析项记录ID
        db: 数据库会话

    Returns:
        JSON响应包含删除结果
    """
    try:
        # 删除分析项记录
        result = AnalysisItemService.delete_analysis_item(item_id, db)

        if result["status"] == "error":
            if "未找到" in result["message"]:
                return JSONResponse(status_code=404, content=result)
            else:
                return JSONResponse(status_code=500, content=result)

        return JSONResponse(status_code=200, content=result)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "删除分析项记录时发生未知错误",
                "item_id": item_id,
                "error": str(e),
            },
        )


@repository_router.post("/upload")
async def upload_repository(
    files: List[UploadFile] = File(...),
    repository_name: str = Form(...),
    db: Session = Depends(get_db),
):
    """
    上传完整的仓库文件夹

    接收前端上传的整个项目文件夹，保持完整的目录结构，
    并提供详细的文件夹结构分析和统计信息。

    Args:
        files: 上传的文件列表（包含完整文件夹结构）
        repository_name: 仓库名称
        db: 数据库会话

    Returns:
        JSON响应包含：
        - 上传结果和仓库信息
        - 文件夹结构分析
        - 文件类型统计
        - 项目特征识别
    """
    try:
        # 调用上传服务
        result = await UploadService.upload_repository_files(files, repository_name, db)

        if result["status"] == "error":
            return JSONResponse(status_code=400, content=result)

        return JSONResponse(status_code=200, content=result)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "上传仓库文件时发生未知错误",
                "repository_name": repository_name,
                "error": str(e),
            },
        )


@repository_router.post("/analysis-tasks/{task_id}/create-knowledge-base")
async def create_knowledge_base(
    task_id: int,
    db: Session = Depends(get_db),
):
    """
    为指定任务创建知识库

    触发知识库创建flow，包含向量化和数据库更新

    Args:
        task_id: 分析任务ID
        db: 数据库会话

    Returns:
        JSON响应包含知识库创建状态和进度信息
    """
    try:
        # 验证任务是否存在
        task = db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
        if not task:
            return JSONResponse(
                status_code=404,
                content={
                    "status": "error",
                    "message": f"未找到ID为 {task_id} 的分析任务",
                    "task_id": task_id,
                },
            )

        # 获取仓库信息
        repository = db.query(Repository).filter(Repository.id == task.repository_id).first()
        if not repository:
            return JSONResponse(
                status_code=404,
                content={
                    "status": "error",
                    "message": f"未找到仓库ID为 {task.repository_id} 的仓库",
                    "task_id": task_id,
                },
            )

        # 检查任务状态
        if task.status not in ["pending", "running"]:
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "message": f"任务状态为 {task.status}，无法创建知识库",
                    "task_id": task_id,
                },
            )

        # 准备仓库信息
        repo_info = {
            "full_name": repository.full_name or repository.name,
            "name": repository.name,
            "local_path": repository.local_path,
        }

        # 启动知识库创建flow（异步执行）
        import asyncio
        import sys
        from pathlib import Path

        # 添加项目根目录到Python路径
        project_root = Path(__file__).parent.parent
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))

        try:
            from src.flows.web_flow import create_knowledge_base as create_kb_flow
        except ImportError as e:
            logger.error(f"导入知识库创建flow失败: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "message": f"导入知识库创建flow失败: {str(e)}",
                    "task_id": task_id,
                },
            )

        # 更新任务状态为运行中
        task.status = "running"
        db.commit()

        # 在后台异步执行知识库创建
        try:
            asyncio.create_task(create_kb_flow(task_id=task_id, local_path=repository.local_path, repo_info=repo_info))
        except Exception as e:
            logger.error(f"启动知识库创建flow失败: {str(e)}")
            # 回滚任务状态
            task.status = "failed"
            db.commit()
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "message": f"启动知识库创建flow失败: {str(e)}",
                    "task_id": task_id,
                },
            )

        return JSONResponse(
            status_code=202,  # 202 Accepted - 请求已接受，正在处理
            content={
                "status": "accepted",
                "message": "知识库创建任务已启动",
                "task_id": task_id,
                "task_status": "running",
            },
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "启动知识库创建时发生未知错误",
                "task_id": task_id,
                "error": str(e),
            },
        )


@repository_router.put("/repositories/{repository_id}")
async def update_repository(
    repository_id: int,
    repository_data: RepositoryUpdate,
    db: Session = Depends(get_db),
):
    """
    更新仓库信息

    Args:
        repository_id: 仓库ID
        repository_data: 仓库更新数据
        db: 数据库会话

    Returns:
        JSON响应包含更新后的仓库信息
    """
    try:
        # 转换为字典，排除None值
        data_dict = repository_data.model_dump(exclude_none=True)

        if not data_dict:
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "message": "没有提供要更新的字段",
                    "repository_id": repository_id,
                },
            )

        # 更新仓库
        result = RepositoryService.update_repository(repository_id, data_dict, db)

        if result["status"] == "error":
            if "未找到" in result["message"]:
                return JSONResponse(status_code=404, content=result)
            else:
                return JSONResponse(status_code=400, content=result)

        return JSONResponse(status_code=200, content=result)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "更新仓库时发生未知错误",
                "repository_id": repository_id,
                "error": str(e),
            },
        )


@repository_router.delete("/repositories/{repository_id}")
async def delete_repository(
    repository_id: int,
    db: Session = Depends(get_db),
    soft_delete: bool = Query(True, description="是否软删除（True=设置status为0，False=物理删除）"),
):
    """
    删除仓库（支持软删除和硬删除）

    Args:
        repository_id: 仓库ID
        db: 数据库会话
        soft_delete: 是否软删除

    Returns:
        JSON响应包含删除结果
    """
    try:
        # 删除仓库
        result = RepositoryService.delete_repository(repository_id, db, soft_delete=soft_delete)

        if result["status"] == "error":
            if "未找到" in result["message"]:
                return JSONResponse(status_code=404, content=result)
            else:
                return JSONResponse(status_code=500, content=result)

        return JSONResponse(status_code=200, content=result)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "删除仓库时发生未知错误",
                "repository_id": repository_id,
                "error": str(e),
            },
        )
