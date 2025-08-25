"""
配置文件
"""

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Settings:
    """应用配置类"""
    
    # 应用基本配置
    APP_NAME: str = "AI 代码库领航员 API"
    APP_VERSION: str = "1.0.0"
    APP_HOST: str = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT: int = int(os.getenv("APP_PORT", 8000))
    
    # 数据库配置
    DB_DIALECT: str = os.getenv("DB_DIALECT", "mysql+pymysql")
    DB_HOST: str = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT: int = int(os.getenv("DB_PORT", 3306))
    DB_NAME: str = os.getenv("DB_NAME", "code_analysis")
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "123456")
    DB_PARAMS: str = os.getenv("DB_PARAMS", "charset=utf8mb4")
    DB_ECHO: bool = bool(int(os.getenv("DB_ECHO", 0)))
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", 5))
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", 10))
    
    @property
    def database_url(self) -> str:
        """构建数据库连接URL"""
        return f"{self.DB_DIALECT}://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?{self.DB_PARAMS}"
    
    # GitHub API配置
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")
    
    # OpenAI API配置
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    
    # LLM 并行处理配置
    LLM_MAX_CONCURRENT: int = int(os.getenv("LLM_MAX_CONCURRENT", 25))
    LLM_BATCH_SIZE: int = int(os.getenv("LLM_BATCH_SIZE", 50))
    LLM_REQUEST_TIMEOUT: int = int(os.getenv("LLM_REQUEST_TIMEOUT", 120))
    LLM_RETRY_DELAY: int = int(os.getenv("LLM_RETRY_DELAY", 2))
    
    # RAG 服务配置
    RAG_BASE_URL: str = os.getenv("RAG_BASE_URL", "")
    RAG_BATCH_SIZE: int = int(os.getenv("RAG_BATCH_SIZE", 100))
    
    # 本地存储配置
    LOCAL_REPO_PATH: str = os.getenv("LOCAL_REPO_PATH", "./data/repos")
    RESULTS_PATH: str = os.getenv("RESULTS_PATH", "./data/results")
    VECTORSTORE_PATH: str = os.getenv("VECTORSTORE_PATH", "./data/vectorstores")

# 创建全局配置实例
settings = Settings()
