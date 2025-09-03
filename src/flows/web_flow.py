"""
Web 知识库创建流程
用于处理前端上传文件后的知识库创建操作
"""

import asyncio
import logging
from typing import Dict, Any, List
from pathlib import Path
from pocketflow import AsyncFlow

from ..nodes.web_vectorize_repo_node import WebVectorizeRepoNode
from ..nodes.rag_database_update_node import RAGDatabaseUpdateNode

from ..utils.llm_parser import LLMParser
from ..utils.config import get_config

# 设置logger
logger = logging.getLogger(__name__)


class WebKnowledgeBaseFlow(AsyncFlow):
    """Web 知识库创建流程"""

    def __init__(self):
        super().__init__()

        # 创建节点实例
        self.vectorize_node = WebVectorizeRepoNode()
        self.database_update_node = RAGDatabaseUpdateNode()

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

        # 添加进度显示延迟，让用户看到初始化过程
        logger.info("🔄 正在初始化知识库创建流程...")
        await asyncio.sleep(2)  # 2秒延迟

        logger.info("✅ 流程初始化完成")
        return shared

    async def post_async(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: str) -> Dict[str, Any]:
        """流程后处理"""
        logger.info("📋 阶段: 流程后处理 (WebKnowledgeBaseFlow.post_async)")

        # prep_res 和 exec_res 是 pocketflow 框架传递的参数，这里不需要使用
        # 我们通过 shared 状态来判断流程执行结果
        _ = prep_res, exec_res  # 避免未使用参数警告

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

        # 知识库创建完成后，将结果保存到数据库
        if shared.get("vectorstore_index") and shared.get("database_updated"):
            logger.info(f"✅ 知识库创建成功，索引: {shared.get('vectorstore_index')}")
            # 注意：task_index已经通过RAGDatabaseUpdateNode更新到数据库了
            # 这里不需要再次更新数据库
            shared["status"] = "knowledge_base_ready"  # 使用中间状态
        else:
            logger.error("❌ 知识库创建失败：缺少向量索引或数据库更新失败")
            shared["status"] = "failed"
            shared["error"] = "Knowledge base creation incomplete"

        # 返回完整的共享数据
        return shared

    except Exception as e:
        logger.error(f"Knowledge base creation failed for task {task_id}: {str(e)}")
        shared["status"] = "failed"
        shared["error"] = str(e)
        return shared


