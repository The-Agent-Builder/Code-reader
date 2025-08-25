"""
FastAPI 主应用程序
构建 RESTful 接口，提供分析触发、结果获取、历史记录管理等接口
"""

import os
import asyncio
import uuid
from datetime import datetime
from typing import Dict, Any, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request

from .models import (
    AnalysisRequest,
    AnalysisStatus,
    AnalysisResult,
    SearchRequest,
    SearchResponse,
    AnalysisListResponse,
    StatisticsResponse,
    ErrorResponse,
    SuccessResponse,
)
from ..flows import analyze_repository, handle_webui_request
from ..utils.result_storage import ResultStorage
from ..utils.search_engine import SearchEngine
from ..utils.logger import logger
from ..utils.error_handler import GitHubAnalyzerError

# 全局状态管理
analysis_tasks: Dict[str, Dict[str, Any]] = {}
result_storage = ResultStorage()
search_engine = SearchEngine(result_storage)


def generate_analysis_id_from_url(repo_url: str) -> str:
    """从仓库URL生成分析ID"""
    try:
        # 从URL中提取仓库名
        # 支持格式: https://github.com/owner/repo 或 https://github.com/owner/repo.git
        if "github.com" in repo_url:
            parts = repo_url.rstrip("/").rstrip(".git").split("/")
            if len(parts) >= 2:
                repo_name = parts[-1]  # 获取仓库名
                return repo_name

        # 如果无法解析，使用URL的哈希值
        import hashlib

        return hashlib.md5(repo_url.encode()).hexdigest()[:8]
    except Exception:
        # 备用方案：使用URL的哈希值
        import hashlib

        return hashlib.md5(repo_url.encode()).hexdigest()[:8]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时的初始化
    logger.info("Starting GitHub Repository Analysis API")

    # 创建必要的目录
    os.makedirs("data/repos", exist_ok=True)
    os.makedirs("data/results", exist_ok=True)
    os.makedirs("data/vectorstores", exist_ok=True)
    os.makedirs("data/cache", exist_ok=True)
    os.makedirs("logs", exist_ok=True)

    yield

    # 关闭时的清理
    logger.info("Shutting down GitHub Repository Analysis API")


