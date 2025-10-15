"""
任务管理 API 接口
"""

import os
import uuid
import zipfile
import tempfile
import shutil
import requests
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

# 导入数据库和服务
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from database import get_db
from services import UploadService, RepositoryService, AnalysisTaskService
from config import settings
import logging

# 设置日志
logger = logging.getLogger(__name__)

# 创建任务路由器
tasks_router = APIRouter(prefix="/api/v1/tasks", tags=["任务管理"])


@tasks_router.post("/create-task-from-zip")
async def create_task_from_zip(
    zip_file: UploadFile = File(..., description="上传的zip压缩文件"),
    db: Session = Depends(get_db)
) -> JSONResponse:
    try:
        # 验证文件类型
        if not zip_file.filename.lower().endswith('.zip'):
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "message": "只支持.zip格式的文件",
                    "filename": zip_file.filename
                }
            )
        
        # 使用文件名（去掉.zip扩展名）作为仓库名称
        repository_name = os.path.splitext(zip_file.filename)[0]
        
        # 清理仓库名称
        clean_repo_name = "".join(c for c in repository_name if c.isalnum() or c in ("-", "_", ".")).strip()
        if not clean_repo_name:
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error", 
                    "message": "文件名包含无效字符，无法生成有效的仓库名称",
                    "filename": zip_file.filename
                }
            )
        
        # 生成唯一的task UUID
        task_uuid = str(uuid.uuid4())
        task_id_string = f"task_{task_uuid}"
        
        # 初始化 external_file_path
        external_file_path = None
        
        # 创建临时目录处理zip文件
        with tempfile.TemporaryDirectory() as temp_dir:
            # 保存上传的zip文件
            zip_path = os.path.join(temp_dir, zip_file.filename)
            with open(zip_path, "wb") as buffer:
                content = await zip_file.read()
                buffer.write(content)
            
            # 上传zip文件到外部系统
            readme_api_base_url = os.getenv("README_API_BASE_URL")
            if readme_api_base_url:
                try:
                    upload_url = f"{readme_api_base_url}/api/upload/zip"
                    
                    # 重新打开文件进行上传
                    with open(zip_path, "rb") as f:
                        files = {'file': (zip_file.filename, f, 'application/x-zip-compressed')}
                        headers = {'accept': 'application/json'}
                        
                        response = requests.post(upload_url, files=files, headers=headers)
                        
                        if response.status_code == 200:
                            upload_result = response.json()
                            if upload_result.get("success"):
                                external_file_path = upload_result.get("file_path")
                                print(f"外部系统上传成功，file_path: {external_file_path}")
                                logger.info(f"ZIP文件已成功上传到外部系统: {external_file_path}")
                            else:
                                logger.warning(f"外部系统上传失败: {upload_result.get('message', '未知错误')}")
                        else:
                            logger.warning(f"外部系统上传请求失败，状态码: {response.status_code}")
                            
                except Exception as e:
                    logger.error(f"上传到外部系统时发生错误: {str(e)}")
            else:
                logger.info("未设置README_API_BASE_URL环境变量，跳过外部系统上传")
            
            # 解压缩文件到临时目录
            extract_dir = os.path.join(temp_dir, "extracted")
            os.makedirs(extract_dir, exist_ok=True)
            
            try:
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
                logger.info(f"成功解压缩文件到: {extract_dir}")
            except zipfile.BadZipFile:
                return JSONResponse(
                    status_code=400,
                    content={
                        "status": "error",
                        "message": "无效的zip文件格式",
                        "filename": zip_file.filename
                    }
                )
            
            # 计算文件内容的MD5哈希值来生成唯一的目录名
            import hashlib
            import time
            import random
            
            md5_hash = hashlib.md5()
            md5_hash.update(task_uuid.encode("utf-8"))
            md5_hash.update(str(time.time_ns()).encode("utf-8"))
            md5_hash.update(str(random.randint(100000, 999999)).encode("utf-8"))
            
            # 添加zip文件内容到哈希
            md5_hash.update(content)
            
            md5_directory_name = md5_hash.hexdigest()
            
            # 创建最终的仓库目录
            repo_path = Path(settings.LOCAL_REPO_PATH) / md5_directory_name
            repo_path.mkdir(parents=True, exist_ok=True)
            
            # 移动解压缩的文件到最终目录
            extracted_items = list(Path(extract_dir).iterdir())
            
            # 如果解压后只有一个顶级目录，则提升其内容
            if len(extracted_items) == 1 and extracted_items[0].is_dir():
                source_dir = extracted_items[0]
                for item in source_dir.iterdir():
                    if item.is_dir():
                        shutil.copytree(item, repo_path / item.name, dirs_exist_ok=True)
                    else:
                        shutil.copy2(item, repo_path)
            else:
                # 直接复制所有内容
                for item in extracted_items:
                    if item.is_dir():
                        shutil.copytree(item, repo_path / item.name, dirs_exist_ok=True)
                    else:
                        shutil.copy2(item, repo_path)
            
            logger.info(f"文件已移动到最终目录: {repo_path}")
            
            # 统计文件信息
            total_files = 0
            file_types = {}
            total_size = 0
            
            for root, dirs, files in os.walk(repo_path):
                for file in files:
                    file_path = Path(root) / file
                    try:
                        file_size = file_path.stat().st_size
                        total_size += file_size
                        total_files += 1
                        
                        # 统计文件类型
                        file_extension = file_path.suffix.lower().lstrip(".")
                        if not file_extension:
                            file_extension = "no_extension"
                        file_types[file_extension] = file_types.get(file_extension, 0) + 1
                    except Exception as e:
                        logger.warning(f"无法统计文件 {file_path}: {e}")
            
            # 构建相对路径（相对于backend目录）
            relative_local_path = os.path.relpath(repo_path, Path(__file__).parent.parent.parent)
            
            # 创建仓库记录
            repository_data = {
                "user_id": 1,  # 默认用户ID
                "name": clean_repo_name,
                "full_name": clean_repo_name,
                "local_path": relative_local_path,
                "status": 1
            }
            
            repo_result = RepositoryService.create_repository(repository_data, db)
            if repo_result["status"] == "error":
                return JSONResponse(
                    status_code=500,
                    content={
                        "status": "error",
                        "message": f"创建仓库记录失败: {repo_result['message']}",
                        "task_id": task_id_string
                    }
                )
            
            repository = repo_result["repository"]
            repository_id = repository["id"]
            
            # 创建分析任务记录
            task_data = {
                "repository_id": repository_id,
                "total_files": total_files,
                "successful_files": 0,
                "failed_files": 0,
                "code_lines": 0,
                "module_count": 0,
                "status": "pending",
                "task_index": task_uuid  # 使用UUID作为任务索引
            }
            
            # 如果没有外部路径，使用本地路径
            if external_file_path is None:
                external_file_path = str(repo_path)
                logger.info(f"外部系统上传失败或未配置，使用本地路径: {external_file_path}")
            
            task_result = AnalysisTaskService.create_analysis_task(task_data, external_file_path, db)
            if task_result["status"] == "error":
                return JSONResponse(
                    status_code=500,
                    content={
                        "status": "error", 
                        "message": f"创建分析任务失败: {task_result['message']}",
                        "task_id": task_id_string
                    }
                )
            
            task = task_result["task"]
            
            # 格式化文件大小
            def format_file_size(size_bytes):
                if size_bytes == 0:
                    return "0 B"
                size_names = ["B", "KB", "MB", "GB"]
                import math
                i = int(math.floor(math.log(size_bytes, 1024)))
                p = math.pow(1024, i)
                s = round(size_bytes / p, 2)
                return f"{s} {size_names[i]}"
            
            # 返回成功响应
            return JSONResponse(
                status_code=201,
                content={
                    "status": "success",
                    "message": "任务创建成功",
                    "task_id": task_id_string,
                    "task_uuid": task_uuid,
                    "task_db_id": task["id"],
                    "repository_id": repository_id,
                    "repository_name": clean_repo_name,
                    "local_path": str(repo_path),
                    "relative_path": relative_local_path,
                    "md5_directory_name": md5_directory_name,
                    "upload_summary": {
                        "total_files": total_files,
                        "total_size_bytes": total_size,
                        "total_size_formatted": format_file_size(total_size),
                        "file_types": file_types
                    },
                    "task_status": task["status"]
                }
            )
            
    except Exception as e:
        logger.error(f"创建任务时发生错误: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "创建任务时发生未知错误",
                "error": str(e),
                "task_id": None
            }
        )


