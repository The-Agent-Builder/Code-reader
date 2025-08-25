"""
VectorizeRepoNode - 对本地仓库构建向量知识库
Design: AsyncNode, max_retries=2, wait=30
"""

from typing import Dict, Any, Tuple
from pathlib import Path
from pocketflow import AsyncNode

from ..utils.rag_api_client import RAGVectorStoreProvider
from ..utils.logger import logger
from ..utils.error_handler import VectorStoreError
from ..utils.config import get_config


class VectorizeRepoNode(AsyncNode):
    """对本地仓库构建向量知识库节点"""

    def __init__(self):
        super().__init__(max_retries=2, wait=30)
        config = get_config()
        self.vectorstore_provider = RAGVectorStoreProvider(config.rag_base_url)

    async def prep_async(self, shared: Dict[str, Any]) -> Tuple[Path, Dict[str, Any]]:
        """
        扫描目录下所有可分析的源码文件（排除非源码文件）

        Data Access:
        - Read: shared.local_path
        """
        logger.info("=" * 60)
        logger.info("📋 阶段 3/4: 向量化构建 (VectorizeRepoNode)")
        shared["current_stage"] = "vectorization"

        local_path = shared.get("local_path")
        repo_info = shared.get("repo_info")

        if not local_path or not repo_info:
            logger.error("❌ 向量化构建需要提供本地路径和仓库信息")
            raise VectorStoreError("Local path and repo info are required")

        local_path = Path(local_path)
        if not local_path.exists():
            logger.error(f"❌ 本地仓库路径不存在: {local_path}")
            raise VectorStoreError(f"Local repository path does not exist: {local_path}")

        logger.info(f"🔍 准备构建向量知识库: {local_path}")
        return local_path, repo_info

    async def exec_async(self, prep_res: Tuple[Path, Dict[str, Any]]) -> str:
        """
        使用 RAG 工具构建知识库
        """
        local_path, repo_info = prep_res

        try:
            vectorstore_path = await self.vectorstore_provider.build_vectorstore(local_path, repo_info)
            # logger.info(f"Vector store created at: {vectorstore_path}")
            return vectorstore_path
        except Exception as e:
            logger.error(f"❌ 向量化构建失败: {str(e)}")
            raise VectorStoreError(f"Failed to build vector store: {str(e)}")

    async def post_async(self, shared: Dict[str, Any], prep_res: Tuple, exec_res: str) -> str:
        """
        设置 shared.vectorstore_index，便于后续 RAG 检索调用

        Data Access:
        - Write: shared.vectorstore_index (RAG API 索引名称)
        - Write: shared.vectorstore_path (兼容性路径)
        """
        # 设置 RAG API 索引名称
        shared["vectorstore_index"] = exec_res

        # 为了兼容性，也设置路径（虽然现在使用的是远程 RAG API）
        repo_info = prep_res[1]
        repo_name = (
            repo_info.get("full_name", "unknown").split("/")[-1]
            if "/" in repo_info.get("full_name", "")
            else repo_info.get("full_name", "unknown")
        )
        shared["vectorstore_path"] = f"./data/vectorstores/{repo_name}"

        # logger.info(f"RAG API 索引已设置: {exec_res}")
        # logger.info(f"兼容性路径已设置: {shared['vectorstore_path']}")
        return "default"
