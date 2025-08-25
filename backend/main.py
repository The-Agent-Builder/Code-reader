"""
AI 代码库领航员 (AI Codebase Navigator) - 后端API服务
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
import uvicorn
import os
from dotenv import load_dotenv
from database import test_database_connection, get_database_info
from routers import repository_router

# 加载环境变量
load_dotenv()

# 创建FastAPI应用实例
app = FastAPI(
    title="AI 代码库领航员 API",
    description="AI Codebase Navigator - 智能代码库分析和导航系统的后端API服务",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI 文档地址
    redoc_url="/redoc",  # ReDoc 文档地址
    openapi_url="/openapi.json",  # OpenAPI schema 地址
)

# 配置CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000", "http://127.0.0.1:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含路由
app.include_router(repository_router)


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
        "repository_files": "/api/repository/files/{task_id}",
        "analysis_items": "/api/repository/analysis-items/{file_analysis_id}",
        "repositories": "/api/repository/repositories?name={name}",
        "analysis_tasks": "/api/repository/analysis-tasks/{repository_id}",
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
    uvicorn.run("main:app", host=host, port=port, reload=True, log_level="info")  # 开发模式下启用热重载
