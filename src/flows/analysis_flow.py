"""
GitHub 仓库分析主流程
整合所有节点，实现完整的代码仓库解析流程
"""

from typing import Dict, Any, List
from pocketflow import AsyncFlow

# 直接导入需要的节点，避免 __init__.py 的依赖问题
from ..nodes.github_info_fetch_node import GitHubInfoFetchNode
from ..nodes.git_clone_node import GitCloneNode
from ..nodes.vectorize_repo_node import VectorizeRepoNode
from ..nodes.code_parsing_batch_node import CodeParsingBatchNode
from ..nodes.readme_analysis_node import ReadmeAnalysisNode
from ..nodes.save_results_node import SaveResultsNode
from ..nodes.save_to_mysql_node import SaveToMySQLNode
from ..utils.logger import logger


class GitHubAnalysisFlow(AsyncFlow):
    """GitHub 仓库分析主流程"""

    def __init__(self):
        super().__init__()

        # 创建节点实例
        self.github_info_node = GitHubInfoFetchNode()
        self.git_clone_node = GitCloneNode()
        self.vectorize_node = VectorizeRepoNode()
        self.code_parse_node = CodeParsingBatchNode()
        self.readme_analysis_node = ReadmeAnalysisNode()
        self.save_results_node = SaveResultsNode()
        self.save_mysql_node = SaveToMySQLNode()

        # 构建流程链
        self._build_flow()

    def _build_flow(self):
        """构建分析流程"""
        # 设置起始节点
        self.start(self.github_info_node)

        # 构建节点链：GitHub信息 -> 克隆 -> 向量化 -> 代码解析 -> README分析 -> 保存结果
        (
            self.github_info_node
            >> self.git_clone_node
            >> self.vectorize_node
            >> self.code_parse_node
            >> self.readme_analysis_node
            >> self.save_results_node
            >> self.save_mysql_node
        )

        logger.info("GitHub analysis flow constructed")

    async def prep_async(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """流程预处理"""
        logger.info("🚀 ========== 开始 GitHub 仓库分析流程 ==========")
        logger.info("📋 阶段: 流程初始化 (GitHubAnalysisFlow.prep_async)")

        # 验证输入
        if "repo_url" not in shared:
            logger.error("❌ 缺少仓库 URL")
            raise ValueError("Repository URL is required")

        repo_url = shared.get("repo_url")
        if repo_url is None:
            logger.error("❌ 仓库 URL 为 None")
            raise ValueError("Repository URL cannot be None")

        if not isinstance(repo_url, str):
            logger.error(f"❌ 仓库 URL 类型错误: {type(repo_url)}")
            raise ValueError("Repository URL must be a string")

        if not repo_url.strip():
            logger.error("❌ 仓库 URL 为空")
            raise ValueError("Repository URL cannot be empty")

        logger.info(f"🎯 目标仓库: {repo_url}")
        logger.info("📊 分析模式: 完整分析 (包含向量化)")

        # 初始化共享状态
        shared.setdefault("status", "processing")
        shared["current_stage"] = "initialization"

        logger.info("✅ 流程初始化完成")
        return shared

    async def post_async(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: str) -> Dict[str, Any]:
        """流程后处理"""
        # 更新最终状态
        if "result_filepath" in shared:
            shared["status"] = "completed"
            logger.info(f"Analysis completed successfully: {shared['result_filepath']}")
        else:
            shared["status"] = "failed"
            logger.error("Analysis failed: no result file generated")

        return shared


class QuickAnalysisFlow(AsyncFlow):
    """快速分析流程（跳过向量化）"""

    def __init__(self, batch_size: int = 5):
        super().__init__()

        # 创建节点实例（跳过向量化节点）
        self.github_info_node = GitHubInfoFetchNode()
        self.git_clone_node = GitCloneNode()
        self.code_parse_node = CodeParsingBatchNode(batch_size=batch_size)
        self.readme_analysis_node = ReadmeAnalysisNode()
        self.save_results_node = SaveResultsNode()
        self.save_mysql_node = SaveToMySQLNode()

        # 构建流程链
        self._build_flow()

    def _build_flow(self):
        """构建快速分析流程"""
        # 设置起始节点
        self.start(self.github_info_node)

        # 构建节点链：GitHub信息 -> 克隆 -> 代码解析 -> README分析 -> 保存结果
        (
            self.github_info_node
            >> self.git_clone_node
            >> self.code_parse_node
            >> self.readme_analysis_node
            >> self.save_results_node
            >> self.save_mysql_node
        )

        logger.info("Quick analysis flow constructed")

    async def prep_async(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """流程预处理"""
        logger.info("🚀 ========== 开始 GitHub 仓库快速分析流程 ==========")
        logger.info("📋 阶段: 流程初始化 (QuickAnalysisFlow.prep_async)")

        # 验证输入
        if "repo_url" not in shared:
            logger.error("❌ Repository URL is missing from shared data")
            raise ValueError("Repository URL is required")

        repo_url = shared.get("repo_url")
        if repo_url is None:
            logger.error("❌ Repository URL is None")
            raise ValueError("Repository URL cannot be None")

        if not isinstance(repo_url, str):
            logger.error(f"❌ Repository URL is not a string: {type(repo_url)}")
            raise ValueError("Repository URL must be a string")

        if not repo_url.strip():
            logger.error("❌ Repository URL is empty")
            raise ValueError("Repository URL cannot be empty")

        logger.info(f"🎯 目标仓库: {repo_url}")
        logger.info("⚡ 分析模式: 快速分析 (跳过向量化)")

        shared.setdefault("status", "processing")
        shared["current_stage"] = "initialization"

        logger.info("✅ 流程初始化完成")
        return shared

    async def post_async(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: str) -> Dict[str, Any]:
        """流程后处理"""
        if "result_filepath" in shared:
            shared["status"] = "completed"
            logger.info(f"Quick analysis completed: {shared['result_filepath']}")
        else:
            shared["status"] = "failed"
            logger.error("Quick analysis failed")

        return shared


async def analyze_repository(
    repo_url: str, use_vectorization: bool = True, batch_size: int = 10, progress_callback=None
) -> Dict[str, Any]:
    """
    分析GitHub仓库的便捷函数

    Args:
        repo_url: GitHub仓库URL
        use_vectorization: 是否使用向量化（RAG）
        batch_size: 批处理大小
        progress_callback: 进度回调函数，接收 (completed, current_file) 参数

    Returns:
        分析结果字典
    """
    # 准备共享数据
    shared = {"repo_url": repo_url, "progress_callback": progress_callback}

    # 选择流程
    if use_vectorization:
        flow = GitHubAnalysisFlow()
        # 设置批次大小
        if hasattr(flow.code_parse_node, "batch_size"):
            flow.code_parse_node.batch_size = batch_size
    else:
        flow = QuickAnalysisFlow(batch_size=batch_size)

    try:
        # 执行分析流程
        result = await flow.run_async(shared)

        # 返回完整的共享数据
        return shared

    except Exception as e:
        logger.error(f"Analysis failed for {repo_url}: {str(e)}")
        shared["status"] = "failed"
        shared["error"] = str(e)
        return shared


# 流程工厂函数
def create_analysis_flow(flow_type: str = "full", **kwargs) -> AsyncFlow:
    """
    创建分析流程的工厂函数

    Args:
        flow_type: 流程类型 ("full", "quick")
        **kwargs: 流程参数

    Returns:
        分析流程实例
    """
    if flow_type == "full":
        return GitHubAnalysisFlow(**kwargs)
    elif flow_type == "quick":
        return QuickAnalysisFlow(**kwargs)
    else:
        raise ValueError(f"Unknown flow type: {flow_type}")


# 批量分析函数
async def analyze_repositories_batch(
    repo_urls: List[str], use_vectorization: bool = True, batch_size: int = 5
) -> List[Dict[str, Any]]:
    """
    批量分析多个仓库

    Args:
        repo_urls: 仓库URL列表
        use_vectorization: 是否使用向量化
        batch_size: 批处理大小

    Returns:
        分析结果列表
    """
    import asyncio

    results = []

    # 分批处理仓库
    for i in range(0, len(repo_urls), batch_size):
        batch_urls = repo_urls[i : i + batch_size]

        # 并行分析当前批次
        tasks = [analyze_repository(url, use_vectorization, batch_size) for url in batch_urls]

        batch_results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in batch_results:
            if isinstance(result, Exception):
                logger.error(f"Batch analysis error: {str(result)}")
                results.append({"status": "failed", "error": str(result)})
            else:
                results.append(result)

        # 批次间延迟
        if i + batch_size < len(repo_urls):
            await asyncio.sleep(2)

    return results
