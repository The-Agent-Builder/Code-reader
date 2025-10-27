"""
AI 代码库领航员 (AI Codebase Navigator) - 后端API服务
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
import uvicorn
import os
import asyncio
import logging
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from database import test_database_connection, get_database_info, SessionLocal
from routers import repository_router, analysis_router, auth_router
from api.v1.tasks import tasks_router
from config import settings
from pathlib import Path
from models import TaskReadme
from utils.makdown_utils.mermaid_to_svg import MermaidToSvgConverter

# 加载环境变量
load_dotenv()

# 配置日志
logger = logging.getLogger(__name__)

# 全局变量用于控制后台任务
background_task_running = False


async def process_empty_rendered_content():
    """
    后台任务：处理task_readmes表中rendered_content为空的记录
    定期检查并生成rendered_content
    """
    global background_task_running
    logger.info("启动rendered_content处理后台任务...")
    
    while background_task_running:
        try:
            db = SessionLocal()
            try:
                # 查询rendered_content为空或NULL的记录，或者content不为空且与rendered_content相同的记录
                empty_readmes = db.query(TaskReadme).filter(
                    (TaskReadme.rendered_content == None) | 
                    (TaskReadme.rendered_content == "") |
                    (
                        (TaskReadme.content != None) & 
                        (TaskReadme.content != "") & 
                        (TaskReadme.content == TaskReadme.rendered_content)
                    )
                ).all()
                
                if empty_readmes:
                    logger.info(f"发现 {len(empty_readmes)} 条需要处理的README记录")
                    
                    # 初始化转换器
                    converter = MermaidToSvgConverter(use_cli=True)
                    
                    for readme in empty_readmes:
                        try:
                            logger.info(f"处理README ID: {readme.id}, Task ID: {readme.task_id}")
                            
                            # 转换markdown内容
                            if readme.content:
                                # 使用 asyncio.to_thread 将阻塞操作移到线程池中执行
                                rendered_content = await asyncio.to_thread(
                                    converter.convert_markdown, 
                                    readme.content
                                )
                                
                                # 更新rendered_content
                                readme.rendered_content = rendered_content
                                db.commit()
                                
                                logger.info(f"成功生成README ID {readme.id} 的rendered_content")
                            else:
                                logger.warning(f"README ID {readme.id} 的content字段为空，跳过处理")
                                
                        except Exception as e:
                            logger.error(f"处理README ID {readme.id} 时发生错误: {str(e)}")
                            db.rollback()
                            # 继续处理下一条记录
                            continue
                else:
                    logger.debug("没有需要处理的README记录")
                    
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"后台任务执行出错: {str(e)}")
        
        # 等待一段时间后再次检查（60秒）
        await asyncio.sleep(60)
    
    logger.info("rendered_content处理后台任务已停止")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    """
    global background_task_running
    
    # 启动时执行
    logger.info("应用启动中...")
    background_task_running = True
    
    # 启动后台任务
    task = asyncio.create_task(process_empty_rendered_content())
    
    yield
    
    # 关闭时执行
    logger.info("应用关闭中...")
    background_task_running = False
    
    # 等待后台任务结束
    try:
        await asyncio.wait_for(task, timeout=5.0)
    except asyncio.TimeoutError:
        logger.warning("后台任务关闭超时")
        task.cancel()


# 确保必要的目录存在
def ensure_directories():
    """确保必要的目录存在"""
    directories = [
        settings.LOCAL_REPO_PATH,
        settings.RESULTS_PATH,
        settings.VECTORSTORE_PATH,
    ]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✓ 确保目录存在: {directory}")


# 创建目录
ensure_directories()

# 创建FastAPI应用实例
app = FastAPI(
    title="AI 代码库领航员 API",
    description="AI Codebase Navigator - 智能代码库分析和导航系统的后端API服务",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI 文档地址
    redoc_url="/redoc",  # ReDoc 文档地址
    openapi_url="/openapi.json",  # OpenAPI schema 地址
    lifespan=lifespan,  # 添加生命周期管理
)

