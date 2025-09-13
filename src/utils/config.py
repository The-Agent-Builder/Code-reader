"""
配置管理模块
统一管理环境变量和应用配置
"""

import os
from typing import Optional, Dict, Any
from pathlib import Path
from dotenv import load_dotenv

from .logger import logger


class Config:
    """应用配置管理器"""

    def __init__(self, env_file: Optional[str] = None):
        """
        初始化配置管理器

        Args:
            env_file: 环境变量文件路径，默认为项目根目录的 .env 文件
        """
        # 强制加载 .env 文件，覆盖系统环境变量
        if env_file:
            load_dotenv(env_file, override=True)
        else:
            # 自动查找 .env 文件并强制覆盖
            load_dotenv(override=True)

        # 验证必需的环境变量
        self._validate_required_vars()

    def _validate_required_vars(self):
        """验证必需的环境变量"""
        required_vars = ["GITHUB_TOKEN", "OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENAI_MODEL", "RAG_BASE_URL"]

        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)

        if missing_vars:
            logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
            logger.error("Please check your .env file")
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

    # GitHub 配置
    @property
    def github_token(self) -> str:
        """GitHub API Token"""
        return os.getenv("GITHUB_TOKEN", "")

    # OpenAI 配置
    @property
    def openai_api_key(self) -> str:
        """OpenAI API Key"""
        return os.getenv("OPENAI_API_KEY", "")

    @property
    def openai_base_url(self) -> str:
        """OpenAI API Base URL"""
        return os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

    @property
    def openai_model(self) -> str:
        """OpenAI Model"""
        return os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

    # LLM 并行处理配置
    @property
    def llm_max_concurrent(self) -> int:
        """LLM 最大并发请求数"""
        return int(os.getenv("LLM_MAX_CONCURRENT", "5"))

    @property
    def llm_batch_size(self) -> int:
        """LLM 批处理大小"""
        return int(os.getenv("LLM_BATCH_SIZE", "10"))

    @property
    def llm_request_timeout(self) -> int:
        """LLM 请求超时时间(秒)"""
        return int(os.getenv("LLM_REQUEST_TIMEOUT", "60"))

    @property
    def llm_retry_delay(self) -> int:
        """LLM 重试延迟时间(秒)"""
        return int(os.getenv("LLM_RETRY_DELAY", "2"))

    # RAG 服务配置
    @property
    def rag_base_url(self) -> str:
        """RAG 服务 Base URL"""
        return os.getenv("RAG_BASE_URL", "")

    @property
    def rag_batch_size(self) -> int:
        """RAG 文档批量大小（<=0 表示一次性上传所有文档）"""
        try:
            return int(os.getenv("RAG_BATCH_SIZE", "100"))
        except ValueError:
            return 100

    # Web API 配置
    @property
    def api_base_url(self) -> str:
        """后端 API Base URL"""
        return os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

    @property
    def readme_api_base_url(self) -> str:
        """README API Base URL"""
        return os.getenv("README_API_BASE_URL", "http://127.0.0.1:8001")

    # 应用配置
    @property
    def app_host(self) -> str:
        """应用主机地址"""
        return os.getenv("APP_HOST", "0.0.0.0")

    @property
    def app_port(self) -> int:
        """应用端口"""
        return int(os.getenv("APP_PORT", 8000))

    @property
    def debug(self) -> bool:
        """调试模式"""
        return os.getenv("DEBUG", "False").lower() == "true"

    # 本地存储配置
    @property
    def local_repo_path(self) -> Path:
        """本地仓库存储路径"""
        path = os.getenv("LOCAL_REPO_PATH", "./data/repos")
        return Path(path)

    @property
    def results_path(self) -> Path:
        """分析结果存储路径"""
        path = os.getenv("RESULTS_PATH", "./data/results")
        return Path(path)

    @property
    def vectorstore_path(self) -> Path:
        """向量存储路径"""
        path = os.getenv("VECTORSTORE_PATH", "./data/vectorstores")
        return Path(path)

    def get_all_config(self) -> Dict[str, Any]:
        """获取所有配置信息（敏感信息会被掩码）"""
        return {
            "github_token": self._mask_sensitive(self.github_token),
            "openai_api_key": self._mask_sensitive(self.openai_api_key),
            "openai_base_url": self.openai_base_url,
            "openai_model": self.openai_model,
            "llm_max_concurrent": self.llm_max_concurrent,
            "llm_batch_size": self.llm_batch_size,
            "llm_request_timeout": self.llm_request_timeout,
            "llm_retry_delay": self.llm_retry_delay,
            "rag_base_url": self.rag_base_url,
            "rag_batch_size": self.rag_batch_size,
            "api_base_url": self.api_base_url,
            "app_host": self.app_host,
            "app_port": self.app_port,
            "debug": self.debug,
            "local_repo_path": str(self.local_repo_path),
            "results_path": str(self.results_path),
            "vectorstore_path": str(self.vectorstore_path),
        }

    def _mask_sensitive(self, value: str) -> str:
        """掩码敏感信息"""
        if not value:
            return ""
        if len(value) <= 8:
            return "*" * len(value)
        return value[:4] + "*" * (len(value) - 8) + value[-4:]


# 全局配置实例
config = Config()


def get_config() -> Config:
    """获取全局配置实例"""
    return config


def reload_config(env_file: Optional[str] = None) -> Config:
    """重新加载配置"""
    global config
    config = Config(env_file)
    return config