class WebAnalysisFlow(AsyncFlow):
    """Web 单文件分析流程"""

    def __init__(self):
        super().__init__()

        # 导入必要的模块

        # 初始化LLM解析器（自动从配置获取参数）
        self.llm_parser = LLMParser()

        # 获取API基础URL
        config = get_config()
        self.api_base_url = config.api_base_url

    async def prep_async(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """流程预处理"""
        logger.info("🚀 ========== 开始 Web 单文件分析流程 ==========")
        logger.info("📋 阶段: 流程初始化 (WebAnalysisFlow.prep_async)")

        # 验证必需的输入参数
        required_fields = ["task_id", "file_id", "vectorstore_index"]
        for field in required_fields:
            if field not in shared:
                logger.error(f"❌ 缺少必需参数: {field}")
                raise ValueError(f"Required field '{field}' is missing from shared data")

        task_id = shared.get("task_id")
        file_id = shared.get("file_id")
        vectorstore_index = shared.get("vectorstore_index")

        # 验证参数类型和值
        if not isinstance(task_id, int) or task_id <= 0:
            logger.error(f"❌ 任务ID无效: {task_id}")
            raise ValueError("Task ID must be a positive integer")

        if not isinstance(file_id, int) or file_id <= 0:
            logger.error(f"❌ 文件ID无效: {file_id}")
            raise ValueError("File ID must be a positive integer")

        if not vectorstore_index or not isinstance(vectorstore_index, str):
            logger.error(f"❌ 向量索引无效: {vectorstore_index}")
            raise ValueError("Vectorstore index must be a valid string")

        logger.info(f"🎯 任务ID: {task_id}")
        logger.info(f"📄 文件ID: {file_id}")
        logger.info(f"📂 向量索引: {vectorstore_index}")

        # 初始化共享状态
        shared.setdefault("status", "processing")
        shared["current_stage"] = "initialization"

        logger.info("✅ 流程初始化完成")
        return shared

    async def run_async(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """执行单文件分析流程"""
        try:
            # 1. 预处理
            await self.prep_async(shared)

            # 2. 获取文件信息
            file_info = await self._get_file_info(shared["file_id"], shared["task_id"])
            if not file_info:
                shared["status"] = "failed"
                shared["error"] = "无法获取文件信息"
                return shared

            # 3. 执行分析
            analysis_results = await self._analyze_file(file_info, shared["vectorstore_index"])

            # 4. 保存分析结果
            await self._save_analysis_results(analysis_results, shared["task_id"])

            # 5. 设置完成状态和分析项数量
            detailed_analysis = analysis_results.get("detailed_analysis", [])
            analysis_items_count = 1 + len(detailed_analysis)  # 1个全局分析 + 详细分析项
            shared["status"] = "completed"
            shared["analysis_items_count"] = analysis_items_count

            # 6. 后处理
            await self.post_async(shared, {}, "")

            return shared

        except Exception as e:
            logger.error(f"❌ 单文件分析流程失败: {str(e)}")
            shared["status"] = "failed"
            shared["error"] = str(e)
            return shared

    async def post_async(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: str) -> Dict[str, Any]:
        """流程后处理"""
        logger.info("📋 阶段: 流程后处理 (WebAnalysisFlow.post_async)")

        # 避免未使用参数警告
        _ = prep_res, exec_res

        if shared.get("status") == "completed":
            logger.info(f"✅ 单文件分析流程完成")
        else:
            logger.error("❌ 单文件分析流程失败")

        logger.info("🏁 ========== Web 单文件分析流程结束 ==========")
        return shared

    async def _get_file_info(self, file_id: int, task_id: int) -> Dict[str, Any]:
        """通过 GET /api/repository/file-analysis/{file_id} 接口获取文件信息"""
        import aiohttp

        try:
            url = f"{self.api_base_url}/api/repository/file-analysis/{file_id}"
            params = {"task_id": task_id}

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("status") == "success":
                            file_analysis = data.get("file_analysis", {})
                            logger.info(f"✅ 成功获取文件信息: {file_analysis.get('file_path', 'unknown')}")
                            return file_analysis

                    logger.error(f"❌ 获取文件信息失败: HTTP {response.status}")
                    return {}

        except Exception as e:
            logger.error(f"❌ 获取文件信息时发生错误: {str(e)}")
            return {}

    async def _analyze_file(self, file_info: Dict[str, Any], vectorstore_index: str) -> Dict[str, Any]:
        """分析文件内容，生成全局分析和类/函数分析"""
        try:
            file_path = file_info.get("file_path", "")
            code_content = file_info.get("code_content", "")
            language = file_info.get("language", "")

            if not code_content:
                logger.warning(f"文件 {file_path} 没有代码内容")
                return {
                    "file_path": file_path,
                    "global_analysis": {},
                    "detailed_analysis": [],
                    "error": "文件没有代码内容",
                }

            logger.info(f"🔍 开始分析文件: {file_path}")

            # 1. 获取RAG上下文
            context = await self._get_rag_context(file_path, code_content, language, vectorstore_index)

            # 2. 进行全局分析
            global_analysis = await self._perform_global_analysis(file_path, code_content, language, context)

            # 3. 进行详细分析（类和函数）
            detailed_analysis = await self._perform_detailed_analysis(file_path, code_content, language, context)

            logger.info(f"✅ 完成文件分析: {file_path}")
            logger.info(f"   - 全局分析: {global_analysis.get('title', 'N/A')}")
            logger.info(f"   - 详细分析项: {len(detailed_analysis)}")

            return {
                "file_path": file_path,
                "file_id": file_info.get("id"),  # 添加 file_id
                "language": language,
                "code_content": code_content,  # 添加 code_content
                "global_analysis": global_analysis,
                "detailed_analysis": detailed_analysis,
            }

        except Exception as e:
            logger.error(f"❌ 分析文件失败: {str(e)}")
            return {
                "file_path": file_info.get("file_path", ""),
                "global_analysis": {},
                "detailed_analysis": [],
                "error": str(e),
            }

    async def _get_rag_context(self, file_path: str, content: str, language: str, vectorstore_index: str) -> str:
        """获取RAG上下文信息，参考 CodeParsingBatchNode 的实现"""
        try:
            from ..utils.rag_api_client import RAGAPIClient
            from ..utils.config import get_config

            # 避免未使用参数警告
            _ = content

            config = get_config()
            rag_client = RAGAPIClient(config.rag_base_url)

            # 构建多个查询策略，参考 CodeParsingBatchNode
            search_queries = []
            search_targets = []

            # 1. 对文件本身进行检索
            search_queries.append(f"{file_path} {language} 文件")
            search_targets.append(f"文件-{file_path}")

            # 2. 对语言特定的检索
            search_queries.append(f"{language} 代码分析")
            search_targets.append(f"语言-{language}")

            logger.info(f"🔍 开始为 {file_path} 检索相关上下文，共 {len(search_queries)} 个查询")

            # 3. 执行检索，收集所有结果
            all_results = []
            for i, (query, target) in enumerate(zip(search_queries, search_targets), 1):
                try:
                    logger.info(f"   [{i}/{len(search_queries)}] 检索 {target}: {query}")
                    # 使用正确的方法名 search_knowledge
                    results = rag_client.search_knowledge(query=query, index_name=vectorstore_index, top_k=5)

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
                                    "category": doc.get("category", ""),
                                    "language": doc.get("language", ""),
                                    "query": query,
                                    "search_target": target,
                                }
                            )
                            found_count += 1

                    logger.info(f"       找到 {found_count} 个相关结果")

                except Exception as e:
                    logger.warning(f"   [{i}/{len(search_queries)}] 检索失败 {target}: {str(e)}")
                    continue

            # 4. 组合检索结果
            if all_results:
                context_parts = ["=== RAG 检索上下文 ==="]

                # 按检索目标分组
                target_groups = {}
                for result in all_results[:10]:  # 限制最多10个结果
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
                        file_info = result.get("file_path", "")
                        category = result.get("category", "")

                        # 截取合适长度
                        snippet = content_snippet[:300] + "..." if len(content_snippet) > 300 else content_snippet

                        context_parts.append(f"  {i}. {title} ({category})")
                        if file_info:
                            context_parts.append(f"     文件: {file_info}")
                        context_parts.append(f"     {snippet}\n")

                context = "\n".join(context_parts)
                logger.info(
                    f"✅ 为 {file_path} 检索到 {len(all_results)} 个相关上下文，分布在 {len(target_groups)} 个检索目标中"
                )
                return context
            else:
                logger.info(f"⚠️ 未找到 {file_path} 的相关上下文")
                return ""

        except Exception as e:
            logger.warning(f"⚠️ 获取RAG上下文失败: {str(e)}")
            return ""

    async def _perform_global_analysis(
        self, file_path: str, code_content: str, language: str, context: str
    ) -> Dict[str, Any]:
        """对完整代码内容进行全局分析"""
        try:
            # 构建全局分析的prompt
            prompt = f"""
请对以下{language}代码文件进行全局分析，生成文件级别的标题和描述。

文件路径: {file_path}
编程语言: {language}

上下文信息:
{context}

代码内容:
```{language}
{code_content}
```

请按照以下JSON格式返回全局分析结果：

{{
    "title": "文件的简洁标题（如：用户管理模块 或 数据库连接工具）",
    "description": "详细的文件功能描述，包括主要用途、核心功能、设计目标等（3-5句专业描述）"
}}

分析要求：
1. TITLE: 简洁明确，体现文件的主要功能或用途
2. DESCRIPTION: 详细专业的描述，包括：
   - 文件的主要功能和用途
   - 核心业务逻辑或技术实现
   - 在整个项目中的作用
   - 主要的类和函数概述

只返回JSON格式的结果，不要其他内容。
"""

            # 调用LLM API
            response = await self.llm_parser._make_api_request(prompt)

            # 解析响应
            import json

            clean_response = response.strip()
            if clean_response.startswith("```json"):
                clean_response = clean_response[7:]
            if clean_response.endswith("```"):
                clean_response = clean_response[:-3]
            clean_response = clean_response.strip()

            result = json.loads(clean_response)

            logger.info(f"✅ 完成全局分析: {result.get('title', 'N/A')}")
            return result

        except Exception as e:
            logger.error(f"❌ 全局分析失败: {str(e)}")
            return {"title": f"{file_path} 文件", "description": "文件分析失败，无法生成描述"}

    async def _perform_detailed_analysis(
        self, file_path: str, code_content: str, language: str, context: str
    ) -> List[Dict[str, Any]]:
        """对代码中的完整类和独立函数进行详细分析"""
        try:
            # 解析代码结构，提取类和独立函数
            code_elements = self._parse_code_structure(code_content, language)

            analysis_items = []

            # 分析每个代码元素
            for element in code_elements:
                if element["type"] == "class":
                    # 分析完整的类（包含所有方法）
                    class_analysis = await self._analyze_complete_class(element, file_path, language, context)
                    if class_analysis:
                        analysis_items.append(class_analysis)

                elif element["type"] == "function":
                    # 分析独立函数
                    function_analysis = await self._analyze_independent_function(element, file_path, language, context)
                    if function_analysis:
                        analysis_items.append(function_analysis)

            logger.info(f"✅ 完成详细分析，生成 {len(analysis_items)} 个分析项")
            logger.info(
                f"   - 类: {len([item for item in analysis_items if 'class' in item.get('title', '').lower()])} 个"
            )
            logger.info(
                f"   - 独立函数: {len([item for item in analysis_items if 'function' in item.get('title', '').lower()])} 个"
            )

            return analysis_items

        except Exception as e:
            logger.error(f"❌ 详细分析失败: {str(e)}")
            return []

    def _parse_code_structure(self, code_content: str, language: str) -> List[Dict[str, Any]]:
        """解析代码结构，提取类和独立函数"""
        import ast
        import re

        elements = []

        if language.lower() == "python":
            try:
                tree = ast.parse(code_content)
                lines = code_content.split("\n")

                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        # 提取完整的类（包含所有方法）
                        start_line = node.lineno
                        end_line = self._find_class_end_line(node, lines)
                        class_code = "\n".join(lines[start_line - 1 : end_line])

                        elements.append(
                            {
                                "type": "class",
                                "name": node.name,
                                "start_line": start_line,
                                "end_line": end_line,
                                "code": class_code,
                                "methods": [method.name for method in node.body if isinstance(method, ast.FunctionDef)],
                            }
                        )

                    elif isinstance(node, ast.FunctionDef):
                        # 检查是否是独立函数（不在类中）
                        if self._is_independent_function(node, tree):
                            # 排除程序入口
                            if node.name != "__main__" and not self._is_main_guard_function(node, lines):
                                start_line = node.lineno
                                end_line = self._find_function_end_line(node, lines)
                                function_code = "\n".join(lines[start_line - 1 : end_line])

                                elements.append(
                                    {
                                        "type": "function",
                                        "name": node.name,
                                        "start_line": start_line,
                                        "end_line": end_line,
                                        "code": function_code,
                                    }
                                )

            except SyntaxError as e:
                logger.warning(f"⚠️ Python 代码解析失败: {str(e)}")
                # 如果AST解析失败，使用正则表达式作为备选方案
                elements = self._parse_with_regex(code_content, language)
        else:
            # 对于其他语言，使用正则表达式解析
            elements = self._parse_with_regex(code_content, language)

        logger.info(
            f"🔍 解析代码结构完成: 找到 {len([e for e in elements if e['type'] == 'class'])} 个类, {len([e for e in elements if e['type'] == 'function'])} 个独立函数"
        )
        return elements

    def _find_class_end_line(self, class_node, lines: List[str]) -> int:
        """找到类的结束行（包括所有方法）"""
        import ast

        # 使用AST节点信息找到类的真正结束位置
        if hasattr(class_node, "end_lineno") and class_node.end_lineno:
            return class_node.end_lineno

        # 如果没有end_lineno，使用启发式方法
        start_line = class_node.lineno
        class_indent = self._get_line_indent(lines[start_line - 1])

        # 从类定义的下一行开始查找
        for i in range(start_line, len(lines)):
            line = lines[i]
            if line.strip():  # 非空行
                current_indent = self._get_line_indent(line)
                # 如果遇到同级别或更低级别的代码（不是类的内容），则类结束
                if current_indent <= class_indent:
                    # 检查是否是新的类、函数或其他顶级定义
                    stripped = line.strip()
                    if (
                        stripped.startswith("class ")
                        or stripped.startswith("def ")
                        or stripped.startswith("if __name__")
                        or stripped.startswith("import ")
                        or stripped.startswith("from ")
                    ):
                        return i

        return len(lines)

    def _get_line_indent(self, line: str) -> int:
        """获取行的缩进级别"""
        indent = 0
        for char in line:
            if char == " ":
                indent += 1
            elif char == "\t":
                indent += 4  # 假设tab等于4个空格
            else:
                break
        return indent

    def _find_function_end_line(self, func_node, lines: List[str]) -> int:
        """找到函数的结束行"""
        # 简单实现：找到下一个同级别的定义或文件结束
        start_line = func_node.lineno
        for i in range(start_line, len(lines)):
            line = lines[i].strip()
            if line and not line.startswith(" ") and not line.startswith("\t") and not line.startswith("#"):
                if line.startswith("class ") or line.startswith("def ") or line.startswith("if __name__"):
                    return i
        return len(lines)

    def _is_independent_function(self, func_node, tree) -> bool:
        """检查函数是否是独立函数（不在类中）"""
        import ast

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for item in node.body:
                    if item is func_node:
                        return False
        return True

    def _is_main_guard_function(self, func_node, lines: List[str]) -> bool:
        """检查函数是否在 if __name__ == "__main__": 块中"""
        func_line = func_node.lineno - 1
        # 向上查找是否有 if __name__ == "__main__":
        for i in range(func_line - 1, -1, -1):
            line = lines[i].strip()
            if "if __name__" in line and "__main__" in line:
                return True
            elif line and not line.startswith(" ") and not line.startswith("\t") and not line.startswith("#"):
                break
        return False

    def _parse_with_regex(self, code_content: str, language: str) -> List[Dict[str, Any]]:
        """使用正则表达式解析代码结构（备选方案）"""
        import re

        elements = []
        lines = code_content.split("\n")

        if language.lower() == "python":
            # 匹配类定义
            class_pattern = r"^class\s+(\w+).*?:"
            for i, line in enumerate(lines):
                if re.match(class_pattern, line.strip()):
                    class_name = re.match(class_pattern, line.strip()).group(1)
                    start_line = i + 1
                    end_line = self._find_block_end_regex(lines, i)
                    class_code = "\n".join(lines[i:end_line])

                    elements.append(
                        {
                            "type": "class",
                            "name": class_name,
                            "start_line": start_line,
                            "end_line": end_line,
                            "code": class_code,
                            "methods": [],
                        }
                    )

            # 匹配独立函数定义
            func_pattern = r"^def\s+(\w+).*?:"
            for i, line in enumerate(lines):
                if re.match(func_pattern, line.strip()) and not self._is_in_class_regex(lines, i):
                    func_name = re.match(func_pattern, line.strip()).group(1)
                    if not self._is_main_guard_regex(lines, i):
                        start_line = i + 1
                        end_line = self._find_block_end_regex(lines, i)
                        func_code = "\n".join(lines[i:end_line])

                        elements.append(
                            {
                                "type": "function",
                                "name": func_name,
                                "start_line": start_line,
                                "end_line": end_line,
                                "code": func_code,
                            }
                        )

        return elements

    def _find_block_end_regex(self, lines: List[str], start_index: int) -> int:
        """使用正则表达式找到代码块的结束位置（改进版，支持类的完整结构）"""
        if start_index >= len(lines):
            return len(lines)

        # 获取起始行的缩进级别
        start_line = lines[start_index]
        start_indent = self._get_line_indent(start_line)

        # 从下一行开始查找
        for i in range(start_index + 1, len(lines)):
            line = lines[i]
            if line.strip():  # 非空行
                current_indent = self._get_line_indent(line)
                # 如果遇到同级别或更低级别的代码，则块结束
                if current_indent <= start_indent:
                    stripped = line.strip()
                    if (
                        stripped.startswith("class ")
                        or stripped.startswith("def ")
                        or stripped.startswith("if __name__")
                        or stripped.startswith("import ")
                        or stripped.startswith("from ")
                    ):
                        return i

        return len(lines)

    def _is_in_class_regex(self, lines: List[str], func_index: int) -> bool:
        """检查函数是否在类中"""
        # 向上查找最近的类定义
        for i in range(func_index - 1, -1, -1):
            line = lines[i].strip()
            if line.startswith("class "):
                return True
            elif line and not line.startswith(" ") and not line.startswith("\t") and not line.startswith("#"):
                if line.startswith("def ") or line.startswith("if __name__"):
                    break
        return False

    def _is_main_guard_regex(self, lines: List[str], func_index: int) -> bool:
        """检查函数是否在 if __name__ == "__main__": 块中"""
        for i in range(func_index - 1, -1, -1):
            line = lines[i].strip()
            if "if __name__" in line and "__main__" in line:
                return True
            elif line and not line.startswith(" ") and not line.startswith("\t") and not line.startswith("#"):
                break
        return False

    async def _analyze_complete_class(
        self, class_element: Dict[str, Any], file_path: str, language: str, context: str
    ) -> Dict[str, Any]:
        """分析完整的类（包含所有方法）"""
        try:
            class_name = class_element["name"]
            class_code = class_element["code"]
            methods = class_element.get("methods", [])

            # 构建分析提示
            prompt = f"""
请对以下{language}类进行完整分析，生成类级别的标题和描述。

类名: {class_name}
文件路径: {file_path}
包含方法: {', '.join(methods) if methods else '无'}

上下文信息:
{context}

类代码:
```{language}
{class_code}
```

请按照以下JSON格式返回分析结果：

{{
    "title": "类的简洁标题（如：UserService类 或 数据处理器类）",
    "description": "详细的类功能描述，包括类的用途、主要方法、设计模式等（3-5句专业描述）"
}}

分析要求：
1. TITLE: 简洁明确，体现类的主要功能
2. DESCRIPTION: 详细描述类的功能、包含的主要方法、在系统中的作用

只返回JSON格式的结果，不要其他内容。
"""

            # 调用LLM API
            response = await self.llm_parser._make_api_request(prompt)

            # 解析响应
            import json

            clean_response = response.strip()
            if clean_response.startswith("```json"):
                clean_response = clean_response[7:]
            if clean_response.endswith("```"):
                clean_response = clean_response[:-3]
            clean_response = clean_response.strip()

            result = json.loads(clean_response)

            # 添加额外信息
            result.update(
                {
                    "source": f"{file_path}:{class_element['start_line']}-{class_element['end_line']}",
                    "code": class_code,
                    "start_line": class_element["start_line"],
                    "end_line": class_element["end_line"],
                    "original_name": class_element["name"],  # 添加原始类名
                    "element_type": "class",  # 添加元素类型
                }
            )

            logger.info(f"✅ 完成类分析: {result.get('title', 'N/A')}")
            return result

        except Exception as e:
            logger.error(f"❌ 类分析失败: {str(e)}")
            return {
                "title": f"{class_element['name']}类",
                "description": "类分析失败，无法生成描述",
                "source": f"{file_path}:{class_element['start_line']}-{class_element['end_line']}",
                "code": class_element["code"],
                "start_line": class_element["start_line"],
                "end_line": class_element["end_line"],
            }

    async def _analyze_independent_function(
        self, func_element: Dict[str, Any], file_path: str, language: str, context: str
    ) -> Dict[str, Any]:
        """分析独立函数"""
        try:
            func_name = func_element["name"]
            func_code = func_element["code"]

            # 构建分析提示
            prompt = f"""
请对以下{language}独立函数进行分析，生成函数级别的标题和描述。

函数名: {func_name}
文件路径: {file_path}

上下文信息:
{context}

函数代码:
```{language}
{func_code}
```

请按照以下JSON格式返回分析结果：

{{
    "title": "函数的简洁标题（如：数据预处理函数 或 用户验证方法）",
    "description": "详细的函数功能描述，包括参数、返回值、主要逻辑等（2-4句专业描述）"
}}

分析要求：
1. TITLE: 简洁明确，体现函数的主要功能
2. DESCRIPTION: 详细描述函数的功能、参数、返回值、主要逻辑

只返回JSON格式的结果，不要其他内容。
"""

            # 调用LLM API
            response = await self.llm_parser._make_api_request(prompt)

            # 解析响应
            import json

            clean_response = response.strip()
            if clean_response.startswith("```json"):
                clean_response = clean_response[7:]
            if clean_response.endswith("```"):
                clean_response = clean_response[:-3]
            clean_response = clean_response.strip()

            result = json.loads(clean_response)

            # 添加额外信息
            result.update(
                {
                    "source": f"{file_path}:{func_element['start_line']}-{func_element['end_line']}",
                    "code": func_code,
                    "start_line": func_element["start_line"],
                    "end_line": func_element["end_line"],
                    "original_name": func_element["name"],  # 添加原始函数名
                    "element_type": "function",  # 添加元素类型
                }
            )

            logger.info(f"✅ 完成函数分析: {result.get('title', 'N/A')}")
            return result

        except Exception as e:
            logger.error(f"❌ 函数分析失败: {str(e)}")
            return {
                "title": f"{func_element['name']}函数",
                "description": "函数分析失败，无法生成描述",
                "source": f"{file_path}:{func_element['start_line']}-{func_element['end_line']}",
                "code": func_element["code"],
                "start_line": func_element["start_line"],
                "end_line": func_element["end_line"],
            }

    async def _save_analysis_results(self, analysis_results: Dict[str, Any], task_id: int):
        """通过 POST /api/repository/analysis-items 接口保存分析结果，并更新 file_analyses 表"""
        import aiohttp

        try:
            file_path = analysis_results.get("file_path", "")
            language = analysis_results.get("language", "")
            global_analysis = analysis_results.get("global_analysis", {})
            detailed_analysis = analysis_results.get("detailed_analysis", [])

            # 首先需要获取 file_analysis_id（从 _get_file_info 获取的 file_id）
            file_analysis_id = analysis_results.get("file_id")
            if not file_analysis_id:
                logger.error(f"❌ 无法获取文件分析ID: {file_path}")
                return

            # 1. 保存全局分析结果（文件级别）
            if global_analysis:
                # 计算文件的总行数
                code_content = analysis_results.get("code_content", "")
                total_lines = len(code_content.split("\n")) if code_content else 0

                # 提取文件名作为 target_name
                import os

                file_name = os.path.basename(file_path)

                global_item_data = {
                    "file_analysis_id": file_analysis_id,
                    "title": global_analysis.get("title", ""),
                    "description": global_analysis.get("description", ""),
                    "target_type": "file",
                    "target_name": file_name,  # 文件名
                    "source": file_path,
                    "language": language,
                    "code": code_content,  # 完整的文件代码
                    "start_line": 1,  # 文件从第1行开始
                    "end_line": total_lines,  # 文件的最后一行
                }

                await self._post_analysis_item(global_item_data)
                logger.info(f"✅ 保存全局分析: {global_analysis.get('title', 'N/A')}")

            # 2. 保存详细分析结果（类和函数）
            for item in detailed_analysis:
                target_type = self._infer_target_type(item.get("title", ""))

                # 从分析结果中直接获取目标名称，或者从代码中提取
                target_name = self._get_target_name_from_analysis(item, target_type)

                # 确保代码片段完整
                code_snippet = item.get("code", "")
                if not code_snippet:
                    # 如果没有代码片段，尝试从文件中提取
                    code_snippet = self._extract_code_snippet(
                        analysis_results.get("code_content", ""), item.get("start_line"), item.get("end_line")
                    )

                detail_item_data = {
                    "file_analysis_id": file_analysis_id,
                    "title": item.get("title", ""),
                    "description": item.get("description", ""),
                    "target_type": target_type,
                    "target_name": target_name,  # 确保有目标名称
                    "source": item.get("source", file_path),
                    "language": language,
                    "code": code_snippet,  # 完整的代码片段
                    "start_line": item.get("start_line"),  # 如实填写起始行
                    "end_line": item.get("end_line"),  # 如实填写结束行
                }

                await self._post_analysis_item(detail_item_data)
                logger.info(f"✅ 保存详细分析: {item.get('title', 'N/A')}")

            # 3. 更新 file_analyses 表的状态和分析结果
            await self._update_file_analysis_status(file_analysis_id, detailed_analysis)

            logger.info(f"✅ 完成保存分析结果，共 {1 + len(detailed_analysis)} 项")

        except Exception as e:
            logger.error(f"❌ 保存分析结果失败: {str(e)}")
            raise

    async def _post_analysis_item(self, data: Dict[str, Any]):
        """调用 POST /api/repository/analysis-items 接口"""
        import aiohttp

        try:
            url = f"{self.api_base_url}/api/repository/analysis-items"

            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data) as response:
                    if response.status == 201:
                        result = await response.json()
                        if result.get("status") == "success":
                            return result

                    logger.error(f"❌ 保存分析项失败: HTTP {response.status}")
                    error_data = await response.json() if response.content_type == "application/json" else {}
                    logger.error(f"错误详情: {error_data}")

        except Exception as e:
            logger.error(f"❌ 调用分析项接口失败: {str(e)}")
            raise

    async def _update_file_analysis_status(self, file_id: int, detailed_analysis: List[Dict[str, Any]]):
        """使用 PUT /api/repository/file-analysis/{file_id} 接口更新文件分析状态"""
        import aiohttp

        try:
            # 统计分析项信息
            classes = []
            functions = []

            for item in detailed_analysis:
                # 优先使用原始名称，如果没有则从标题中提取
                original_name = item.get("original_name")
                element_type = item.get("element_type")

                if original_name and element_type:
                    # 使用准确的原始名称和类型
                    if element_type == "class":
                        classes.append(original_name)
                    elif element_type == "function":
                        functions.append(original_name)
                else:
                    # 回退到从标题中提取（兼容性）
                    target_type = self._infer_target_type(item.get("title", ""))
                    target_name = self._extract_target_name(item.get("title", ""), target_type)

                    if target_type == "class" and target_name:
                        classes.append(target_name)
                    elif target_type == "function" and target_name:
                        functions.append(target_name)

            # 构建 file_analysis 内容（不包含文件级别的分析项）
            total_items = len(detailed_analysis)  # 只统计类和函数的分析项

            if total_items == 0:
                analysis_summary = "文件包含 0 个分析项"
            else:
                # 构建具体的类名和函数名列表
                item_names = []

                # 添加类名
                for class_name in classes:
                    item_names.append(f"{class_name}类")

                # 添加函数名
                for func_name in functions:
                    item_names.append(f"{func_name}函数")

                # 构建摘要
                if item_names:
                    analysis_summary = f"文件包含 {total_items} 个分析项：{', '.join(item_names)}"
                else:
                    analysis_summary = f"文件包含 {total_items} 个分析项"

            # 准备更新数据
            update_data = {
                "status": "success",
                "file_analysis": analysis_summary,  # 直接使用摘要文本
            }

            # 调用 PUT 接口更新
            url = f"{self.api_base_url}/api/repository/file-analysis/{file_id}"

            async with aiohttp.ClientSession() as session:
                async with session.put(url, json=update_data) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get("status") == "success":
                            logger.info(f"✅ 更新文件分析状态成功: {analysis_summary}")
                            return result

                    logger.error(f"❌ 更新文件分析状态失败: HTTP {response.status}")
                    error_data = await response.json() if response.content_type == "application/json" else {}
                    logger.error(f"错误详情: {error_data}")

        except Exception as e:
            logger.error(f"❌ 更新文件分析状态失败: {str(e)}")
            raise

    def _infer_target_type(self, title: str) -> str:
        """从标题推断目标类型"""
        title_lower = title.lower()

        if "class" in title_lower or "类" in title:
            return "class"
        elif any(keyword in title_lower for keyword in ["function", "method", "def", "函数", "方法"]):
            return "function"
        else:
            return "file"

    def _extract_target_name(self, title: str, target_type: str) -> str:
        """从标题中提取目标名称（类名或函数名）"""
        import re

        if target_type == "class":
            # 尝试提取类名
            patterns = [
                r"class\s+([A-Za-z_][A-Za-z0-9_]*)",  # class ClassName
                r"([A-Za-z_][A-Za-z0-9_]*)\s*类",  # ClassName类
                r"类\s*([A-Za-z_][A-Za-z0-9_]*)",  # 类 ClassName
            ]
            for pattern in patterns:
                match = re.search(pattern, title, re.IGNORECASE)
                if match:
                    return match.group(1)

        elif target_type == "function":
            # 尝试提取函数名
            patterns = [
                r"def\s+([A-Za-z_][A-Za-z0-9_]*)",  # def function_name
                r"function\s+([A-Za-z_][A-Za-z0-9_]*)",  # function function_name
                r"([A-Za-z_][A-Za-z0-9_]*)\s*函数",  # function_name函数
                r"函数\s*([A-Za-z_][A-Za-z0-9_]*)",  # 函数 function_name
                r"方法\s*([A-Za-z_][A-Za-z0-9_]*)",  # 方法 method_name
                r"([A-Za-z_][A-Za-z0-9_]*)\s*方法",  # method_name方法
            ]
            for pattern in patterns:
                match = re.search(pattern, title, re.IGNORECASE)
                if match:
                    return match.group(1)

        # 如果无法提取，返回 None
        return None

    def _get_target_name_from_analysis(self, item: Dict[str, Any], target_type: str) -> str:
        """从分析结果中获取目标名称"""
        # 1. 首先尝试从分析结果中直接获取
        if "target_name" in item and item["target_name"]:
            return item["target_name"]

        # 2. 从标题中提取
        title = item.get("title", "")
        extracted_name = self._extract_target_name(title, target_type)
        if extracted_name:
            return extracted_name

        # 3. 从代码中提取（如果有的话）
        code = item.get("code", "")
        if code:
            if target_type == "class":
                # 从代码中提取类名
                import re

                class_match = re.search(r"class\s+([A-Za-z_][A-Za-z0-9_]*)", code)
                if class_match:
                    return class_match.group(1)
            elif target_type == "function":
                # 从代码中提取函数名
                import re

                func_match = re.search(r"def\s+([A-Za-z_][A-Za-z0-9_]*)", code)
                if func_match:
                    return func_match.group(1)

        # 4. 如果都无法提取，返回默认值
        if target_type == "class":
            return "UnknownClass"
        elif target_type == "function":
            return "UnknownFunction"
        else:
            return "Unknown"

    def _extract_code_snippet(self, full_code: str, start_line: int, end_line: int) -> str:
        """从完整代码中提取指定行范围的代码片段"""
        if not full_code or not start_line or not end_line:
            return ""

        try:
            lines = full_code.split("\n")
            # 转换为0基索引
            start_idx = max(0, start_line - 1)
            end_idx = min(len(lines), end_line)

            # 提取代码片段
            code_snippet = "\n".join(lines[start_idx:end_idx])
            return code_snippet

        except Exception as e:
            logger.warning(f"⚠️ 提取代码片段失败: {str(e)}")
            return ""


