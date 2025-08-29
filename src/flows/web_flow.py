"""
Web 知识库创建流程
用于处理前端上传文件后的知识库创建操作
"""

import logging
from typing import Dict, Any
from pathlib import Path
from pocketflow import AsyncFlow

from ..nodes.web_vectorize_repo_node import WebVectorizeRepoNode
from ..nodes.database_update_node import DatabaseUpdateNode

# 设置logger
logger = logging.getLogger(__name__)


class WebKnowledgeBaseFlow(AsyncFlow):
    """Web 知识库创建流程"""

    def __init__(self):
        super().__init__()

        # 创建节点实例
        self.vectorize_node = WebVectorizeRepoNode()
        self.database_update_node = DatabaseUpdateNode()

        # 构建流程链
        self._build_flow()

    def _build_flow(self):
        """构建知识库创建流程"""
        # 设置起始节点
        self.start(self.vectorize_node)

        # 构建节点链：向量化 -> 数据库更新
        self.vectorize_node >> self.database_update_node

        logger.info("Web knowledge base flow constructed")

    async def prep_async(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """流程预处理"""
        logger.info("🚀 ========== 开始 Web 知识库创建流程 ==========")
        logger.info("📋 阶段: 流程初始化 (WebKnowledgeBaseFlow.prep_async)")

        # 验证必需的输入参数
        required_fields = ["task_id", "local_path", "repo_info"]
        for field in required_fields:
            if field not in shared:
                logger.error(f"❌ 缺少必需参数: {field}")
                raise ValueError(f"Required field '{field}' is missing from shared data")

        task_id = shared.get("task_id")
        local_path = shared.get("local_path")
        repo_info = shared.get("repo_info")

        # 验证参数类型和值
        if not isinstance(task_id, int) or task_id <= 0:
            logger.error(f"❌ 任务ID无效: {task_id}")
            raise ValueError("Task ID must be a positive integer")

        if not local_path or not isinstance(local_path, (str, Path)):
            logger.error(f"❌ 本地路径无效: {local_path}")
            raise ValueError("Local path must be a valid string or Path object")

        if not repo_info or not isinstance(repo_info, dict):
            logger.error(f"❌ 仓库信息无效: {repo_info}")
            raise ValueError("Repository info must be a valid dictionary")

        # 注意：WebVectorizeRepoNode从API获取数据，不需要验证本地路径
        # 这里保留local_path参数是为了兼容性，但实际不使用

        logger.info(f"🎯 任务ID: {task_id}")
        logger.info(f"📁 本地路径: {local_path}")
        logger.info(f"📊 仓库信息: {repo_info.get('full_name', 'Unknown')}")

        # 初始化共享状态
        shared.setdefault("status", "processing")
        shared["current_stage"] = "initialization"

        logger.info("✅ 流程初始化完成")
        return shared

    async def post_async(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: str) -> Dict[str, Any]:
        """流程后处理"""
        logger.info("📋 阶段: 流程后处理 (WebKnowledgeBaseFlow.post_async)")

        # prep_res 和 exec_res 是 pocketflow 框架传递的参数，这里不需要使用
        # 我们通过 shared 状态来判断流程执行结果

        # 检查流程执行结果
        if shared.get("vectorstore_index") and shared.get("database_updated"):
            shared["status"] = "completed"
            logger.info(f"✅ 知识库创建流程完成")
            logger.info(f"📂 向量索引: {shared.get('vectorstore_index')}")
        else:
            shared["status"] = "failed"
            logger.error("❌ 知识库创建流程失败")

        logger.info("🏁 ========== Web 知识库创建流程结束 ==========")
        return shared


async def create_knowledge_base(
    task_id: int, local_path: str, repo_info: Dict[str, Any], progress_callback=None
) -> Dict[str, Any]:
    """
    创建知识库的便捷函数

    Args:
        task_id: 任务ID
        local_path: 本地仓库路径
        repo_info: 仓库信息字典
        progress_callback: 进度回调函数

    Returns:
        创建结果字典
    """
    # 准备共享数据
    shared = {"task_id": task_id, "local_path": local_path, "repo_info": repo_info, "status": "processing"}

    if progress_callback:
        shared["progress_callback"] = progress_callback

    # 创建并执行流程
    flow = WebKnowledgeBaseFlow()

    try:
        # 执行知识库创建流程
        await flow.run_async(shared)

        # 返回完整的共享数据
        return shared

    except Exception as e:
        logger.error(f"Knowledge base creation failed for task {task_id}: {str(e)}")
        shared["status"] = "failed"
        shared["error"] = str(e)
        return shared
