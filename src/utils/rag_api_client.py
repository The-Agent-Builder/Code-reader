"""
RAG API 客户端
使用您提供的 RAG API 服务进行文档向量化和检索
"""

import requests
import time
import asyncio
from typing import List, Dict, Any, Optional
from pathlib import Path

from .logger import logger
from .error_handler import VectorStoreError


class RAGAPIClient:
    """RAG API 客户端，参照 demo.py 实现"""

    def __init__(self, base_url: str):
        """
        初始化 RAG API 客户端

        Args:
            base_url: RAG API 服务地址（必需参数）
        """
        if not base_url:
            raise ValueError("RAG API base_url is required")
        self.base_url = base_url
        self.index_name = None

    def check_health(self) -> bool:
        """检查服务健康状态"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                logger.info("✅ RAG API 服务运行正常")
                return True
            else:
                logger.error(f"❌ RAG API 服务异常: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ 无法连接 RAG API 服务: {e}")
            return False

    def create_knowledge_base(
        self, documents: List[Dict[str, Any]], vector_field: str = "content", project_name: str = None
    ) -> Optional[str]:
        """
        创建知识库，参照 demo.py 的 create_documents 方法

        Args:
            documents: 文档列表，每个文档包含 title、content、category 等字段
            vector_field: 向量化字段名
            project_name: 项目名称，用于索引前缀

        Returns:
            索引名称，失败返回 None
        """
        logger.info(f"📚 正在创建知识库，文档数量: {len(documents)}")
        if project_name:
            logger.info(f"📂 项目名称: {project_name}")

        try:
            # 构建请求数据，参照 demo.py 格式
            request_data = {"documents": documents, "vector_field": vector_field}

            # 如果提供了项目名称，添加到请求中（用于生成带前缀的索引名）
            # if project_name:
            # request_data["project_name"] = project_name

            response = requests.post(
                f"{self.base_url}/documents",
                headers={"Content-Type": "application/json"},
                json=request_data,
                timeout=300,  # 5分钟超时，因为向量化可能需要较长时间
            )

            if response.status_code == 200:
                result = response.json()
                self.index_name = result["index"]
                count = result["count"]
                logger.info(f"✅ 知识库创建成功")
                logger.info(f"📂 索引名称: {self.index_name}")
                logger.info(f"📄 文档数量: {count}")
                return self.index_name
            else:
                error_msg = response.json() if response.content else f"HTTP {response.status_code}"
                logger.error(f"❌ 知识库创建失败: {error_msg}")
                return None

        except requests.exceptions.Timeout:
            logger.error("❌ 创建知识库超时，请检查文档数量或网络连接")
            return None
        except Exception as e:
            logger.error(f"❌ 创建知识库时出错: {e}")
            return None

    def search_knowledge(
        self, query: str, index_name: str = None, vector_field: str = None, top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        在知识库中搜索相关文档，参照 demo.py 的 search_documents 方法

        Args:
            query: 查询文本
            index_name: 索引名称，如果为空则使用当前索引
            vector_field: 向量化字段名
            top_k: 返回最相关的文档数量

        Returns:
            相关文档列表
        """
        if not index_name:
            index_name = self.index_name

        if not index_name:
            logger.error("❌ 知识库未初始化，请先创建知识库")
            return []

        try:
            # 构建搜索请求，参照 demo.py 格式
            vf = vector_field or getattr(self, "default_vector_field", "content")
            search_data = {"query": query, "vector_field": vf, "index": index_name, "top_k": top_k}

            response = requests.post(
                f"{self.base_url}/search", headers={"Content-Type": "application/json"}, json=search_data, timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                results = result["results"]
                total = result["total"]
                took = result["took"]

                logger.info(f"🔍 搜索完成: 找到 {total} 个相关文档，耗时 {took}ms")
                return results
            else:
                error_msg = response.json() if response.content else f"HTTP {response.status_code}"
                logger.error(f"❌ 搜索失败: {error_msg}")
                return []

        except Exception as e:
            logger.error(f"❌ 搜索时出错: {e}")
            return []

    def add_documents_to_existing_index(
        self, documents: List[Dict[str, Any]], index_name: str, vector_field: str = "content", project_name: str = None
    ) -> bool:
        """
        向已存在的索引添加文档

        Args:
            documents: 文档列表
            index_name: 已存在的索引名称
            vector_field: 向量化字段名
            project_name: 项目名称（用于一致性检查）

        Returns:
            是否成功
        """
        # logger.info(f"📝 向索引 {index_name} 添加 {len(documents)} 个文档")
        # if project_name:
        #     logger.info(f"📂 项目名称: {project_name}")

        try:
            request_data = {"documents": documents, "vector_field": vector_field, "index": index_name}

            # 如果提供了项目名称，添加到请求中
            # if project_name:
            # request_data["project_name"] = project_name

            response = requests.post(
                f"{self.base_url}/documents",
                headers={"Content-Type": "application/json"},
                json=request_data,
                timeout=300,
            )

            if response.status_code == 200:
                result = response.json()
                count = result["count"]
                logger.info(f"✅ 成功添加 {count} 个文档到索引")
                return True
            else:
                error_msg = response.json() if response.content else f"HTTP {response.status_code}"
                logger.error(f"❌ 添加文档失败: {error_msg}")
                return False

        except Exception as e:
            logger.error(f"❌ 添加文档时出错: {e}")
            return False


class RAGVectorStoreProvider:
    """
    使用 RAG API 的向量存储提供者
    """

    def __init__(self, rag_api_url: str, vector_field: str = "content"):
        """
        初始化 RAG 向量存储提供者

        Args:
            rag_api_url: RAG API 服务地址（必需参数）
            vector_field: 默认向量化字段名（可在初始化时指定）
        """
        from .vectorstore_provider import CodeSplitter
        from .config import get_config

        if not rag_api_url:
            raise ValueError("RAG API URL is required")

        self.rag_client = RAGAPIClient(rag_api_url)
        self.code_splitter = CodeSplitter()
        self.base_path = Path("./data/vectorstores")
        self.base_path.mkdir(parents=True, exist_ok=True)
        # 读取批量大小配置（<=0 表示一次性上传）
        self.rag_batch_size = get_config().rag_batch_size
        # 默认向量化字段（可通过初始化参数或直接修改此属性来控制）
        self.default_vector_field = vector_field

    def _generate_store_id(self, repo_info: Dict[str, Any]) -> str:
        """生成向量存储的唯一ID（使用仓库名）"""
        full_name = repo_info.get("full_name", "unknown")
        if "/" in full_name:
            repo_name = full_name.split("/")[-1]
        else:
            repo_name = full_name
        return repo_name

    async def build_vectorstore(self, repo_path: Path, repo_info: Dict[str, Any]) -> str:
        """
        构建向量存储，使用 RAG API

        Args:
            repo_path: 本地仓库路径
            repo_info: 仓库信息

        Returns:
            向量存储标识（索引名称）
        """
        try:
            # 检查 RAG API 服务状态
            if not self.rag_client.check_health():
                raise VectorStoreError("RAG API 服务不可用")

            store_id = self._generate_store_id(repo_info)
            logger.info(f"开始为仓库 {store_id} 构建向量知识库")

            # 收集所有代码文件并转换为文档
            documents = []
            processed_files = 0

            for file_path in self._get_code_files(repo_path):
                try:
                    elements = self.code_splitter.extract_code_elements(file_path)

                    for element in elements:
                        # 构建符合 RAG API 要求的文档格式（满足：title、file、content、category）
                        # title：优先使用类名/函数名
                        if element.get("element_type") in ("function", "class"):
                            desired_title = element.get("element_name", element.get("title", ""))
                        else:
                            desired_title = element.get("title") or element.get("element_name") or file_path.stem

                        # file：相对于项目根目录（repo_path）的文件路径
                        try:
                            file_rel = str(file_path.relative_to(repo_path))
                        except Exception:
                            file_rel = element.get("file_path", str(file_path))

                        # category：根据文件类型区分“文档/代码”
                        doc_exts = {".md", ".mdx", ".rst", ".txt", ".adoc"}
                        desired_category = "文档" if file_path.suffix.lower() in doc_exts else "代码"

                        doc = {
                            "title": desired_title,
                            "file": file_rel,
                            "content": element["content"],
                            "category": desired_category,
                            # 以下为兼容/附加元信息，便于后续检索与调试
                            "language": element.get("language"),
                            # "repo_name": repo_info.get("full_name", "unknown"),
                            "start_line": element.get("start_line", 1),
                            "end_line": element.get("end_line", 1),
                        }
                        documents.append(doc)

                    processed_files += 1
                    if processed_files % 10 == 0:
                        logger.info(f"已处理 {processed_files} 个文件，提取 {len(documents)} 个代码/文档片段元素")

                except Exception as e:
                    logger.warning(f"处理文件 {file_path} 失败: {str(e)}")
                    continue

            if not documents:
                raise VectorStoreError("未找到可向量化的代码文档")

            logger.info(f"总共提取 {len(documents)} 个代码/文档片段元素，开始向量化...")

            # 分批处理大量文档，避免超时；可通过 .env 配置 RAG_BATCH_SIZE
            batch_size = self.rag_batch_size
            index_name = None

            if batch_size <= 0 or batch_size >= len(documents):
                # 一次性上传所有文档
                logger.info(f"一次性上传所有文档（共 {len(documents)} 条）")
                index_name = self.rag_client.create_knowledge_base(
                    documents=documents, vector_field="content", project_name=store_id
                )
                if not index_name:
                    raise VectorStoreError("RAG API 创建知识库失败")
            else:
                for i in range(0, len(documents), batch_size):
                    batch = documents[i : i + batch_size]
                    batch_num = i // batch_size + 1
                    total_batches = (len(documents) + batch_size - 1) // batch_size

                    logger.info(f"处理第 {batch_num}/{total_batches} 批文档 ({len(batch)} 个文档)")

                    if i == 0:
                        # 第一批：创建新的知识库，使用项目名称作为前缀
                        index_name = self.rag_client.create_knowledge_base(
                            documents=batch, vector_field="content", project_name=store_id
                        )
                        if not index_name:
                            raise VectorStoreError("RAG API 创建知识库失败")
                    else:
                        # 后续批次：添加到已存在的知识库
                        success = self.rag_client.add_documents_to_existing_index(
                            documents=batch,
                            index_name=index_name,
                            vector_field="content",
                            project_name=store_id,
                        )
                        if not success:
                            logger.warning(f"第 {batch_num} 批文档添加失败，继续处理下一批")

                    # 添加延迟避免API限流
                    if i + batch_size < len(documents):
                        await asyncio.sleep(1)

            if not index_name:
                raise VectorStoreError("RAG API 创建知识库失败")

            # 保存索引信息到本地（用于兼容性）
            store_path = self.base_path / store_id
            store_path.mkdir(parents=True, exist_ok=True)

            # 保存元数据
            metadata = {
                "index_name": index_name,
                "repo_name": store_id,
                "repo_info": repo_info,
                "document_count": len(documents),
                "processed_files": processed_files,
                "rag_api_url": self.rag_client.base_url,
            }

            import json

            with open(store_path / "metadata.json", "w", encoding="utf-8") as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)

            # 保存索引文档内容（与本地元数据相同的文件夹下）
            docs_path = store_path / "documents.jsonl"
            with open(docs_path, "w", encoding="utf-8") as f:
                for doc in documents:
                    f.write(json.dumps(doc, ensure_ascii=False) + "\n")

            logger.info(f"✅ 向量知识库构建完成")
            logger.info(f"📂 RAG API 索引: {index_name}")
            logger.info(f"📄 文档数量: {len(documents)}")
            logger.info(f"📁 本地元数据: {store_path}")

            return index_name

        except Exception as e:
            raise VectorStoreError(f"构建向量存储失败: {str(e)}")

    def _get_code_files(self, repo_path: Path) -> List[Path]:
        """获取所有代码文件"""
        from .file_filter import FileFilter, SUPPORTED_CODE_EXTENSIONS

        # 支持的文档文件扩展名
        doc_extensions = {".md", ".mdx", ".rst", ".txt", ".adoc"}
        allowed_extensions = SUPPORTED_CODE_EXTENSIONS | doc_extensions

        file_filter = FileFilter(repo_path)
        code_files = file_filter.scan_directory(repo_path, allowed_extensions)

        logger.info(f"找到 {len(code_files)} 个代码/文档文件")
        return code_files

    async def search_similar(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        相似性搜索

        Args:
            query: 查询文本
            k: 返回结果数量

        Returns:
            相似文档列表
        """
        if not self.rag_client.index_name:
            logger.error("❌ 知识库未初始化")
            return []

        return self.rag_client.search_knowledge(query, top_k=k)