async def analyze_data_model(
    task_id: int, vectorstore_index: str, batch_size: int = None, progress_callback=None
) -> Dict[str, Any]:
    """
    分析数据模型的便捷函数 - 新版本：逐个文件分析

    Args:
        task_id: 任务ID
        vectorstore_index: 向量索引名称
        batch_size: 批处理大小（保留兼容性，但在新流程中不使用）
        progress_callback: 进度回调函数

    Returns:
        分析结果字典
    """
    import aiohttp
    from ..utils.config import get_config

    # 避免未使用参数警告
    _ = batch_size

    config = get_config()
    api_base_url = config.api_base_url

    logger.info("🏁 ========== 开始逐个文件分析数据模型流程 ==========")

    try:
        # 1. 先获取任务下的所有文件
        logger.info(f"📋 步骤 1: 获取任务 {task_id} 下的所有文件")

        async with aiohttp.ClientSession() as session:
            url = f"{api_base_url}/api/repository/files/{task_id}"
            params = {"include_code_content": "false"}  # 只获取文件列表，不需要内容

            async with session.get(url, params=params) as response:
                if response.status != 200:
                    error_msg = f"获取文件列表失败: HTTP {response.status}"
                    logger.error(error_msg)
                    return {"status": "failed", "error": error_msg, "task_id": task_id}

                data = await response.json()
                if data.get("status") != "success":
                    error_msg = f"获取文件列表失败: {data.get('message', '未知错误')}"
                    logger.error(error_msg)
                    return {"status": "failed", "error": error_msg, "task_id": task_id}

                files = data.get("files", [])

        if not files:
            logger.warning(f"任务 {task_id} 下没有找到文件")
            return {
                "status": "analysis_completed",
                "task_id": task_id,
                "analysis_items_count": 0,
                "message": "没有文件需要分析",
            }

        logger.info(f"📁 找到 {len(files)} 个文件需要分析")

        # 2. 逐个调用单文件分析接口
        total_files = len(files)
        successful_files = 0
        failed_files = 0
        total_analysis_items = 0
        analysis_results = []

        for i, file_info in enumerate(files, 1):
            file_id = file_info.get("id")
            file_path = file_info.get("file_path", "unknown")

            if not file_id:
                logger.warning(f"跳过无效文件: {file_path} (缺少ID)")
                failed_files += 1
                continue

            logger.info(f"📝 [{i}/{total_files}] 分析文件: {file_path} (ID: {file_id})")

            # 调用进度回调
            if progress_callback:
                try:
                    progress_callback(
                        current_file=file_path,
                        current_index=i,
                        total_files=total_files,
                        successful_files=successful_files,
                        failed_files=failed_files,
                    )
                except Exception as e:
                    logger.warning(f"Progress callback failed: {str(e)}")

            # 调用单文件分析接口
            try:
                async with aiohttp.ClientSession() as session:
                    url = f"{api_base_url}/api/analysis/file/{file_id}/analyze-data-model"
                    params = {"task_index": vectorstore_index, "task_id": task_id}

                    async with session.post(url, params=params) as response:
                        if response.status == 200:
                            result = await response.json()
                            if result.get("status") == "success":
                                successful_files += 1
                                items_count = result.get("analysis_items_count", 0)
                                total_analysis_items += items_count
                                analysis_results.append(
                                    {
                                        "file_id": file_id,
                                        "file_path": file_path,
                                        "status": "success",
                                        "analysis_items_count": items_count,
                                    }
                                )
                                logger.info(f"✅ [{i}/{total_files}] 分析成功: {file_path} ({items_count} 个分析项)")
                            else:
                                failed_files += 1
                                error_msg = result.get("message", "未知错误")
                                analysis_results.append(
                                    {"file_id": file_id, "file_path": file_path, "status": "failed", "error": error_msg}
                                )
                                logger.error(f"❌ [{i}/{total_files}] 分析失败: {file_path} - {error_msg}")
                        else:
                            failed_files += 1
                            error_data = await response.json() if response.content_type == "application/json" else {}
                            error_msg = error_data.get("message", f"HTTP {response.status}")
                            analysis_results.append(
                                {"file_id": file_id, "file_path": file_path, "status": "failed", "error": error_msg}
                            )
                            logger.error(f"❌ [{i}/{total_files}] 分析失败: {file_path} - {error_msg}")

            except Exception as e:
                failed_files += 1
                error_msg = str(e)
                analysis_results.append(
                    {"file_id": file_id, "file_path": file_path, "status": "failed", "error": error_msg}
                )
                logger.error(f"❌ [{i}/{total_files}] 分析异常: {file_path} - {error_msg}")

        # 3. 汇总结果
        success_rate = (successful_files / total_files * 100) if total_files > 0 else 0

        logger.info("🏁 ========== 逐个文件分析数据模型流程完成 ==========")
        logger.info(f"📊 分析统计:")
        logger.info(f"   - 总文件数: {total_files}")
        logger.info(f"   - 成功分析: {successful_files}")
        logger.info(f"   - 失败分析: {failed_files}")
        logger.info(f"   - 成功率: {success_rate:.1f}%")
        logger.info(f"   - 总分析项: {total_analysis_items}")

        return {
            "status": "analysis_completed",
            "task_id": task_id,
            "vectorstore_index": vectorstore_index,
            "total_files": total_files,
            "successful_files": successful_files,
            "failed_files": failed_files,
            "success_rate": f"{success_rate:.1f}%",
            "analysis_items_count": total_analysis_items,
            "analysis_results": analysis_results,
            "message": f"完成 {total_files} 个文件的分析，成功 {successful_files} 个，失败 {failed_files} 个",
        }

    except Exception as e:
        logger.error(f"逐个文件分析数据模型流程失败: {str(e)}")
        return {"status": "failed", "task_id": task_id, "error": str(e), "message": f"分析流程异常: {str(e)}"}


async def analyze_single_file_data_model(
    task_id: int, file_id: int, vectorstore_index: str, progress_callback=None
) -> Dict[str, Any]:
    """
    单文件分析数据模型的便捷函数

    Args:
        task_id: 任务ID
        file_id: 文件ID
        vectorstore_index: 向量索引名称
        progress_callback: 进度回调函数

    Returns:
        分析结果字典
    """
    # 准备共享数据
    shared = {"task_id": task_id, "file_id": file_id, "vectorstore_index": vectorstore_index, "status": "processing"}

    if progress_callback:
        shared["progress_callback"] = progress_callback

    # 创建并执行流程
    flow = WebAnalysisFlow()

    try:
        # 执行分析流程
        await flow.run_async(shared)

        # 返回完整的共享数据
        return shared

    except Exception as e:
        logger.error(f"Single file data model analysis failed for file {file_id}: {str(e)}")
        shared["status"] = "failed"
        shared["error"] = str(e)
        return shared
