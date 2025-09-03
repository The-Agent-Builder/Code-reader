"""
SingleFileAnalysisNode - 单文件代码分析节点
基于 WebCodeAnalysisNode 和 CodeParsingBatchNode 的逻辑，专门用于分析单个文件
"""

import aiohttp
from typing import Dict, Any, List
from pocketflow import AsyncNode

from ..utils.llm_parser import LLMParser
from ..utils.rag_api_client import RAGAPIClient
from ..utils.logger import logger
from ..utils.error_handler import LLMParsingError
from ..utils.config import get_config


class SingleFileAnalysisNode(AsyncNode):
    """单文件代码分析节点"""

    def __init__(self):
        super().__init__()
        self.llm_parser = LLMParser()  # LLM解析器

        config = get_config()
        self.rag_client = RAGAPIClient(config.rag_base_url)  # RAG API客户端
        self.api_base_url = config.api_base_url  # 后端API地址

    async def exec_async(self, shared: Dict[str, Any]) -> str:
        """
        分析单个文件：获取代码内容 -> RAG检索 -> LLM分析

        Data Access:
        - Read: shared.file_id, shared.vectorstore_index
        - Write: shared.single_file_analysis
        """
        logger.info("=" * 60)
        logger.info("📋 阶段: 单文件代码分析 (SingleFileAnalysisNode)")

        shared["current_stage"] = "single_file_analysis"

        file_id = shared.get("file_id")
        vectorstore_index = shared.get("vectorstore_index")

        if not file_id:
            logger.error("❌ 单文件分析需要提供文件ID")
            raise LLMParsingError("File ID is required")

        if not vectorstore_index:
            logger.error("❌ 单文件分析需要提供向量索引")
            raise LLMParsingError("Vectorstore index is required")

        try:
            # 1. 获取文件信息和内容
            file_info = await self._get_file_info(file_id)
            if not file_info:
                logger.error(f"无法获取文件信息: file_id={file_id}")
                shared["single_file_analysis"] = []
                shared["status"] = "failed"
                shared["error"] = "无法获取文件信息"
                return "default"

            file_path = file_info.get("file_path", "")
            language = file_info.get("language", "unknown")
            content = file_info.get("code_content", "")

            if not content:
                logger.warning(f"文件内容为空: {file_path}")
                shared["single_file_analysis"] = []
                shared["status"] = "completed"
                return "default"

            logger.info(f"🔍 开始分析文件: {file_path} (ID: {file_id})")

            # 2. 使用RAG获取相关上下文
            context = await self._get_rag_context(file_path, content, language, vectorstore_index)

            # 3. 调用LLM进行详细分析
            result = await self.llm_parser.parse_code_file_detailed(file_path, content, language, context)

            # 4. 处理分析结果
            if not result.get("error"):
                result["file_id"] = file_id
                # 为每个分析项添加file_id
                for item in result.get("analysis_items", []):
                    item["file_id"] = file_id

                shared["single_file_analysis"] = [result]
                shared["status"] = "completed"
                logger.info(f"✅ 完成文件分析: {file_path}")
            else:
                logger.error(f"❌ 文件分析失败: {file_path}, 错误: {result.get('error')}")
                shared["single_file_analysis"] = []
                shared["status"] = "failed"
                shared["error"] = result.get("error")

            return "default"

        except Exception as e:
            logger.error(f"❌ 单文件分析过程中发生错误: {str(e)}")
            shared["single_file_analysis"] = []
            shared["status"] = "failed"
            shared["error"] = str(e)
            return "default"

    async def _get_file_info(self, file_id: int) -> Dict[str, Any]:
        """从API获取文件信息和内容"""
        try:
            # 首先获取文件基本信息
            url = f"{self.api_base_url}/api/repository/file-analysis/{file_id}"

            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("status") == "success":
                            return data.get("file_analysis", {})
                    else:
                        logger.error(f"获取文件信息失败: HTTP {response.status}")
                        return {}

        except Exception as e:
            logger.error(f"获取文件信息时发生错误: {str(e)}")
            return {}

    async def _get_rag_context(self, file_path: str, content: str, language: str, vectorstore_index: str) -> str:
        """
        使用RAG API获取与当前文件相关的上下文信息
        复用WebCodeAnalysisNode的RAG逻辑
        """
        try:
            if not vectorstore_index:
                logger.warning("RAG API 索引不可用")
                return ""

            # 1. 提取类-方法关联关系和独立函数
            class_method_relationships = self._extract_class_method_relationships(content, language)
            independent_functions = self._extract_independent_functions(content, language, class_method_relationships)

            logger.info(f"🔍 从 {file_path} 文件中提取到:")
            logger.info(f"   - 类: {list(class_method_relationships.keys())}")
            logger.info(f"   - 独立函数: {independent_functions}")

            # 2. 构建检索策略：文件 + 每个类 + 每个独立函数
            search_queries = []
            search_targets = []

            # 2.1 对文件本身进行检索
            search_queries.append(f"{file_path} {language} 文件")
            search_targets.append(f"文件-{file_path}")

            # 2.2 对每个类进行检索
            for class_name, methods in class_method_relationships.items():
                search_queries.append(f"{file_path} {class_name} 类 {language}")
                search_targets.append(f"文件-类({class_name})")

            # 2.3 对每个独立函数进行检索
            for func_name in independent_functions:
                search_queries.append(f"{file_path} {func_name} 函数 {language}")
                search_targets.append(f"文件-函数({func_name})")

            # 3. 执行检索
            all_results = []
            total_searches = len(search_queries)

            for i, (query, target) in enumerate(zip(search_queries, search_targets)):
                try:
                    logger.info(f"   [{i+1}/{total_searches}] 检索: {target}")

                    search_results = await self.rag_client.search(
                        query=query, index_name=vectorstore_index, top_k=3, score_threshold=0.3
                    )

                    if search_results and search_results.get("results"):
                        for result in search_results["results"]:
                            result["search_target"] = target
                            all_results.append(result)

                        logger.info(f"   [{i+1}/{total_searches}] ✅ 找到 {len(search_results['results'])} 个相关结果")
                    else:
                        logger.info(f"   [{i+1}/{total_searches}] ⚠️ 未找到相关结果")

                except Exception as e:
                    logger.warning(f"   [{i+1}/{total_searches}] 检索失败 {target}: {str(e)}")
                    continue

            # 4. 简单去重并组合结果
            seen_content = set()
            unique_results = []
            for result in all_results:
                content_hash = hash(result["content"])
                if content_hash not in seen_content:
                    seen_content.add(content_hash)
                    unique_results.append(result)

            # 5. 组合检索结果
            if unique_results:
                context_parts = ["=== RAG 检索上下文 ==="]

                # 按检索目标分组
                target_groups = {}
                for result in unique_results[:15]:  # 限制最多15个结果
                    target = result.get("search_target", "未知目标")
                    if target not in target_groups:
                        target_groups[target] = []
                    target_groups[target].append(result)

                # 按目标组织输出
                for target, results in target_groups.items():
                    context_parts.append(f"\n--- {target} ---")
                    for result in results:
                        title = result.get("title", "无标题")
                        content = result.get("content", "")[:500]  # 限制长度
                        context_parts.append(f"标题: {title}")
                        context_parts.append(f"内容: {content}")
                        context_parts.append("")

                context = "\n".join(context_parts)
                logger.info(f"✅ 为 {file_path} 检索到 {len(unique_results)} 个相关上下文")
                return context
            else:
                logger.info(f"⚠️ 未找到 {file_path} 的相关上下文")
                return ""

        except Exception as e:
            logger.warning(f"Failed to get RAG context for {file_path}: {str(e)}")
            return ""

    def _extract_class_method_relationships(self, content: str, language: str) -> Dict[str, List[str]]:
        """提取类和方法的关联关系"""
        import re
        import ast

        relationships = {}

        if language == "python":
            try:
                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        class_name = node.name
                        methods = []

                        # 提取类中的方法
                        for item in node.body:
                            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                                methods.append(item.name)

                        relationships[class_name] = methods

            except Exception as e:
                logger.warning(f"Failed to parse AST: {e}")
                # 回退到正则表达式
                return self._extract_class_method_relationships_regex(content)
        else:
            # 对于非 Python 语言，使用正则表达式
            return self._extract_class_method_relationships_regex(content)

        return relationships

    def _extract_class_method_relationships_regex(self, content: str) -> Dict[str, List[str]]:
        """使用正则表达式提取类和方法的关联关系"""
        import re

        relationships = {}
        lines = content.split("\n")
        current_class = None
        indent_level = 0

        for line in lines:
            stripped_line = line.strip()
            if not stripped_line:
                continue

            # 计算缩进级别
            line_indent = len(line) - len(line.lstrip())

            # 检测类定义
            class_match = re.match(r"^class\s+([A-Za-z_][A-Za-z0-9_]*)", stripped_line)
            if class_match:
                current_class = class_match.group(1)
                relationships[current_class] = []
                indent_level = line_indent
                continue

            # 检测方法定义（在类内部）
            if current_class and line_indent > indent_level:
                method_match = re.match(r"^(async\s+)?def\s+([A-Za-z_][A-Za-z0-9_]*)", stripped_line)
                if method_match:
                    method_name = method_match.group(2)
                    # 过滤掉一些无意义的方法名
                    if method_name not in {"__str__", "__repr__", "__eq__", "__hash__"}:
                        relationships[current_class].append(method_name)
            elif current_class and line_indent <= indent_level:
                # 退出当前类
                current_class = None

        return relationships

    def _extract_independent_functions(
        self, content: str, language: str, class_relationships: Dict[str, List[str]]
    ) -> List[str]:
        """提取独立函数（不在类中的函数）"""
        import re
        import ast

        independent_functions = []

        if language == "python":
            try:
                tree = ast.parse(content)

                # 收集所有类中的方法名
                class_methods = set()
                for methods in class_relationships.values():
                    class_methods.update(methods)

                # 查找模块级别的函数（不在类中的函数）
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        # 检查函数是否在模块级别（不在类中）
                        parent = getattr(node, "parent", None)
                        if parent is None or not isinstance(parent, ast.ClassDef):
                            # 这是一个模块级别的函数
                            func_name = node.name
                            if func_name not in class_methods and not func_name.startswith("_"):
                                independent_functions.append(func_name)

                # 如果AST解析没有parent信息，使用备用方法
                if not independent_functions:
                    return self._extract_independent_functions_regex(content, class_relationships)

            except Exception as e:
                logger.warning(f"Failed to parse AST for functions: {e}")
                # 回退到正则表达式
                return self._extract_independent_functions_regex(content, class_relationships)
        else:
            # 对于非 Python 语言，使用正则表达式
            return self._extract_independent_functions_regex(content, class_relationships)

        return independent_functions

    def _extract_independent_functions_regex(
        self, content: str, class_relationships: Dict[str, List[str]]
    ) -> List[str]:
        """使用正则表达式提取独立函数"""
        import re

        independent_functions = []
        lines = content.split("\n")

        # 收集所有类中的方法名
        class_methods = set()
        for methods in class_relationships.values():
            class_methods.update(methods)

        # 查找函数定义，排除类中的方法
        in_class = False
        class_indent = 0

        for line in lines:
            stripped_line = line.strip()
            if not stripped_line:
                continue

            line_indent = len(line) - len(line.lstrip())

            # 检测类定义
            if re.match(r"^class\s+", stripped_line):
                in_class = True
                class_indent = line_indent
                continue

            # 检查是否退出类
            if in_class and line_indent <= class_indent and stripped_line and not stripped_line.startswith("#"):
                if not re.match(r"^(def|async\s+def|@)", stripped_line):
                    in_class = False

            # 查找函数定义
            func_match = re.match(r"^(async\s+)?def\s+([A-Za-z_][A-Za-z0-9_]*)", stripped_line)
            if func_match and not in_class:
                func_name = func_match.group(2)
                if func_name not in class_methods and not func_name.startswith("_"):
                    independent_functions.append(func_name)

        return independent_functions