# 配置CORS中间件
# 在 Docker 容器中，前端通过 Nginx 反向代理访问后端，不需要跨域
# 但为了开发环境兼容，仍保留 CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://localhost",
        "http://127.0.0.1"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含路由
app.include_router(repository_router)
app.include_router(analysis_router)
app.include_router(auth_router)
app.include_router(tasks_router)


@app.get("/health", tags=["系统监控"])
async def health_check():
    """
    健康检查接口

    返回系统运行状态和基本信息
    """
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "message": "AI 代码库领航员后端服务运行正常",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "service": "AI Codebase Navigator API",
        },
    )


@app.get("/", tags=["根路径"])
async def root():
    """
    根路径接口

    返回API服务的基本信息
    """
    return {
        "message": "欢迎使用 AI 代码库领航员 API",
        "description": "智能代码库分析和导航系统",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
        "database_test": "/database/test",
        "database_info": "/database/info",
        "api_endpoints": {
            "repositories": {
                "get_by_id": "/api/repository/repositories/{repository_id}",
                "create": "/api/repository/repositories",
                "update": "/api/repository/repositories/{repository_id}",
                "delete": "/api/repository/repositories/{repository_id}",
                "get_by_name": "/api/repository/repositories?name={name}",
                "get_list": "/api/repository/repositories-list",
            },
            "analysis": {
                "get_tasks": "/api/repository/analysis-tasks/{repository_id}",
                "create_task": "/api/repository/analysis-tasks",
                "update_task": "/api/repository/analysis-tasks/{task_id}",
                "delete_task": "/api/repository/analysis-tasks/{task_id}",
                "can_start_task": "/api/repository/analysis-tasks/{task_id}/can-start",
                "queue_status": "/api/repository/analysis-tasks/queue/status",
                "files": "/api/repository/files/{task_id}",
                "get_file_analysis": "/api/repository/file-analysis/{file_id}?task_id={task_id}",
                "create_file_analysis": "/api/repository/file-analysis",
                "update_file_analysis": "/api/repository/file-analysis/{file_id}",
                "delete_file_analysis": "/api/repository/file-analysis/{file_id}",
                "get_analysis_items": "/api/repository/analysis-items/{file_analysis_id}",
                "create_analysis_item": "/api/repository/analysis-items",
                "update_analysis_item": "/api/repository/analysis-items/{item_id}",
                "delete_analysis_item": "/api/repository/analysis-items/{item_id}",
            },
            "upload": {
                "repository": "/api/repository/upload",
            },
            "analysis_management": {
                "create_knowledge_base": "/api/analysis/{task_id}/create-knowledge-base",
                "analyze_data_model": "/api/analysis/{task_id}/analyze-data-model",
            },
        },
    }


@app.get("/database/test", tags=["数据库"])
async def test_database():
    """
    测试数据库连接

    返回数据库连接状态和基本信息
    """
    result = await test_database_connection()

    # 根据连接状态返回不同的HTTP状态码
    if result["status"] == "success":
        return JSONResponse(status_code=200, content=result)
    else:
        return JSONResponse(status_code=503, content=result)


@app.get("/database/info", tags=["数据库"])
async def database_info():
    """
    获取数据库详细信息

    返回数据库版本、用户、表信息等详细数据
    """
    result = await get_database_info()

    # 根据查询状态返回不同的HTTP状态码
    if result["status"] == "success":
        return JSONResponse(status_code=200, content=result)
    else:
        return JSONResponse(status_code=503, content=result)


if __name__ == "__main__":
    # 从环境变量获取配置
    host = os.getenv("APP_HOST", "0.0.0.0")
    port = int(os.getenv("APP_PORT", 8000))

    # 启动服务器
    uvicorn.run("main:app", host=host, port=port, reload=False, log_level="info", reload_excludes=["data/**"])  # 开发模式下启用热重载，排除data目录