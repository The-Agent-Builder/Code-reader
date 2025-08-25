"""
CodeParsingBatchNode - 并行解析所有源码文件，提取结构化信息
Design: AsyncParallelBatchNode, batch_size=10, max_retries=2, wait=20
"""

from typing import Dict, Any, List
from pathlib import Path
from pocketflow import AsyncParallelBatchNode

from ..utils.llm_parser import LLMParser
from ..utils.rag_api_client import RAGAPIClient
from ..utils.logger import logger
from ..utils.error_handler import LLMParsingError
from ..utils.config import get_config


class CodeParsingBatchNode(AsyncParallelBatchNode):
    """并行解析所有源码文件，提取结构化信息节点"""

    def __init__(self, batch_size: int = None):
        super().__init__(max_retries=2, wait=20)
        self.llm_parser = LLMParser()  # LLM解析器

        config = get_config()
        self.rag_client = RAGAPIClient(config.rag_base_url)  # RAG API客户端
        self.batch_size = batch_size if batch_size is not None else config.llm_batch_size
        self.max_concurrent = config.llm_max_concurrent

    async def prep_async(self, shared: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        为每个文件准备独立的上下文参数

        Data Access:
        - Read: shared.vectorstore_index, shared.local_path
        """
        # 根据是否有向量化阶段来确定当前是第几阶段
        logger.info("=" * 60)
        if shared.get("current_stage") == "vectorization":
            logger.info("📋 阶段 4/4: 代码分析 (CodeParsingBatchNode)")
        else:
            logger.info("📋 阶段 3/3: 代码分析 (CodeParsingBatchNode)")

        shared["current_stage"] = "code_analysis"

        local_path = shared.get("local_path")
        vectorstore_index = shared.get("vectorstore_index")

        if not local_path:
            logger.error("❌ 代码分析需要提供本地仓库路径")
            raise LLMParsingError("Local path is required")

        local_path = Path(local_path)
        logger.info(f"🔍 扫描源码文件: {local_path}")

        # 收集所有需要解析的代码文件
        file_items = []
        supported_extensions = {
            ".py",
            ".js",
            ".ts",
            ".java",
            ".cpp",
            ".c",
            ".h",
            ".hpp",
            ".cs",
            ".go",
            ".rs",
            ".php",
            ".rb",
            ".swift",
            ".kt",
            ".scala",
            ".ipynb",
        }

        ignore_dirs = {".git", "__pycache__", "node_modules", ".venv", "venv", "env"}

        for file_path in local_path.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                # 跳过忽略的目录
                if any(ignore_dir in file_path.parts for ignore_dir in ignore_dirs):
                    continue

                try:
                    if file_path.suffix.lower() == ".ipynb":
                        content = self._extract_notebook_content(file_path)
                        if not content:
                            continue
                    else:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()

                    # 跳过空文件或过大的文件
                    # if len(content.strip()) == 0 or len(content) > 50000:
                    #     continue

                    # 确定语言
                    language_map = {
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
                        ".ipynb": "jupyter",
                    }
                    language = language_map.get(file_path.suffix.lower(), "text")

                    file_items.append(
                        {
                            "file_path": str(file_path.relative_to(local_path)),
                            "content": content,
                            "language": language,
                            "full_path": str(file_path),
                            "vectorstore_index": vectorstore_index,
                        }
                    )

                except Exception as e:
                    logger.warning(f"Failed to read file {file_path}: {str(e)}")
                    continue

        logger.info(f"准备解析 {len(file_items)} 个文件")

        # 初始化实时写入的 markdown 文件
        await self._initialize_analysis_file(shared)

        # 添加进度回调和索引信息
        progress_callback = shared.get("progress_callback")
        for i, file_item in enumerate(file_items):
            file_item["progress_callback"] = progress_callback
            file_item["current_index"] = i
            # 添加共享数据引用，用于实时写入
            file_item["shared"] = shared

        return file_items

    async def exec_async(self, file_item: Dict[str, Any]) -> Dict[str, Any]:
        """
        使用 RAG API 获取上下文，然后调用 LLM 分析文件内容，生成详细的技术文档
        """
        try:
            # 1. 使用 RAG API 获取相关上下文
            context = await self._get_rag_context(file_item)

            # 2. 调用 LLM 进行详细分析，生成类似 res.md 格式的内容
            result = await self.llm_parser.parse_code_file_detailed(
                file_item["file_path"], file_item["content"], file_item["language"], context
            )

            # 3. 立即写入分析结果到 markdown 文件
            if not result.get("error"):
                await self._append_analysis_to_file(result, file_item.get("shared", {}))

            # 4. 调用进度回调（如果存在）
            progress_callback = file_item.get("progress_callback")
            if progress_callback:
                # 使用递增模式，不传入completed参数，让回调函数自己计数
                current_file = file_item["file_path"]
                try:
                    progress_callback(current_file=current_file)
                except Exception as e:
                    logger.warning(f"Progress callback failed: {str(e)}")

            return result

        except Exception as e:
            logger.error(f"Failed to parse file {file_item['file_path']}: {str(e)}")
            # 返回空结果而不是抛出异常，保持批处理继续
            return {"file_path": file_item["file_path"], "analysis_items": [], "error": str(e)}

    async def _get_rag_context(self, file_item: Dict[str, Any]) -> str:
        """
        使用 RAG API 获取与当前文件相关的上下文信息
        简化版：按类、方法或整个文件进行检索，不重新排序，直接通过RAG LLM增强
        """
        try:
            # 检查是否有向量存储索引
            vectorstore_index = file_item.get("vectorstore_index")
            if not vectorstore_index:
                logger.warning("RAG API 索引不可用")
                return ""

            file_path = file_item["file_path"]
            content = file_item["content"]
            language = file_item["language"]

            # 1. 提取类-方法关联关系和独立函数
            class_method_relationships = self._extract_class_method_relationships(content, language)
            independent_functions = self._extract_independent_functions(content, language, class_method_relationships)

            logger.info(f"🔍 从 {file_path} 文件中提取到:")
            logger.info(f"   - 类: {list(class_method_relationships.keys())}")
            logger.info(f"   - 独立函数: {independent_functions}")

            # 2. 构建细粒度检索策略：文件 + 每个类 + 每个独立函数
            search_queries = []
            search_targets = []  # 用于记录检索目标

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
            logger.info(f"🔍 开始为 {file_path} 检索相关上下文，共 {total_searches} 个查询:")
            logger.info(f"   - 文件检索: 1次")
            logger.info(f"   - 类检索: {len(class_method_relationships)}次")
            logger.info(f"   - 独立函数检索: {len(independent_functions)}次")

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
                                    "search_target": target,  # 添加检索目标信息
                                }
                            )
                            found_count += 1

                    logger.info(f"       找到 {found_count} 个相关结果")

                except Exception as e:
                    logger.warning(f"   [{i}/{total_searches}] 检索失败 {target}: {str(e)}")
                    continue

            # 4. 简单去重（基于内容）
            seen_content = set()
            unique_results = []
            for result in all_results:
                content_hash = hash(result["content"])
                if content_hash not in seen_content:
                    seen_content.add(content_hash)
                    unique_results.append(result)

            # 5. 直接组合所有检索结果，按检索目标分组显示
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
                logger.info(
                    f"✅ 为 {file_path} 检索到 {len(unique_results)} 个相关上下文，分布在 {len(target_groups)} 个检索目标中"
                )
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

    async def _initialize_analysis_file(self, shared: Dict[str, Any]):
        """初始化实时分析文件（markdown 和 JSON）"""
        try:
            # 获取仓库信息
            repo_info = shared.get("repo_info", {})
            repo_name = repo_info.get("name", "unknown")

            # 创建仓库专用的结果目录: data/results/仓库名/
            repo_results_dir = Path("./data/results") / repo_name
            repo_results_dir.mkdir(parents=True, exist_ok=True)

            # 生成分析报告文件名
            doc_path = repo_results_dir / "analysis_report.md"
            json_path = repo_results_dir / "analysis_report.json"

            # 初始化 markdown 文件（清空或创建）
            with open(doc_path, "w", encoding="utf-8") as f:
                f.write("# 代码分析报告\n\n")
                f.write(f"仓库: {repo_name}\n")
                f.write(f"分析时间: {self._get_current_time()}\n\n")
                f.write("---\n\n")

            # 初始化 JSON 文件
            import json

            initial_json_data = {
                "repository": {"name": repo_name, "info": repo_info, "analysis_time": self._get_current_time()},
                "files": [],
                "statistics": {"total_files": 0, "total_functions": 0, "total_classes": 0, "total_snippets": 0},
            }

            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(initial_json_data, f, ensure_ascii=False, indent=2)

            # 保存文件路径到共享数据
            shared["analysis_report_path"] = str(doc_path)
            shared["analysis_json_path"] = str(json_path)
            logger.info(f"📄 初始化分析报告文件: {doc_path}")
            logger.info(f"📄 初始化 JSON 数据文件: {json_path}")

        except Exception as e:
            logger.error(f"❌ 初始化分析文件失败: {str(e)}")

    async def _append_analysis_to_file(self, result: Dict[str, Any], shared: Dict[str, Any]):
        """将单个文件的分析结果追加到 markdown 和 JSON 文件"""
        try:
            analysis_file_path = shared.get("analysis_report_path")
            json_file_path = shared.get("analysis_json_path")

            if not analysis_file_path or not json_file_path:
                logger.warning("分析报告文件路径未找到，跳过写入")
                return

            file_path = result["file_path"]
            items = result.get("analysis_items", [])

            if not items:
                return

            # 为每个分析项添加文件路径字段和检索目标信息
            enhanced_items = []
            for item in items:
                enhanced_item = item.copy()
                enhanced_item["file_path"] = file_path  # 添加文件路径字段

                # 尝试从分析项中提取检索目标信息
                title = item.get("title", "")
                source = item.get("source", "")

                # 根据分析项的特征推断检索目标类型
                search_target = self._infer_search_target(title, source, file_path)
                enhanced_item["search_target"] = search_target

                enhanced_items.append(enhanced_item)

            # 1. 写入到 markdown 文件
            await self._append_to_markdown(file_path, enhanced_items, analysis_file_path, shared)

            # 2. 写入到 JSON 文件
            await self._append_to_json(file_path, enhanced_items, json_file_path, result)

            logger.info(f"✅ 已将 {file_path} 的分析结果写入 markdown 和 JSON 文件")

        except Exception as e:
            logger.error(f"❌ 追加分析结果到文件失败: {str(e)}")

    def _infer_search_target(self, title: str, source: str, file_path: str) -> str:
        """根据分析项的特征推断检索目标类型"""
        title_lower = title.lower()

        # 检查是否是类
        if "class" in title_lower or "类" in title:
            # 尝试提取类名
            import re

            class_match = re.search(r"class\s+([A-Za-z_][A-Za-z0-9_]*)", title, re.IGNORECASE)
            if class_match:
                class_name = class_match.group(1)
                return f"文件-类({class_name})"
            else:
                return f"文件-类(未知)"

        # 检查是否是函数/方法
        elif any(keyword in title_lower for keyword in ["function", "method", "def", "函数", "方法"]):
            # 尝试提取函数名
            import re

            func_patterns = [
                r"def\s+([A-Za-z_][A-Za-z0-9_]*)",
                r"function\s+([A-Za-z_][A-Za-z0-9_]*)",
                r"([A-Za-z_][A-Za-z0-9_]*)\s*\(",
                r"方法\s*([A-Za-z_][A-Za-z0-9_]*)",
                r"函数\s*([A-Za-z_][A-Za-z0-9_]*)",
            ]

            for pattern in func_patterns:
                func_match = re.search(pattern, title, re.IGNORECASE)
                if func_match:
                    func_name = func_match.group(1)
                    return f"文件-函数({func_name})"

            return f"文件-函数(未知)"

        # 默认为文件级别
        return f"文件-{file_path}"

    async def _append_to_markdown(
        self, file_path: str, items: List[Dict[str, Any]], markdown_path: str, shared: Dict[str, Any]
    ):
        """追加分析结果到 markdown 文件，按检索目标分组"""
        try:
            # 按检索目标分组
            target_groups = {}
            for item in items:
                target = item.get("search_target", f"文件-{file_path}")
                if target not in target_groups:
                    target_groups[target] = []
                target_groups[target].append(item)

            # 追加写入到 markdown 文件
            with open(markdown_path, "a", encoding="utf-8") as f:
                f.write(f"## 文件: {file_path}\n\n")

                # 按检索目标分组显示
                for target, target_items in target_groups.items():
                    f.write(f"### 检索目标: {target}\n\n")

                    for item in target_items:
                        title = item.get("title", "Unknown")
                        description = item.get("description", "No description")
                        source = item.get("source", "Unknown source")
                        language = item.get("language", "unknown")
                        code = item.get("code", "")

                        # 构建 SOURCE 链接（如果有仓库URL）
                        repo_url = shared.get("repo_url", "")
                        if repo_url and source:
                            # 从 source 中提取文件路径和行号
                            if ":" in source:
                                file_part, line_part = source.split(":", 1)
                                if "-" in line_part:
                                    start_line, end_line = line_part.split("-", 1)
                                    source_url = f"{repo_url}/blob/main/{file_part}#L{start_line}-L{end_line}"
                                else:
                                    source_url = f"{repo_url}/blob/main/{file_part}#L{line_part}"
                            else:
                                source_url = f"{repo_url}/blob/main/{source}"
                        else:
                            source_url = source

                        # 按照 res.md 的精确格式生成条目
                        item_content = f"""TITLE: {title}
DESCRIPTION: {description}
SOURCE: {source_url}
SEARCH_TARGET: {target}

LANGUAGE: {language}
CODE:
```
{code}
```

----------------------------------------

"""
                        f.write(item_content)

                    f.write("\n")  # 每个检索目标后添加空行

                f.write("\n")  # 文件结束后添加空行

        except Exception as e:
            logger.error(f"❌ 写入 markdown 文件失败: {str(e)}")

    async def _append_to_json(
        self, file_path: str, items: List[Dict[str, Any]], json_path: str, result: Dict[str, Any]
    ):
        """追加分析结果到 JSON 文件，包含检索目标信息"""
        try:
            import json

            # 读取现有的 JSON 数据
            with open(json_path, "r", encoding="utf-8") as f:
                json_data = json.load(f)

            # 按检索目标分组分析项
            target_groups = {}
            for item in items:
                target = item.get("search_target", f"文件-{file_path}")
                if target not in target_groups:
                    target_groups[target] = []
                target_groups[target].append(item)

            # 从分析项中推断文件语言（如果result中没有语言信息）
            file_language = result.get("language", "unknown")
            if file_language == "unknown" and items:
                # 尝试从第一个分析项中获取语言信息
                first_item_language = items[0].get("language", "unknown")
                if first_item_language != "unknown":
                    file_language = first_item_language

            # 构建文件分析数据
            file_data = {
                "file_path": file_path,
                "language": file_language,
                "analysis_items": items,  # 保留原始分析项
                "analysis_items_by_target": target_groups,  # 按检索目标分组的分析项
                "search_targets": list(target_groups.keys()),  # 检索目标列表
                "functions": result.get("functions", []),
                "classes": result.get("classes", []),
                "code_snippets": result.get("code_snippets", []),
                "analysis_timestamp": self._get_current_time(),
                "target_statistics": {
                    "total_targets": len(target_groups),
                    "targets_detail": {target: len(target_items) for target, target_items in target_groups.items()},
                },
            }

            # 添加到文件列表
            json_data["files"].append(file_data)

            # 更新统计信息
            json_data["statistics"]["total_files"] = len(json_data["files"])
            json_data["statistics"]["total_functions"] += len(result.get("functions", []))
            json_data["statistics"]["total_classes"] += len(result.get("classes", []))
            json_data["statistics"]["total_snippets"] += len(items)

            # 更新检索目标统计
            if "search_targets" not in json_data["statistics"]:
                json_data["statistics"]["search_targets"] = {}

            for target in target_groups.keys():
                if target not in json_data["statistics"]["search_targets"]:
                    json_data["statistics"]["search_targets"][target] = 0
                json_data["statistics"]["search_targets"][target] += len(target_groups[target])

            # 写回 JSON 文件
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"❌ 写入 JSON 文件失败: {str(e)}")

    def _extract_function_names(self, content: str, language: str) -> List[str]:
        """提取文件中的函数名（用于没有类的情况）"""
        import re

        function_names = []

        if language == "python":
            # 提取 Python 函数名
            func_pattern = r"^def\s+([A-Za-z_][A-Za-z0-9_]*)"
            matches = re.findall(func_pattern, content, re.MULTILINE)
            function_names.extend(matches)
        elif language in ["javascript", "typescript"]:
            # 提取 JS/TS 函数名
            func_patterns = [
                r"function\s+([A-Za-z_][A-Za-z0-9_]*)",
                r"const\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?:async\s+)?(?:function|\()",
                r"([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(?:async\s+)?function",
            ]
            for pattern in func_patterns:
                matches = re.findall(pattern, content)
                function_names.extend(matches)
        elif language == "java":
            # 提取 Java 方法名
            method_pattern = r"(?:public|private|protected)?\s*(?:static)?\s*\w+\s+([A-Za-z_][A-Za-z0-9_]*)\s*\("
            matches = re.findall(method_pattern, content)
            function_names.extend(matches)

        # 过滤常见的无意义函数名
        filtered_names = []
        common_words = {
            "main",
            "init",
            "test",
            "get",
            "set",
            "new",
            "create",
            "update",
            "delete",
            "__init__",
            "__str__",
            "__repr__",
        }

        for name in set(function_names):
            if len(name) > 2 and name.lower() not in common_words:
                filtered_names.append(name)

        return filtered_names[:10]  # 限制数量

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

    def _detect_language(self, file_extension: str) -> str:
        """
        根据文件扩展名检测编程语言
        """
        extension_map = {
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
            ".ipynb": "jupyter",  # Jupyter Notebook
        }
        return extension_map.get(file_extension.lower(), "unknown")

    async def exec_fallback_async(self, file_item: Dict[str, Any], exc: Exception) -> Dict[str, Any]:
        """
        若解析失败，尝试降级为仅提取函数签名或简单注释
        """
        logger.warning(f"Fallback parsing for {file_item['file_path']}: {str(exc)}")

        # 简单的降级策略：提取基本信息
        return {"file_path": file_item["file_path"], "functions": [], "classes": [], "error": f"Fallback: {str(exc)}"}

    async def post_async(
        self, shared: Dict[str, Any], prep_res: List[Dict[str, Any]], exec_res: List[Dict[str, Any]]
    ) -> str:
        """
        整理所有结果，更新 shared.code_analysis，完成实时分析报告

        Data Access:
        - Write: shared.code_analysis
        """
        # 过滤掉错误结果
        valid_results = [r for r in exec_res if not r.get("error")]
        error_count = len(exec_res) - len(valid_results)

        shared["code_analysis"] = valid_results

        # 统计信息
        total_functions = sum(len(r.get("functions", [])) for r in valid_results)
        total_classes = sum(len(r.get("classes", [])) for r in valid_results)
        total_snippets = sum(len(r.get("code_snippets", [])) for r in valid_results)

        logger.info(
            f"Code parsing completed: {len(valid_results)} files, "
            f"{total_functions} functions, {total_classes} classes, "
            f"{total_snippets} code snippets, {error_count} errors"
        )

        # 完成实时分析报告
        await self._finalize_analysis_report(shared, valid_results, error_count)

        return "default"

    async def _finalize_analysis_report(
        self, shared: Dict[str, Any], valid_results: List[Dict[str, Any]], error_count: int
    ):
        """完成实时分析报告，添加统计信息和备份（markdown 和 JSON）"""
        try:
            analysis_file_path = shared.get("analysis_report_path")
            json_file_path = shared.get("analysis_json_path")

            if not analysis_file_path or not json_file_path:
                logger.warning("分析报告文件路径未找到，跳过最终化")
                return

            # 统计信息
            total_functions = sum(len(r.get("functions", [])) for r in valid_results)
            total_classes = sum(len(r.get("classes", [])) for r in valid_results)
            total_snippets = sum(len(r.get("analysis_items", [])) for r in valid_results)

            # 1. 完成 markdown 文件
            with open(analysis_file_path, "a", encoding="utf-8") as f:
                f.write("\n---\n\n")
                f.write("## 分析统计\n\n")
                f.write(f"- 成功分析文件数: {len(valid_results)}\n")
                f.write(f"- 失败文件数: {error_count}\n")
                f.write(f"- 总函数数: {total_functions}\n")
                f.write(f"- 总类数: {total_classes}\n")
                f.write(f"- 总代码片段数: {total_snippets}\n")
                f.write(f"- 完成时间: {self._get_current_time()}\n")

            # 2. 完成 JSON 文件
            await self._finalize_json_report(json_file_path, valid_results, error_count)

            logger.info(f"📄 分析报告已完成: {analysis_file_path}")
            logger.info(f"📄 JSON 数据文件已完成: {json_file_path}")

            # 3. 创建带时间戳的备份版本
            repo_info = shared.get("repo_info", {})
            repo_name = repo_info.get("name", "unknown")
            repo_results_dir = Path("./data/results") / repo_name

            timestamp = self._get_current_time().replace(":", "-").replace(" ", "_")
            backup_md_path = repo_results_dir / f"analysis_report_{timestamp}.md"
            backup_json_path = repo_results_dir / f"analysis_report_{timestamp}.json"

            # 复制完整报告到备份文件
            import shutil

            shutil.copy2(analysis_file_path, backup_md_path)
            shutil.copy2(json_file_path, backup_json_path)

            logger.info(f"📄 备份分析报告已保存到: {backup_md_path}")
            logger.info(f"📄 备份 JSON 数据已保存到: {backup_json_path}")

            # 更新共享数据
            shared["analysis_backup_path"] = str(backup_md_path)
            shared["analysis_json_backup_path"] = str(backup_json_path)

        except Exception as e:
            logger.error(f"❌ 完成分析报告失败: {str(e)}")

    async def _finalize_json_report(self, json_path: str, valid_results: List[Dict[str, Any]], error_count: int):
        """完成 JSON 报告，添加最终统计信息"""
        try:
            import json

            # 读取现有的 JSON 数据
            with open(json_path, "r", encoding="utf-8") as f:
                json_data = json.load(f)

            # 更新最终统计信息
            json_data["statistics"]["error_count"] = error_count
            json_data["statistics"]["completion_time"] = self._get_current_time()

            # 添加分析摘要
            json_data["summary"] = {
                "total_files_processed": len(valid_results) + error_count,
                "successful_files": len(valid_results),
                "failed_files": error_count,
                "success_rate": (
                    f"{(len(valid_results) / (len(valid_results) + error_count) * 100):.1f}%"
                    if (len(valid_results) + error_count) > 0
                    else "0%"
                ),
            }

            # 写回 JSON 文件
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"❌ 完成 JSON 报告失败: {str(e)}")

    async def process_files_with_llm_parallel(self, file_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        使用 LLMParser 的并行处理功能来分析文件
        这是一个替代 AsyncParallelBatchNode 的高效方法

        Args:
            file_items: 文件项列表

        Returns:
            分析结果列表
        """
        logger.info(f"使用 LLM 并行处理 {len(file_items)} 个文件")
        logger.info(f"配置: 最大并发={self.max_concurrent}, 批次大小={self.batch_size}")

        # 为每个文件添加 RAG 上下文
        enhanced_file_items = []
        for file_item in file_items:
            # 获取 RAG 上下文
            context = await self._get_rag_context(file_item)

            # 创建增强的文件项
            enhanced_item = file_item.copy()
            enhanced_item["context"] = context
            enhanced_file_items.append(enhanced_item)

        # 使用 LLMParser 的分批并行处理
        results = await self.llm_parser.parse_files_in_batches(enhanced_file_items)

        return results

    def _get_current_time(self) -> str:
        """获取当前时间字符串"""
        from datetime import datetime

        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _extract_notebook_content(self, notebook_path: Path) -> str:
        """
        提取 Jupyter Notebook 文件中的代码内容

        Args:
            notebook_path: Notebook 文件路径

        Returns:
            提取的代码内容字符串
        """
        try:
            import json

            with open(notebook_path, "r", encoding="utf-8") as f:
                notebook = json.load(f)

            code_cells = []
            cell_index = 1

            # 遍历所有单元格
            for cell in notebook.get("cells", []):
                cell_type = cell.get("cell_type", "")

                if cell_type == "code":
                    # 代码单元格
                    source = cell.get("source", [])
                    if isinstance(source, list):
                        code_content = "".join(source)
                    else:
                        code_content = str(source)

                    # 跳过空的代码单元格
                    if code_content.strip():
                        code_cells.append(f"# Cell {cell_index}\n{code_content}\n")
                        cell_index += 1

                elif cell_type == "markdown":
                    # Markdown 单元格，作为注释包含
                    source = cell.get("source", [])
                    if isinstance(source, list):
                        markdown_content = "".join(source)
                    else:
                        markdown_content = str(source)

                    if markdown_content.strip():
                        # 将 Markdown 转换为 Python 注释
                        markdown_lines = markdown_content.split("\n")
                        commented_lines = [f"# {line}" if line.strip() else "#" for line in markdown_lines]
                        code_cells.append(f"# Markdown Cell {cell_index}\n" + "\n".join(commented_lines) + "\n")
                        cell_index += 1

            # 组合所有内容
            if code_cells:
                full_content = f"# Jupyter Notebook: {notebook_path.name}\n\n" + "\n".join(code_cells)
                return full_content
            else:
                return ""

        except Exception as e:
            logger.warning(f"Failed to extract notebook content from {notebook_path}: {str(e)}")
            return ""
