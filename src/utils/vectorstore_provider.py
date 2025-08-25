"""
RAG 向量存储提供者模块
定义统一接口抽象，支持多种 RAG 引擎，实现源码切片策略（函数级/类级）
"""

import ast
import requests
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any, Optional

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

from .logger import logger
from .error_handler import VectorStoreError
from .config import get_config


class BaseVectorStore(ABC):
    """向量存储基础抽象类"""

    @abstractmethod
    async def build_vectorstore(self, repo_path: Path, repo_info: Dict[str, Any]) -> str:
        """构建向量存储"""
        pass

    @abstractmethod
    async def search_similar(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """相似性搜索"""
        pass


class CodeSplitter:
    """代码切片器"""

    SUPPORTED_EXTENSIONS = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".java": "java",
        ".cpp": "cpp",
        ".c": "c",
        ".h": "c",
        ".hpp": "cpp",
        ".cs": "csharp",
        ".go": "go",
        ".rs": "rust",
        ".php": "php",
        ".rb": "ruby",
        ".swift": "swift",
        ".kt": "kotlin",
        ".scala": "scala",
    }

    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )

    def extract_code_elements(self, file_path: Path) -> List[Dict[str, Any]]:
        """提取代码元素（函数、类等）"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            language = self.SUPPORTED_EXTENSIONS.get(file_path.suffix.lower(), "text")

            if language == "python":
                return self._extract_python_elements(content, file_path)
            else:
                return self._extract_generic_elements(content, file_path, language)

        except Exception as e:
            logger.warning(f"Failed to extract elements from {file_path}: {str(e)}")
            return []

    def _extract_python_elements(self, content: str, file_path: Path) -> List[Dict[str, Any]]:
        """提取Python代码元素"""
        elements = []

        try:
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # 构建类似rag_example.py的文档结构
                    code_segment = ast.get_source_segment(content, node) or ""
                    elements.append(
                        {
                            "title": f"函数: {node.name}",
                            "content": code_segment,
                            "category": "function",
                            "file_path": (
                                str(file_path.relative_to(file_path.parents[2]))
                                if len(file_path.parts) > 2
                                else str(file_path)
                            ),
                            "language": "python",
                            "element_type": "function",
                            "element_name": node.name,
                            "start_line": node.lineno,
                            "end_line": getattr(node, "end_lineno", node.lineno),
                            "difficulty": self._estimate_complexity(code_segment),
                        }
                    )
                elif isinstance(node, ast.ClassDef):
                    # 构建类似rag_example.py的文档结构
                    code_segment = ast.get_source_segment(content, node) or ""
                    elements.append(
                        {
                            "title": f"类: {node.name}",
                            "content": code_segment,
                            "category": "class",
                            "file_path": (
                                str(file_path.relative_to(file_path.parents[2]))
                                if len(file_path.parts) > 2
                                else str(file_path)
                            ),
                            "language": "python",
                            "element_type": "class",
                            "element_name": node.name,
                            "start_line": node.lineno,
                            "end_line": getattr(node, "end_lineno", node.lineno),
                            "difficulty": self._estimate_complexity(code_segment),
                        }
                    )
        except SyntaxError as e:
            logger.warning(f"语法错误: {file_path}: {str(e)}")

        return elements

    def _estimate_complexity(self, code: str) -> str:
        """
        估算代码复杂度，参照rag_example.py的difficulty字段

        Args:
            code: 代码内容

        Returns:
            复杂度等级：初级、中级、高级
        """
        lines = len(code.split("\n"))

        # 简单的复杂度估算规则
        if lines <= 10:
            return "初级"
        elif lines <= 30:
            return "中级"
        else:
            return "高级"

    def _extract_generic_elements(self, content: str, file_path: Path, language: str) -> List[Dict[str, Any]]:
        """提取通用代码元素（非Python）"""
        # 简单的基于行的切分策略
        lines = content.split("\n")
        chunks = []

        # 使用文本切分器
        text_chunks = self.text_splitter.split_text(content)

        for i, chunk in enumerate(text_chunks):
            # 构建类似rag_example.py的文档结构
            chunks.append(
                {
                    "title": f"{language.title()}代码片段 {i+1}",
                    "content": chunk,
                    "category": "code_chunk",
                    "file_path": (
                        str(file_path.relative_to(file_path.parents[2])) if len(file_path.parts) > 2 else str(file_path)
                    ),
                    "language": language,
                    "element_type": "chunk",
                    "element_name": f"chunk_{i}",
                    "start_line": 1,  # 简化处理
                    "end_line": len(chunk.split("\n")),
                    "chunk_index": i,
                    "difficulty": self._estimate_complexity(chunk),
                }
            )

        return chunks


class ChromaVectorStore(BaseVectorStore):
    """基于Chroma的向量存储实现"""

    def __init__(self, base_path: Optional[str] = None):
        config = get_config()
        self.base_path = Path(base_path or str(config.vectorstore_path))
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.embeddings = OpenAIEmbeddings(openai_api_key=config.openai_api_key, openai_api_base=config.openai_base_url)
        self.vectorstore = None
        self.code_splitter = CodeSplitter()

    def _generate_store_id(self, repo_info: Dict[str, Any]) -> str:
        """生成向量存储的唯一ID（使用仓库名）"""
        full_name = repo_info.get("full_name", "unknown")
        if "/" in full_name:
            # 从 "owner/repo" 中提取 "repo"
            repo_name = full_name.split("/")[-1]
        else:
            repo_name = full_name
        return repo_name

    async def build_vectorstore(self, repo_path: Path, repo_info: Dict[str, Any]) -> str:
        """构建向量存储"""
        try:
            store_id = self._generate_store_id(repo_info)
            store_path = self.base_path / store_id

            # 如果已存在，直接返回
            if store_path.exists():
                logger.info(f"Vector store already exists at {store_path}")
                self.vectorstore = Chroma(persist_directory=str(store_path), embedding_function=self.embeddings)
                return str(store_path)

            # 收集所有代码文件
            documents = []
            for file_path in self._get_code_files(repo_path):
                elements = self.code_splitter.extract_code_elements(file_path)

                for element in elements:
                    # 创建文档，使用类似rag_example.py的结构
                    doc = Document(
                        page_content=element["content"],  # 使用content字段
                        metadata={
                            "title": element["title"],
                            "category": element["category"],
                            "file_path": element["file_path"],
                            "element_type": element["element_type"],
                            "element_name": element["element_name"],
                            "start_line": element.get("start_line", 1),
                            "end_line": element.get("end_line", 1),
                            "language": element["language"],
                            "difficulty": element["difficulty"],
                            "repo_name": repo_info.get("full_name", "unknown"),
                        },
                    )
                    documents.append(doc)

            if not documents:
                raise VectorStoreError("No code documents found to vectorize")

            # 创建向量存储
            logger.info(f"Creating vector store with {len(documents)} documents")
            self.vectorstore = Chroma.from_documents(
                documents=documents, embedding=self.embeddings, persist_directory=str(store_path)
            )

            logger.info(f"Vector store created at {store_path}")
            return str(store_path)

        except Exception as e:
            raise VectorStoreError(f"Failed to build vector store: {str(e)}")

    def _get_code_files(self, repo_path: Path) -> List[Path]:
        """获取所有代码文件"""
        code_files = []

        # 忽略的目录和文件
        ignore_dirs = {".git", "__pycache__", "node_modules", ".venv", "venv", "env"}
        ignore_files = {".gitignore", ".env", "package-lock.json", "yarn.lock"}

        for file_path in repo_path.rglob("*"):
            # 跳过目录
            if file_path.is_dir():
                continue

            # 跳过忽略的目录中的文件
            if any(ignore_dir in file_path.parts for ignore_dir in ignore_dirs):
                continue

            # 跳过忽略的文件
            if file_path.name in ignore_files:
                continue

            # 检查文件扩展名
            if file_path.suffix.lower() in self.code_splitter.SUPPORTED_EXTENSIONS:
                code_files.append(file_path)

        return code_files

    async def search_similar(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """相似性搜索"""
        if not self.vectorstore:
            raise VectorStoreError("Vector store not initialized")

        try:
            results = self.vectorstore.similarity_search_with_score(query, k=k)

            formatted_results = []
            for doc, score in results:
                formatted_results.append(
                    {"content": doc.page_content, "metadata": doc.metadata, "similarity_score": score}
                )

            return formatted_results

        except Exception as e:
            raise VectorStoreError(f"Search failed: {str(e)}")


class RAGVectorStoreProvider:
    """RAG向量存储提供者"""

    def __init__(self, provider_type: str = "chroma"):
        if provider_type == "chroma":
            self.store = ChromaVectorStore()
        else:
            raise VectorStoreError(f"Unsupported vector store type: {provider_type}")

    async def build_vectorstore(self, repo_path: Path, repo_info: Dict[str, Any]) -> str:
        """构建向量存储"""
        return await self.store.build_vectorstore(repo_path, repo_info)

    async def search_similar(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """相似性搜索"""
        return await self.store.search_similar(query, k)