# 创建FastAPI应用
app = FastAPI(
    title="GitHub Repository Analysis API",
    description="基于PocketFlow的GitHub代码仓库解析工具",
    version="1.0.0",
    lifespan=lifespan,
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件和模板
app.mount("/static", StaticFiles(directory="static"), name="static")

# 添加额外的静态文件路由以支持直接访问CSS和JS文件
app.mount("/css", StaticFiles(directory="static/css"), name="css")
app.mount("/js", StaticFiles(directory="static/js"), name="js")

templates = Jinja2Templates(directory="templates")


async def run_analysis_task(analysis_id: str, request: AnalysisRequest):
    """后台分析任务"""
    try:
        # 更新任务状态
        analysis_tasks[analysis_id].update(
            {"status": "processing", "progress": 0.1, "message": "Starting analysis...", "updated_at": datetime.now()}
        )

        # 创建全局进度计数器
        progress_counter = {"completed": 0}

        # 创建进度回调函数
        def progress_callback(completed: int = None, current_file: str = ""):
            try:
                # 如果提供了completed参数，使用它；否则递增计数器
                if completed is not None:
                    progress_counter["completed"] = completed
                else:
                    progress_counter["completed"] += 1

                completed_count = progress_counter["completed"]

                # 获取总文件数（如果可用）
                total_files = analysis_tasks[analysis_id].get("total_files", 10)
                if total_files is None:
                    total_files = 10
                progress = min(0.9, (completed_count / total_files) * 0.8 + 0.1)  # 0.1-0.9 范围

                message = (
                    f"分析中: {current_file}" if current_file else f"已分析 {completed_count}/{total_files} 个文件"
                )

                analysis_tasks[analysis_id].update(
                    {
                        "progress": progress,
                        "message": message,
                        "completed_files": completed_count,
                        "total_files": total_files,
                        "current_file": current_file,
                        "updated_at": datetime.now(),
                    }
                )

                logger.info(f"Analysis {analysis_id}: {message} ({progress:.1%})")

            except Exception as e:
                logger.warning(f"Progress callback failed: {str(e)}")

        # 预估文件数量（用于进度计算）
        try:
            from ..utils.git_manager import GitManager

            git_manager = GitManager()
            local_path = git_manager.get_local_path(request.repo_url)

            total_files = 0
            if local_path.exists():
                supported_extensions = {
                    ".py",
                    ".js",
                    ".ts",
                    ".java",
                    ".cpp",
                    ".c",
                    ".h",
                    ".hpp",
                    ".cs",
                    ".go",
                    ".rs",
                    ".php",
                    ".rb",
                    ".swift",
                    ".kt",
                    ".scala",
                    ".ipynb",  # 添加 Jupyter Notebook 支持
                }
                ignore_dirs = {".git", "__pycache__", "node_modules", ".venv", "venv", "env"}

                for file_path in local_path.rglob("*"):
                    if (
                        file_path.is_file()
                        and file_path.suffix.lower() in supported_extensions
                        and not any(ignore_dir in file_path.parts for ignore_dir in ignore_dirs)
                    ):
                        total_files += 1

            if total_files > 0:
                analysis_tasks[analysis_id]["total_files"] = total_files
                analysis_tasks[analysis_id]["message"] = f"发现 {total_files} 个源码文件"
                logger.info(f"Estimated {total_files} files for analysis {analysis_id}")
            else:
                # 如果没有找到文件，设置默认值
                analysis_tasks[analysis_id]["total_files"] = 10
                analysis_tasks[analysis_id]["message"] = "准备分析文件..."
                logger.info(f"No files found, using default count for analysis {analysis_id}")

        except Exception as e:
            logger.warning(f"Failed to estimate file count: {str(e)}")
            analysis_tasks[analysis_id]["total_files"] = 10  # 默认值
            analysis_tasks[analysis_id]["message"] = "准备分析文件..."

        # 获取配置中的批处理大小
        from src.utils.config import get_config

        config = get_config()
        batch_size = config.llm_batch_size

        # 执行分析（带进度回调）
        result = await analyze_repository(
            request.repo_url, request.use_vectorization, batch_size, progress_callback=progress_callback
        )

        # 更新任务状态
        if result.get("status") == "completed":
            analysis_tasks[analysis_id].update(
                {
                    "status": "completed",
                    "progress": 1.0,
                    "message": "Analysis completed successfully",
                    "result": result,
                    "updated_at": datetime.now(),
                }
            )
        else:
            analysis_tasks[analysis_id].update(
                {
                    "status": "failed",
                    "progress": 0.0,
                    "message": result.get("error", "Analysis failed"),
                    "updated_at": datetime.now(),
                }
            )

    except Exception as e:
        logger.error(f"Analysis task {analysis_id} failed: {str(e)}")
        analysis_tasks[analysis_id].update(
            {"status": "failed", "progress": 0.0, "message": str(e), "updated_at": datetime.now()}
        )


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """首页"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/analysis/{analysis_id}", response_class=HTMLResponse)
async def view_analysis_detail(request: Request, analysis_id: str):
    """查看分析详情页面"""
    return templates.TemplateResponse("analysis_detail.html", {"request": request, "analysis_id": analysis_id})


@app.get("/analysis-config", response_class=HTMLResponse)
async def analysis_config_page(request: Request):
    """分析配置页面"""
    return templates.TemplateResponse("analysis_config.html", {"request": request})


@app.post("/api/analyze", response_model=AnalysisStatus)
async def start_analysis(request: AnalysisRequest, background_tasks: BackgroundTasks):
    """启动仓库分析"""
    try:
        # 从URL提取仓库名生成分析ID
        analysis_id = generate_analysis_id_from_url(request.repo_url)

        # 检查是否已有相同仓库的分析在进行中
        if not request.force_refresh:
            # 检查是否已存在分析结果
            result_storage = ResultStorage()
            existing_result = result_storage.get_analysis_by_id(analysis_id)
            if existing_result:
                logger.info(f"Found existing analysis for {request.repo_url}, analysis_id: {analysis_id}")
                # 返回已存在的分析状态
                try:
                    created_at_str = existing_result.get("created_at", datetime.now().isoformat())
                    if isinstance(created_at_str, str):
                        created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                    else:
                        created_at = datetime.now()
                except (ValueError, TypeError):
                    created_at = datetime.now()

                return AnalysisStatus(
                    analysis_id=analysis_id,
                    repo_url=request.repo_url,
                    status="completed",
                    progress=1.0,
                    message="Analysis already completed",
                    total_files=None,
                    completed_files=None,
                    current_file=None,
                    created_at=created_at,
                    updated_at=datetime.now(),
                )

        # 创建任务记录
        analysis_tasks[analysis_id] = {
            "analysis_id": analysis_id,
            "repo_url": request.repo_url,
            "status": "pending",
            "progress": 0.0,
            "message": "Analysis queued",
            "total_files": 0,  # 初始化为0，后续会更新
            "completed_files": 0,  # 初始化为0
            "current_file": None,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }

        # 添加后台任务
        background_tasks.add_task(run_analysis_task, analysis_id, request)

        logger.info(f"Started analysis task {analysis_id} for {request.repo_url}")

        return AnalysisStatus(**analysis_tasks[analysis_id])

    except Exception as e:
        logger.error(f"Failed to start analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analysis/{analysis_id}/status", response_model=AnalysisStatus)
async def get_analysis_status(analysis_id: str = Path(..., description="分析任务ID")):
    """获取分析状态"""
    if analysis_id not in analysis_tasks:
        raise HTTPException(status_code=404, detail="Analysis not found")

    return AnalysisStatus(**analysis_tasks[analysis_id])


@app.get("/api/analyses", response_model=AnalysisListResponse)
async def get_analysis_list(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
    """获取已分析的仓库列表"""
    try:
        # 从结果存储中获取分析列表
        result_storage = ResultStorage()
        all_analyses = result_storage.get_analysis_list(limit=1000)  # 获取更多数据用于分页

        # 分页处理
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_analyses = all_analyses[start_idx:end_idx]

        return AnalysisListResponse(analyses=page_analyses, total=len(all_analyses), page=page, page_size=page_size)
    except Exception as e:
        logger.error(f"Failed to get analysis list: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analysis/{analysis_id}/result")
async def get_analysis_result(analysis_id: str = Path(..., description="分析任务ID")):
    """获取分析结果详情"""
    try:
        # 从结果存储中获取分析结果
        result_storage = ResultStorage()
        result = result_storage.get_analysis_result(analysis_id)

        if not result:
            raise HTTPException(status_code=404, detail="Analysis result not found")

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get analysis result: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/search", response_model=SearchResponse)
async def search_code(request: SearchRequest):
    """搜索代码元素"""
    try:
        if request.repo_name:
            results = search_engine.search_by_repo(request.repo_name, request.query, request.limit)
        else:
            results = search_engine.search(request.query, request.search_type, request.limit)

        # 转换为API模型
        search_results = []
        for result in results:
            search_results.append(
                {
                    "analysis_id": result.analysis_id,
                    "repo_name": result.repo_name,
                    "file_path": result.file_path,
                    "element_type": result.element_type,
                    "element_name": result.element_name,
                    "description": result.description,
                    "source": result.source,
                    "language": result.language,
                    "code": result.code,
                    "score": result.score,
                }
            )

        return SearchResponse(
            results=search_results, total=len(search_results), query=request.query, search_type=request.search_type
        )

    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/statistics", response_model=StatisticsResponse)
async def get_statistics():
    """获取统计信息"""
    try:
        stats = search_engine.get_statistics()
        return StatisticsResponse(**stats)

    except Exception as e:
        logger.error(f"Failed to get statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analysis/{analysis_id}/reanalyze")
async def reanalyze_repository(analysis_id: str = Path(..., description="分析任务ID")):
    """重新分析仓库"""
    try:
        # 获取原分析信息
        existing_analysis = result_storage.get_analysis_by_id(analysis_id)
        if not existing_analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")

        repo_url = existing_analysis.get("repo_url")
        if not repo_url:
            raise HTTPException(status_code=400, detail="Repository URL not found in analysis")

        # 检查是否已有相同仓库的分析在进行中
        for task_id, task_info in analysis_tasks.items():
            if task_info.get("repo_url") == repo_url and task_info.get("status") == "processing":
                logger.info(f"Analysis already in progress for {repo_url}, task_id: {task_id}")
                return AnalysisStatus(
                    analysis_id=task_id,
                    repo_url=repo_url,
                    status="processing",
                    message="Analysis already in progress",
                    created_at=task_info.get("created_at", datetime.now()),
                    progress=task_info.get("progress", 0),
                    current_file=task_info.get("current_file", ""),
                )

        # 生成新的分析ID
        new_analysis_id = generate_analysis_id_from_url(repo_url)

        # 创建分析任务
        analysis_tasks[new_analysis_id] = {
            "repo_url": repo_url,
            "status": "processing",
            "created_at": datetime.now(),
            "use_vectorization": True,
            "batch_size": 10,
            "force_refresh": True,
        }

        # 启动后台分析任务
        asyncio.create_task(
            run_analysis_task(new_analysis_id, repo_url, use_vectorization=True, batch_size=10, force_refresh=True)
        )

        logger.info(f"Started reanalysis for {repo_url}, new analysis_id: {new_analysis_id}")

        return AnalysisStatus(
            analysis_id=new_analysis_id,
            repo_url=repo_url,
            status="processing",
            message="Reanalysis started successfully",
            created_at=datetime.now(),
            progress=0,
            current_file="",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start reanalysis for {analysis_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/analysis/{analysis_id}")
async def delete_analysis(analysis_id: str = Path(..., description="分析任务ID")):
    """删除分析结果"""
    try:
        # 从任务列表中删除
        if analysis_id in analysis_tasks:
            del analysis_tasks[analysis_id]

        # 从存储中删除
        success = result_storage.delete_analysis(analysis_id)

        if success:
            return SuccessResponse(success=True, message="Analysis deleted successfully")
        else:
            raise HTTPException(status_code=404, detail="Analysis not found")

    except Exception as e:
        logger.error(f"Failed to delete analysis {analysis_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat(), "version": "1.0.0"}


# 错误处理
@app.exception_handler(GitHubAnalyzerError)
async def github_analyzer_exception_handler(request: Request, exc: GitHubAnalyzerError):
    """自定义异常处理"""
    return ErrorResponse(
        error=exc.__class__.__name__,
        message=exc.message,
        details={"error_code": exc.error_code} if exc.error_code else None,
    )


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("APP_HOST", "0.0.0.0")
    port = int(os.getenv("APP_PORT", 8000))
    debug = os.getenv("DEBUG", "False").lower() == "true"

    uvicorn.run("src.api.main:app", host=host, port=port, reload=debug, log_level="info")
