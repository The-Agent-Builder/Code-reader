"""
WebCodeAnalysisNode - 从数据库读取文件并进行AI分析
专门用于Web前端的"分析数据模型"模块
"""

import asyncio
import aiohttp
from typing import Dict, Any, List
from pathlib import Path
from pocketflow import AsyncParallelBatchNode

from ..utils.llm_parser import LLMParser
from ..utils.rag_api_client import RAGAPIClient
from ..utils.logger import logger
from ..utils.error_handler import LLMParsingError
from ..utils.config import get_config


class WebCodeAnalysisNode(AsyncParallelBatchNode):
    """Web代码分析节点 - 从数据库读取文件并进行AI分析"""

    def __init__(self, batch_size: int = None):
        super().__init__(max_retries=2, wait=20)
        self.llm_parser = LLMParser()  # LLM解析器

        config = get_config()
        self.rag_client = RAGAPIClient(config.rag_base_url)  # RAG API客户端
        self.api_base_url = config.api_base_url  # 后端API地址
        self.batch_size = batch_size if batch_size is not None else config.llm_batch_size
        self.max_concurrent = config.llm_max_concurrent

    async def prep_async(self, shared: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        从数据库获取文件列表并准备分析参数

        Data Access:
        - Read: shared.task_id, shared.vectorstore_index
        """
        logger.info("=" * 60)
        logger.info("📋 阶段: Web代码分析 (WebCodeAnalysisNode)")

        shared["current_stage"] = "web_code_analysis"

        task_id = shared.get("task_id")
        vectorstore_index = shared.get("vectorstore_index")

        if not task_id:
            logger.error("❌ Web代码分析需要提供任务ID")
            raise LLMParsingError("Task ID is required")

        if not vectorstore_index:
            logger.error("❌ Web代码分析需要提供向量索引")
            raise LLMParsingError("Vectorstore index is required")

        logger.info(f"🔍 获取任务 {task_id} 的文件列表")

        # 1. 从API获取文件列表（不包含代码内容）
        file_list = await self._get_repository_files(task_id)
        if not file_list:
            logger.warning(f"任务 {task_id} 没有找到文件")
            return []

        logger.info(f"📁 找到 {len(file_list)} 个文件需要分析")

        # 2. 为每个文件准备分析参数
        file_items = []
        for file_info in file_list:
            file_analysis_id = file_info.get("id")
            file_path = file_info.get("file_path")
            language = file_info.get("language", "unknown")

            if not file_analysis_id or not file_path:
                logger.warning(f"跳过无效文件信息: {file_info}")
                continue

            file_items.append(
                {
                    "file_analysis_id": file_analysis_id,
                    "file_path": file_path,
                    "language": language,
                    "task_id": task_id,
                    "vectorstore_index": vectorstore_index,
                    "shared": shared,  # 传递共享数据引用
                }
            )

        logger.info(f"准备分析 {len(file_items)} 个文件")

        # 添加进度回调信息
        progress_callback = shared.get("progress_callback")
        for i, file_item in enumerate(file_items):
            file_item["progress_callback"] = progress_callback
            file_item["current_index"] = i

        return file_items

    async def exec_async(self, file_item: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析单个文件：获取代码内容 -> RAG检索 -> LLM分析
        """
        try:
            file_analysis_id = file_item["file_analysis_id"]
            file_path = file_item["file_path"]
            task_id = file_item["task_id"]

            logger.info(f"🔍 开始分析文件: {file_path} (ID: {file_analysis_id})")

            # 1. 获取文件的完整代码内容
            file_content = await self._get_file_content(file_analysis_id, task_id)
            if not file_content:
                logger.warning(f"无法获取文件内容: {file_path}")
                return {
                    "file_analysis_id": file_analysis_id,
                    "file_path": file_path,
                    "analysis_items": [],
                    "error": "无法获取文件内容",
                }

            # 2. 使用RAG获取相关上下文
            context = await self._get_rag_context(file_item, file_content)

            # 3. 调用LLM进行详细分析
            result = await self.llm_parser.parse_code_file_detailed(
                file_path, file_content, file_item["language"], context
            )

            # 4. 添加文件分析ID到结果中
            if not result.get("error"):
                result["file_analysis_id"] = file_analysis_id
                # 为每个分析项添加file_analysis_id
                for item in result.get("analysis_items", []):
                    item["file_analysis_id"] = file_analysis_id

            # 5. 调用进度回调
            progress_callback = file_item.get("progress_callback")
            if progress_callback:
                try:
                    progress_callback(current_file=file_path)
                except Exception as e:
                    logger.warning(f"Progress callback failed: {str(e)}")

            logger.info(f"✅ 完成文件分析: {file_path}")
            return result

        except Exception as e:
            logger.error(f"Failed to analyze file {file_item['file_path']}: {str(e)}")
            return {
                "file_analysis_id": file_item["file_analysis_id"],
                "file_path": file_item["file_path"],
                "analysis_items": [],
                "error": str(e),
            }

    async def _get_repository_files(self, task_id: int) -> List[Dict[str, Any]]:
        """从API获取仓库文件列表"""
        try:
            url = f"{self.api_base_url}/api/repository/files/{task_id}"
            params = {"include_code_content": False}

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("files", [])
                    elif response.status == 404:
                        logger.warning(f"任务 {task_id} 没有找到文件")
                        return []
                    else:
                        logger.error(f"获取文件列表失败: HTTP {response.status}")
                        return []

        except Exception as e:
            logger.error(f"获取文件列表时发生错误: {str(e)}")
            return []

    async def _get_file_content(self, file_analysis_id: int, task_id: int) -> str:
        """从API获取单个文件的代码内容"""
        try:
            url = f"{self.api_base_url}/api/repository/file-analysis/{file_analysis_id}"
            params = {"task_id": task_id}

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        file_analysis = data.get("file_analysis", {})
                        return file_analysis.get("code_content", "")
                    else:
                        logger.error(f"获取文件内容失败: HTTP {response.status}")
                        return ""

        except Exception as e:
            logger.error(f"获取文件内容时发生错误: {str(e)}")
            return ""

    async def _get_rag_context(self, file_item: Dict[str, Any], content: str) -> str:
        """
        使用RAG API获取与当前文件相关的上下文信息
        复用CodeParsingBatchNode的RAG逻辑
        """
        try:
            vectorstore_index = file_item.get("vectorstore_index")
            if not vectorstore_index:
                logger.warning("RAG API 索引不可用")
                return ""

            file_path = file_item["file_path"]
            language = file_item["language"]

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

            # 2.2 对每个类分别进行检索
            for class_name in class_method_relationships.keys():
                search_queries.append(f"{class_name} 类 {language}")
                search_targets.append(f"文件-类({class_name})")

            # 2.3 对每个独立函数分别进行检索
            for func_name in independent_functions:
                search_queries.append(f"{func_name} 函数 {language}")
                search_targets.append(f"文件-函数({func_name})")

            total_searches = len(search_queries)
            logger.info(f"🔍 开始为 {file_path} 检索相关上下文，共 {total_searches} 个查询")

            # 3. 执行检索，收集所有结果
            all_results = []
            for i, (query, target) in enumerate(zip(search_queries, search_targets), 1):
                try:
                    logger.info(f"   [{i}/{total_searches}] 检索 {target}: {query}")
                    results = self.rag_client.search_knowledge(query=query, index_name=vectorstore_index, top_k=5)

                    found_count = 0
                    for result in results:
                        doc = result.get("document", {})
                        title = doc.get("title", "")
                        content_snippet = doc.get("content", "")
                        if title and content_snippet:
                            all_results.append(
                                {
                                    "title": title,
                                    "content": content_snippet,
                                    "file_path": doc.get("file_path", ""),
                                    "file": doc.get("file", ""),
                                    "category": doc.get("category", ""),
                                    "language": doc.get("language", ""),
                                    "query": query,
                                    "search_target": target,
                                }
                            )
                            found_count += 1

                    logger.info(f"       找到 {found_count} 个相关结果")

                except Exception as e:
                    logger.warning(f"   [{i}/{total_searches}] 检索失败 {target}: {str(e)}")
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

                # 按目标分组显示结果
                for target, results in target_groups.items():
                    context_parts.append(f"\n--- 检索目标: {target} ---")
                    for i, result in enumerate(results[:3], 1):  # 每个目标最多3个结果
                        title = result.get("title", "Unknown")
                        content_snippet = result.get("content", "")
                        file_info = result.get("file", result.get("file_path", ""))
                        category = result.get("category", "")

                        # 截取合适长度
                        snippet = content_snippet[:400] + "..." if len(content_snippet) > 400 else content_snippet

                        context_parts.append(f"  {i}. {title} ({category})")
                        if file_info:
                            context_parts.append(f"     文件: {file_info}")
                        context_parts.append(f"     {snippet}\n")

                context = "\n".join(context_parts)
                logger.info(f"✅ 为 {file_path} 检索到 {len(unique_results)} 个相关上下文")
                return context
            else:
                logger.info(f"⚠️ 未找到 {file_path} 的相关上下文")
                return ""

        except Exception as e:
            logger.warning(f"Failed to get RAG context for {file_item['file_path']}: {str(e)}")
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
                logger.warning(f"Failed to parse AST for independent functions: {e}")
                return self._extract_independent_functions_regex(content, class_relationships)
        else:
            # 对于非Python语言，使用正则表达式
            return self._extract_independent_functions_regex(content, class_relationships)

        # 过滤和限制数量
        filtered_functions = []
        common_words = {"main", "init", "test", "setup", "teardown", "__init__", "__main__"}

        for func_name in set(independent_functions):
            if len(func_name) > 2 and func_name.lower() not in common_words:
                filtered_functions.append(func_name)

        return filtered_functions[:10]  # 限制数量

    def _extract_independent_functions_regex(
        self, content: str, class_relationships: Dict[str, List[str]]
    ) -> List[str]:
        """使用正则表达式提取独立函数（备用方法）"""
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

        return list(set(independent_functions))

    def _extract_class_method_relationships_regex(self, content: str) -> Dict[str, List[str]]:
        """使用正则表达式提取类-方法关系（回退方案）"""
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

    async def post_async(
        self, shared: Dict[str, Any], prep_res: List[Dict[str, Any]], exec_res: List[Dict[str, Any]]
    ) -> str:
        """
        整理所有结果，更新共享状态

        Data Access:
        - Write: shared.web_code_analysis
        """
        # 过滤掉错误结果
        valid_results = [r for r in exec_res if not r.get("error")]
        error_count = len(exec_res) - len(valid_results)

        shared["web_code_analysis"] = valid_results

        # 统计信息
        total_analysis_items = sum(len(r.get("analysis_items", [])) for r in valid_results)
        total_functions = sum(len(r.get("functions", [])) for r in valid_results)
        total_classes = sum(len(r.get("classes", [])) for r in valid_results)

        logger.info(
            f"Web code analysis completed: {len(valid_results)} files, "
            f"{total_functions} functions, {total_classes} classes, "
            f"{total_analysis_items} analysis items, {error_count} errors"
        )

        return "default"

    async def exec_fallback_async(self, file_item: Dict[str, Any], exc: Exception) -> Dict[str, Any]:
        """
        若解析失败，返回错误信息
        """
        logger.warning(f"Fallback parsing for {file_item['file_path']}: {str(exc)}")

        return {
            "file_analysis_id": file_item["file_analysis_id"],
            "file_path": file_item["file_path"],
            "analysis_items": [],
            "error": f"Fallback: {str(exc)}",
        }
