"""
WebVectorizeRepoNode - Web向量化节点，从后端API获取文件内容并创建向量知识库
Design: AsyncNode, max_retries=2, wait=30
"""

import aiohttp
import asyncio
import logging
from typing import Dict, Any, Tuple
from pathlib import Path
from pocketflow import AsyncNode

from ..utils.config import get_config

# 设置logger
logger = logging.getLogger(__name__)


class WebVectorizeRepoNode(AsyncNode):
    """Web向量化节点 - 从后端API获取文件内容并创建向量知识库"""

    def __init__(self):
        super().__init__(max_retries=2, wait=30)
        self.config = get_config()
        self.api_base_url = self.config.api_base_url
        self.rag_base_url = self.config.rag_base_url
        self.rag_batch_size = self.config.rag_batch_size

    async def prep_async(self, shared: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        """
        准备向量化操作 - 获取任务文件列表

        Data Access:
        - Read: shared.task_id (任务ID)
        - Read: shared.repo_info (仓库信息)
        """
        logger.info("=" * 60)
        logger.info("📋 阶段: Web向量化构建 (WebVectorizeRepoNode)")
        shared["current_stage"] = "vectorization"

        task_id = shared.get("task_id")
        repo_info = shared.get("repo_info")

        if not task_id:
            logger.error("❌ 向量化构建需要提供任务ID")
            raise ValueError("Task ID is required for vectorization")

        if not repo_info:
            logger.error("❌ 向量化构建需要提供仓库信息")
            raise ValueError("Repository info is required for vectorization")

        logger.info(f"🔍 准备为任务 {task_id} 构建向量知识库")
        return task_id, repo_info

    async def exec_async(self, prep_res: Tuple[int, Dict[str, Any]]) -> str:
        """
        执行向量化操作 - 从API获取文件内容并创建向量知识库
        """
        task_id, repo_info = prep_res

        try:
            # 1. 从后端API获取文件内容
            logger.info(f"📥 从API获取任务 {task_id} 的文件内容...")
            await asyncio.sleep(1)  # 1秒延迟让用户看到开始状态

            documents = await self._fetch_documents_from_api(task_id)

            if not documents:
                raise ValueError("未找到可向量化的文档")

            logger.info(f"📄 获取到 {len(documents)} 个文档")
            await asyncio.sleep(1)  # 1秒延迟

            # 2. 创建向量知识库
            store_id = self._generate_store_id(repo_info)
            logger.info(f"🚀 开始为仓库 {store_id} 创建向量知识库")
            await asyncio.sleep(2)  # 2秒延迟让用户看到创建过程

            index_name = await self._create_vector_store(documents, store_id)

            if not index_name:
                raise ValueError("向量知识库创建失败")

            logger.info(f"✅ 向量知识库创建成功，索引: {index_name}")
            await asyncio.sleep(1)  # 1秒延迟让用户看到完成状态
            return index_name

        except Exception as e:
            logger.error(f"❌ 向量化构建失败: {str(e)}")
            raise ValueError(f"Failed to build vector store: {str(e)}")

    async def post_async(self, shared: Dict[str, Any], prep_res: Tuple, exec_res: str) -> str:
        """
        向量化后处理

        Data Access:
        - Write: shared.vectorstore_index (RAG API 索引名称)
        """
        shared["vectorstore_index"] = exec_res
        logger.info(f"📂 向量索引已设置: {exec_res}")
        return "default"

    async def _fetch_documents_from_api(self, task_id: int) -> list:
        """从后端API获取文件内容"""
        try:
            api_url = f"{self.api_base_url}/api/repository/files/{task_id}?include_code_content=true"

            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, timeout=aiohttp.ClientTimeout(total=60)) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get("status") == "success" and result.get("files"):
                            return self._convert_files_to_documents(result["files"])
                        else:
                            logger.error(f"API返回错误: {result.get('message', 'Unknown error')}")
                            return []
                    else:
                        error_text = await response.text()
                        logger.error(f"API请求失败: HTTP {response.status} - {error_text}")
                        return []
        except Exception as e:
            logger.error(f"获取文件内容失败: {str(e)}")
            return []

    def _convert_files_to_documents(self, files: list) -> list:
        """将文件记录转换为RAG文档格式"""
        documents = []

        for file_record in files:
            try:
                # 跳过没有内容的文件
                if not file_record.get("code_content") or file_record["code_content"].strip() == "":
                    continue

                # 根据文件类型确定类别
                file_path = file_record.get("file_path", "")
                doc_exts = [".md", ".mdx", ".rst", ".txt", ".adoc"]
                file_extension = "." + file_path.split(".")[-1].lower() if "." in file_path else ""
                category = "文档" if file_extension in doc_exts else "代码"

                # 构建文档对象
                document = {
                    "title": file_path.split("/")[-1] if "/" in file_path else file_path,
                    "file": file_path,
                    "content": file_record["code_content"],
                    "category": category,
                    "language": file_record.get("language", "text"),
                    "start_line": 1,
                    "end_line": file_record.get("code_lines", 1),
                }

                documents.append(document)

            except Exception as e:
                logger.warning(f"转换文件记录失败: {str(e)}")
                continue

        return documents

    def _generate_store_id(self, repo_info: Dict[str, Any]) -> str:
        """生成向量存储的唯一ID"""
        full_name = repo_info.get("full_name", "unknown")
        if "/" in full_name:
            repo_name = full_name.split("/")[-1]
        else:
            repo_name = full_name
        return repo_name

    async def _create_vector_store(self, documents: list, store_id: str) -> str:
        """创建向量知识库"""
        try:
            # 检查RAG服务健康状态
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.rag_base_url}/health", timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status != 200:
                        raise ValueError("RAG API 服务不可用")

            logger.info("✅ RAG API 服务运行正常")

            # 分批处理文档
            batch_size = self.rag_batch_size
            index_name = None

            if batch_size <= 0 or batch_size >= len(documents):
                # 一次性上传所有文档
                logger.info(f"一次性上传所有文档（共 {len(documents)} 条）")
                index_name = await self._create_knowledge_base(documents, store_id)
            else:
                # 分批上传
                for i in range(0, len(documents), batch_size):
                    batch = documents[i : i + batch_size]
                    batch_num = i // batch_size + 1
                    total_batches = (len(documents) + batch_size - 1) // batch_size

                    logger.info(f"处理第 {batch_num}/{total_batches} 批文档 ({len(batch)} 个文档)")

                    if i == 0:
                        # 第一批：创建新的知识库
                        index_name = await self._create_knowledge_base(batch, store_id)
                        if not index_name:
                            raise ValueError("创建知识库失败")
                    else:
                        # 后续批次：添加到已存在的知识库
                        success = await self._add_documents_to_index(batch, index_name)
                        if not success:
                            logger.warning(f"第 {batch_num} 批文档添加失败，继续处理下一批")

                    # 添加延迟避免API限流
                    if i + batch_size < len(documents):
                        await asyncio.sleep(1)

            return index_name

        except Exception as e:
            logger.error(f"创建向量知识库失败: {str(e)}")
            raise

    async def _create_knowledge_base(self, documents: list, store_id: str) -> str:
        """调用RAG API创建知识库"""
        try:
            request_data = {"documents": documents, "vector_field": "content"}

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.rag_base_url}/documents",
                    json=request_data,
                    headers={"Content-Type": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=300),
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        index_name = result["index"]
                        count = result["count"]
                        logger.info(f"✅ 知识库创建成功，索引: {index_name}, 文档数量: {count}")
                        return index_name
                    else:
                        error_text = await response.text()
                        logger.error(f"创建知识库失败: HTTP {response.status} - {error_text}")
                        return None
        except Exception as e:
            logger.error(f"调用RAG API失败: {str(e)}")
            return None

    async def _add_documents_to_index(self, documents: list, index_name: str) -> bool:
        """向已存在的索引添加文档"""
        try:
            request_data = {"documents": documents, "vector_field": "content", "index": index_name}

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.rag_base_url}/documents",
                    json=request_data,
                    headers={"Content-Type": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=300),
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        count = result["count"]
                        logger.info(f"✅ 成功添加 {count} 个文档到索引")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"添加文档失败: HTTP {response.status} - {error_text}")
                        return False
        except Exception as e:
            logger.error(f"添加文档时出错: {str(e)}")
            return False
