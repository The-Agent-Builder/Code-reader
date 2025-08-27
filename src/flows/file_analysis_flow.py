"""
本地文件夹分析主流程
整合所有节点，实现完整的代码仓库解析流程
"""

from typing import Dict, Any, List
from pocketflow import AsyncFlow

from ..nodes import (
    LocalFolderNode,
    VectorizeRepoNode,
    CodeParsingBatchNode,
    ReadmeAnalysisNode,
    SaveResultsNode,
    SaveToMySQLNode,
)
from ..utils.logger import logger


class GitHubAnalysisFlow(AsyncFlow):
    """本地文件夹分析主流程（原GitHub分析流程）"""

    def __init__(self):
        super().__init__()

        # 创建节点实例
        self.local_folder_node = LocalFolderNode()
        
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
        self.start(self.local_folder_node)

        # 构建节点链：本地文件夹 -> 向量化 -> 代码解析 -> README分析 -> 保存结果
        (
            self.local_folder_node
            >> self.vectorize_node
            >> self.code_parse_node
            >> self.readme_analysis_node
            >> self.save_results_node
            >> self.save_mysql_node
        )

        logger.info("Local folder analysis flow constructed")

    async def prep_async(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """流程预处理"""
        logger.info("🚀 ========== 开始本地文件夹分析流程 ==========")
        logger.info("📋 阶段: 流程初始化 (GitHubAnalysisFlow.prep_async)")

        # 验证输入
        if "local_folder_path" not in shared:
            logger.error("❌ 缺少本地文件夹路径")
            raise ValueError("Local folder path is required")

        local_folder_path = shared.get("local_folder_path")
        if local_folder_path is None:
            logger.error("❌ 本地文件夹路径为 None")
            raise ValueError("Local folder path cannot be None")

        if not isinstance(local_folder_path, str):
            logger.error(f"❌ 本地文件夹路径类型错误: {type(local_folder_path)}")
            raise ValueError("Local folder path must be a string")

        if not local_folder_path.strip():
            logger.error("❌ 本地文件夹路径为空")
            raise ValueError("Local folder path cannot be empty")

        logger.info(f"🎯 目标文件夹: {local_folder_path}")
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
            logger.info(f"Local folder analysis completed successfully: {shared['result_filepath']}")
        else:
            shared["status"] = "failed"
            logger.error("Local folder analysis failed: no result file generated")

        return shared


class QuickAnalysisFlow(AsyncFlow):
    """快速分析流程（跳过向量化）"""

    def __init__(self, batch_size: int = 5):
        super().__init__()

        # 创建节点实例（跳过向量化节点）
        self.local_folder_node = LocalFolderNode()
        self.code_parse_node = CodeParsingBatchNode(batch_size=batch_size)
        self.readme_analysis_node = ReadmeAnalysisNode()
        self.save_results_node = SaveResultsNode()
        self.save_mysql_node = SaveToMySQLNode()

        # 构建流程链
        self._build_flow()

    def _build_flow(self):
        """构建快速分析流程"""
        # 设置起始节点
        self.start(self.local_folder_node)

        # 构建节点链：本地文件夹 -> 代码解析 -> README分析 -> 保存结果
        (
            self.local_folder_node
            >> self.code_parse_node
            >> self.readme_analysis_node
            >> self.save_results_node
            >> self.save_mysql_node
        )

        logger.info("Quick analysis flow constructed")

    async def prep_async(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """流程预处理"""
        logger.info("🚀 ========== 开始本地文件夹快速分析流程 ==========")
        logger.info("📋 阶段: 流程初始化 (QuickAnalysisFlow.prep_async)")

        # 验证输入
        if "local_folder_path" not in shared:
            logger.error("❌ 缺少本地文件夹路径")
            raise ValueError("Local folder path is required")

        local_folder_path = shared.get("local_folder_path")
        if local_folder_path is None:
            logger.error("❌ 本地文件夹路径为 None")
            raise ValueError("Local folder path cannot be None")

        if not isinstance(local_folder_path, str):
            logger.error(f"❌ 本地文件夹路径类型错误: {type(local_folder_path)}")
            raise ValueError("Local folder path must be a string")

        if not local_folder_path.strip():
            logger.error("❌ 本地文件夹路径为空")
            raise ValueError("Local folder path cannot be empty")

        logger.info(f"🎯 目标文件夹: {local_folder_path}")
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
    local_folder_path: str, use_vectorization: bool = True, batch_size: int = 10, progress_callback=None
) -> Dict[str, Any]:
    """
    分析本地文件夹的便捷函数（原analyze_repository函数）

    Args:
        local_folder_path: 本地文件夹路径
        use_vectorization: 是否使用向量化（RAG）
        batch_size: 批处理大小
        progress_callback: 进度回调函数，接收 (completed, current_file) 参数

    Returns:
        分析结果字典
    """
    # 准备共享数据
    shared = {"local_folder_path": local_folder_path, "progress_callback": progress_callback}

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
        logger.error(f"Analysis failed for {local_folder_path}: {str(e)}")
        shared["status"] = "failed"
        shared["error"] = str(e)
        return shared


async def analyze_local_folder(
    local_folder_path: str, use_vectorization: bool = True, batch_size: int = 10, progress_callback=None
) -> Dict[str, Any]:
    """
    分析本地文件夹的便捷函数

    Args:
        local_folder_path: 本地文件夹路径
        use_vectorization: 是否使用向量化（RAG）
        batch_size: 批处理大小
        progress_callback: 进度回调函数，接收 (completed, current_file) 参数

    Returns:
        分析结果字典
    """
    # 准备共享数据
    shared = {"local_folder_path": local_folder_path, "progress_callback": progress_callback}

    # 创建本地文件夹分析流程
    flow = LocalFolderAnalysisFlow(use_vectorization=use_vectorization, batch_size=batch_size)

    try:
        # 执行分析流程
        result = await flow.run_async(shared)

        # 返回完整的共享数据
        return shared

    except Exception as e:
        logger.error(f"Local folder analysis failed for {local_folder_path}: {str(e)}")
        shared["status"] = "failed"
        shared["error"] = str(e)
        return shared


# 流程工厂函数
def create_analysis_flow(flow_type: str = "full", **kwargs) -> AsyncFlow:
    """
    创建分析流程的工厂函数

    Args:
        flow_type: 流程类型 ("full", "quick", "local_full", "local_quick")
                  - "full": 完整本地文件夹分析（包含向量化）
                  - "quick": 快速本地文件夹分析（跳过向量化）
                  - "local_full": 完整本地文件夹分析（包含向量化）
                  - "local_quick": 快速本地文件夹分析（跳过向量化）
        **kwargs: 流程参数

    Returns:
        分析流程实例
    """
    if flow_type == "full":
        return GitHubAnalysisFlow(**kwargs)
    elif flow_type == "quick":
        return QuickAnalysisFlow(**kwargs)
    elif flow_type == "local_full":
        return LocalFolderAnalysisFlow(use_vectorization=True, **kwargs)
    elif flow_type == "local_quick":
        return LocalFolderAnalysisFlow(use_vectorization=False, **kwargs)
    else:
        raise ValueError(f"Unknown flow type: {flow_type}. Supported types: full, quick, local_full, local_quick")


# 批量分析函数
async def analyze_repositories_batch(
    local_folder_paths: List[str], use_vectorization: bool = True, batch_size: int = 5
) -> List[Dict[str, Any]]:
    """
    批量分析多个本地文件夹

    Args:
        local_folder_paths: 本地文件夹路径列表
        use_vectorization: 是否使用向量化
        batch_size: 批处理大小

    Returns:
        分析结果列表
    """
    import asyncio

    results = []

    # 分批处理文件夹
    for i in range(0, len(local_folder_paths), batch_size):
        batch_paths = local_folder_paths[i : i + batch_size]

        # 并行分析当前批次
        tasks = [analyze_repository(path, use_vectorization, batch_size) for path in batch_paths]

        batch_results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in batch_results:
            if isinstance(result, Exception):
                logger.error(f"Batch analysis error: {str(result)}")
                results.append({"status": "failed", "error": str(result)})
            else:
                results.append(result)

        # 批次间延迟
        if i + batch_size < len(local_folder_paths):
            await asyncio.sleep(2)

    return results


class LocalFolderAnalysisFlow(AsyncFlow):
    """本地文件夹分析流程（跳过GitHub信息获取和克隆）"""

    def __init__(self, use_vectorization: bool = True, batch_size: int = 5):
        super().__init__()
        self.use_vectorization = use_vectorization

        # 创建节点实例
        self.local_folder_node = LocalFolderNode()
        if use_vectorization:
            self.vectorize_node = VectorizeRepoNode()
        self.code_parse_node = CodeParsingBatchNode(batch_size=batch_size)
        self.readme_analysis_node = ReadmeAnalysisNode()
        self.save_results_node = SaveResultsNode()
        self.save_mysql_node = SaveToMySQLNode()

        # 构建流程链
        self._build_flow()

    def _build_flow(self):
        """构建本地文件夹分析流程"""
        # 设置起始节点
        self.start(self.local_folder_node)

        if self.use_vectorization:
            # 完整流程：本地文件夹 -> 向量化 -> 代码解析 -> README分析 -> 保存结果
            (
                self.local_folder_node
                >> self.vectorize_node
                >> self.code_parse_node
                >> self.readme_analysis_node
                >> self.save_results_node
                >> self.save_mysql_node
            )
            logger.info("Local folder analysis flow with vectorization constructed")
        else:
            # 快速流程：本地文件夹 -> 代码解析 -> README分析 -> 保存结果
            (
                self.local_folder_node
                >> self.code_parse_node
                >> self.readme_analysis_node
                >> self.save_results_node
                >> self.save_mysql_node
            )
            logger.info("Local folder quick analysis flow constructed")

    async def prep_async(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """流程预处理"""
        logger.info("🚀 ========== 开始本地文件夹分析流程 ==========")
        logger.info("📋 阶段: 流程初始化 (LocalFolderAnalysisFlow.prep_async)")

        # 验证输入
        if "local_folder_path" not in shared:
            logger.error("❌ 缺少本地文件夹路径")
            raise ValueError("Local folder path is required")

        local_folder_path = shared.get("local_folder_path")
        if local_folder_path is None:
            logger.error("❌ 本地文件夹路径为 None")
            raise ValueError("Local folder path cannot be None")

        if not isinstance(local_folder_path, str):
            logger.error(f"❌ 本地文件夹路径类型错误: {type(local_folder_path)}")
            raise ValueError("Local folder path must be a string")

        if not local_folder_path.strip():
            logger.error("❌ 本地文件夹路径为空")
            raise ValueError("Local folder path cannot be empty")

        logger.info(f"🎯 目标文件夹: {local_folder_path}")
        if self.use_vectorization:
            logger.info("📊 分析模式: 完整分析 (包含向量化)")
        else:
            logger.info("⚡ 分析模式: 快速分析 (跳过向量化)")

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
            logger.info(f"Local folder analysis completed successfully: {shared['result_filepath']}")
        else:
            shared["status"] = "failed"
            logger.error("Local folder analysis failed: no result file generated")

        return shared