@tasks_router.get("/{task_id}")
async def get_task_info(
    task_id: str,
    db: Session = Depends(get_db)
):
    """
    获取任务信息
    
    Args:
        task_id: 任务ID，支持task_{uuid}格式或数字ID
        db: 数据库会话
        
    Returns:
        JSON响应包含任务详细信息
    """
    try:
        # 处理task_{uuid}格式
        if task_id.startswith("task_"):
            task_uuid = task_id[5:]  # 去掉"task_"前缀
            
            # 通过task_index查询任务
            from models import AnalysisTask
            task = db.query(AnalysisTask).filter(AnalysisTask.task_index == task_uuid).first()
            
            if not task:
                return JSONResponse(
                    status_code=404,
                    content={
                        "status": "error",
                        "message": f"未找到任务: {task_id}",
                        "task_id": task_id
                    }
                )
            
            task_db_id = task.id
        else:
            # 处理数字ID格式
            try:
                task_db_id = int(task_id)
            except ValueError:
                return JSONResponse(
                    status_code=400,
                    content={
                        "status": "error",
                        "message": f"无效的任务ID格式: {task_id}",
                        "task_id": task_id
                    }
                )
        
        # 获取任务详细信息
        result = AnalysisTaskService.get_task_by_id(task_db_id, db)
        
        if result["status"] == "error":
            return JSONResponse(
                status_code=404 if "未找到" in result["message"] else 500,
                content=result
            )
        
        task_info = result["task"]
        
        # 添加task_{uuid}格式的ID
        if task_info.get("task_index"):
            task_info["task_id_string"] = f"task_{task_info['task_index']}"
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "获取任务信息成功",
                "task": task_info
            }
        )
        
    except Exception as e:
        logger.error(f"获取任务信息时发生错误: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "获取任务信息时发生未知错误",
                "task_id": task_id,
                "error": str(e)
            }
        )
