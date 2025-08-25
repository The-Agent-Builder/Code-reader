"""
定义标准异常类型与捕获策略
"""
from typing import Optional


class GitHubAnalyzerError(Exception):
    """基础异常类"""
    def __init__(self, message: str, error_code: Optional[str] = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class GitHubAPIError(GitHubAnalyzerError):
    """GitHub API 相关错误"""
    pass


class GitCloneError(GitHubAnalyzerError):
    """Git 克隆相关错误"""
    pass


class VectorStoreError(GitHubAnalyzerError):
    """向量存储相关错误"""
    pass


class LLMParsingError(GitHubAnalyzerError):
    """LLM 解析相关错误"""
    pass


class ResultStorageError(GitHubAnalyzerError):
    """结果存储相关错误"""
    pass


class SearchEngineError(GitHubAnalyzerError):
    """搜索引擎相关错误"""
    pass


class ConfigurationError(GitHubAnalyzerError):
    """配置相关错误"""
    pass


def handle_error(func):
    """错误处理装饰器"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except GitHubAnalyzerError:
            # 重新抛出自定义异常
            raise
        except Exception as e:
            # 包装其他异常
            raise GitHubAnalyzerError(f"Unexpected error in {func.__name__}: {str(e)}")
    return wrapper


async def async_handle_error(func):
    """异步错误处理装饰器"""
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except GitHubAnalyzerError:
            # 重新抛出自定义异常
            raise
        except Exception as e:
            # 包装其他异常
            raise GitHubAnalyzerError(f"Unexpected error in {func.__name__}: {str(e)}")
    return wrapper
