"""
API 数据模型定义
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class AnalysisRequest(BaseModel):
    """分析请求模型"""

    repo_url: str = Field(..., description="GitHub仓库URL")
    use_vectorization: bool = Field(True, description="是否使用向量化（RAG）")
    force_refresh: bool = Field(False, description="是否强制重新分析")


class AnalysisStatus(BaseModel):
    """分析状态模型"""

    analysis_id: str
    repo_url: str
    status: str  # processing, completed, failed
    progress: Optional[float] = None
    message: Optional[str] = None
    total_files: Optional[int] = None
    completed_files: Optional[int] = None
    current_file: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class CodeElement(BaseModel):
    """代码元素模型"""

    title: str
    description: str
    source: str
    language: str
    code: str


class FileAnalysis(BaseModel):
    """文件分析结果模型"""

    file_path: str
    functions: List[CodeElement]
    classes: List[CodeElement]


class RepositoryInfo(BaseModel):
    """仓库信息模型"""

    description: str
    language: str
    created_at: str
    updated_at: str
    languages: Dict[str, int]
    readme: str
    full_name: str
    clone_url: str
    ssh_url: str
    stars: int
    forks: int


class AnalysisResult(BaseModel):
    """完整分析结果模型"""

    analysis_id: str
    repo_url: str
    repo_info: RepositoryInfo
    code_analysis: List[FileAnalysis]
    analysis_time: str
    status: str
    statistics: Dict[str, Any]


class SearchRequest(BaseModel):
    """搜索请求模型"""

    query: str = Field(..., description="搜索查询")
    search_type: str = Field("all", description="搜索类型")
    repo_name: Optional[str] = Field(None, description="限制搜索的仓库名")
    limit: int = Field(20, ge=1, le=100, description="结果数量限制")


class SearchResult(BaseModel):
    """搜索结果模型"""

    analysis_id: str
    repo_name: str
    file_path: str
    element_type: str
    element_name: str
    description: str
    source: str
    language: str
    code: str
    score: float


class SearchResponse(BaseModel):
    """搜索响应模型"""

    results: List[SearchResult]
    total: int
    query: str
    search_type: str


class AnalysisListResponse(BaseModel):
    """分析列表响应模型"""

    analyses: List[Dict[str, Any]]
    total: int
    page: int
    page_size: int


class StatisticsResponse(BaseModel):
    """统计信息响应模型"""

    total_repositories: int
    total_functions: int
    total_classes: int
    languages: Dict[str, int]


class ErrorResponse(BaseModel):
    """错误响应模型"""

    error: str
    message: str
    details: Optional[Dict[str, Any]] = None


class SuccessResponse(BaseModel):
    """成功响应模型"""

    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
