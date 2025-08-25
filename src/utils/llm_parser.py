"""
LLM 解析器模块
封装 OpenAI API 调用逻辑，实现批量调用、缓存命中判断、prompt 统一模板
"""

import json
import asyncio
from typing import Dict, List, Any, Optional
from pathlib import Path
from openai import OpenAI

from .logger import logger
from .error_handler import LLMParsingError
from .config import get_config
from .prompt import CodeAnalysisPrompts


class LLMParser:
    """LLM 代码解析器"""

    def __init__(self):
        config = get_config()
        self.api_key = config.openai_api_key
        self.base_url = config.openai_base_url
        self.model = config.openai_model
        self.cache_dir = Path("./data/cache/llm")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        if not self.api_key:
            raise LLMParsingError("OpenAI API key not found in environment variables")

        # 初始化 OpenAI 客户端
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

        # 并行处理配置
        self.max_concurrent = config.llm_max_concurrent
        self.batch_size = config.llm_batch_size
        self.request_timeout = config.llm_request_timeout
        self.retry_delay = config.llm_retry_delay

        # 创建信号量来控制并发数
        self.semaphore = asyncio.Semaphore(self.max_concurrent)

    def _get_cache_key(self, file_path: str, prompt_type: str = "analysis") -> str:
        """生成缓存键（基于文件路径）"""
        # 将文件路径转换为安全的文件名
        safe_path = file_path.replace("/", "_").replace("\\", "_").replace(":", "_").replace(" ", "_").replace("-", "_")

        # 移除文件扩展名，添加prompt类型
        if "." in safe_path:
            safe_path = safe_path.rsplit(".", 1)[0]
        return f"{safe_path}_{prompt_type}"

    def _get_cache_path(self, cache_key: str) -> Path:
        """获取缓存文件路径"""
        return self.cache_dir / f"{cache_key}.json"

    def _load_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """从缓存加载结果"""
        cache_path = self._get_cache_path(cache_key)
        if cache_path.exists():
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load cache {cache_key}: {str(e)}")
        return None

    def _save_to_cache(self, cache_key: str, result: Dict[str, Any]):
        """保存结果到缓存"""
        cache_path = self._get_cache_path(cache_key)
        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save cache {cache_key}: {str(e)}")

    async def _make_api_request(self, prompt_or_messages, max_retries: int = 3) -> str:
        """发起API请求，使用 OpenAI 客户端，支持并发控制"""
        # 支持两种输入格式：字符串prompt或消息列表
        if isinstance(prompt_or_messages, str):
            messages = [{"role": "user", "content": prompt_or_messages}]
        else:
            messages = prompt_or_messages

        # 使用信号量控制并发数
        async with self.semaphore:
            for attempt in range(max_retries):
                try:
                    # 使用 OpenAI 客户端进行调用
                    response = self.client.chat.completions.create(
                        model=self.model, messages=messages, temperature=0.1, max_tokens=2000
                    )

                    return response.choices[0].message.content

                except Exception as e:
                    logger.warning(f"API request attempt {attempt + 1} failed: {str(e)}")
                    if attempt == max_retries - 1:
                        raise LLMParsingError(f"API request failed: {str(e)}")
                    await asyncio.sleep(self.retry_delay * (2**attempt))

            raise LLMParsingError("Max retries exceeded")

    async def parse_code_file_detailed(
        self, file_path: str, code_content: str, language: str, context: str = ""
    ) -> Dict[str, Any]:
        """
        详细解析代码文件，生成类似 res.md 格式的分析结果

        Args:
            file_path: 文件路径
            code_content: 代码内容
            language: 编程语言
            context: RAG 检索的上下文信息

        Returns:
            详细分析结果，包含 TITLE、DESCRIPTION、SOURCE、LANGUAGE、CODE 格式的分析项
        """
        try:
            # 使用详细分析的 prompt
            prompt = CodeAnalysisPrompts.get_detailed_analysis_prompt(code_content, file_path, language, context)

            # 调用 API
            response = await self._make_api_request(prompt)

            # 解析响应
            result = self._parse_detailed_response(response, file_path)

            return result

        except Exception as e:
            logger.error(f"Failed to parse file {file_path}: {str(e)}")
            return {"file_path": file_path, "analysis_items": [], "error": str(e)}

    async def parse_code_file(
        self, file_path: str, code_content: str, language: str, context: str = ""
    ) -> Dict[str, Any]:
        """
        解析单个代码文件

        Args:
            file_path: 文件路径
            code_content: 代码内容
            language: 编程语言
            context: 上下文信息（来自RAG检索）

        Returns:
            解析结果字典
        """
        # 检查缓存
        cache_key = self._get_cache_key(str(file_path), "analysis")
        cached_result = self._load_from_cache(cache_key)
        if cached_result:
            logger.info(f"Using cached result for {file_path}")
            return cached_result

        try:
            # 构建prompt
            prompt = CodeAnalysisPrompts.get_analysis_prompt(code_content, file_path, language, context)

            messages = [
                {"role": "system", "content": CodeAnalysisPrompts.get_system_message()},
                {"role": "user", "content": prompt},
            ]

            # 调用API
            logger.info(f"Analyzing code file: {file_path}")
            response = await self._make_api_request(messages)

            # 解析JSON响应
            try:
                # 清理响应，移除可能的markdown标记
                clean_response = response.strip()
                if clean_response.startswith("```json"):
                    clean_response = clean_response[7:]
                if clean_response.endswith("```"):
                    clean_response = clean_response[:-3]
                clean_response = clean_response.strip()

                result = json.loads(clean_response)

                # 验证结果格式
                if not isinstance(result, dict):
                    raise ValueError("Invalid response format: not a dictionary")

                # 确保必要的字段存在
                if "functions" not in result:
                    result["functions"] = []
                if "classes" not in result:
                    result["classes"] = []
                if "code_snippets" not in result:
                    result["code_snippets"] = []

                # 添加文件路径信息
                result["file_path"] = file_path

                # 保存到缓存
                self._save_to_cache(cache_key, result)

                logger.info(
                    f"Successfully analyzed {file_path}: {len(result['functions'])} functions, {len(result['classes'])} classes"
                )
                return result

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response for {file_path}: {str(e)}")
                logger.error(f"Response content: {response}")
                raise LLMParsingError(f"Invalid JSON response: {str(e)}")

        except Exception as e:
            logger.error(f"Failed to parse code file {file_path}: {str(e)}")
            raise LLMParsingError(f"Code parsing failed for {file_path}: {str(e)}")

    async def parse_code_batch(
        self, file_items: List[Dict[str, Any]], context_provider=None, batch_size: int = 5
    ) -> List[Dict[str, Any]]:
        """
        批量解析代码文件

        Args:
            file_items: 文件信息列表，每个包含file_path, content, language
            context_provider: 上下文提供者（RAG）
            batch_size: 批处理大小

        Returns:
            解析结果列表
        """
        results = []

        # 分批处理
        for i in range(0, len(file_items), batch_size):
            batch = file_items[i : i + batch_size]

            # 并行处理当前批次
            tasks = []
            for item in batch:
                # 获取上下文信息
                context = ""
                if context_provider:
                    try:
                        context_results = await context_provider.search_similar(
                            f"{item['file_path']} {item.get('language', '')}", k=3
                        )
                        context = "\n".join([r["content"][:200] for r in context_results])
                    except Exception as e:
                        logger.warning(f"Failed to get context for {item['file_path']}: {str(e)}")

                task = self.parse_code_file(item["file_path"], item["content"], item.get("language", "text"), context)
                tasks.append(task)

            # 等待当前批次完成
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Batch parsing error: {str(result)}")
                    # 添加空结果以保持索引一致性
                    results.append({"file_path": "error", "functions": [], "classes": []})
                else:
                    results.append(result)

            # 批次间延迟，避免API限流
            if i + batch_size < len(file_items):
                await asyncio.sleep(1)

        return results

    async def parse_files_parallel(self, file_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        并行处理多个文件的代码分析

        Args:
            file_items: 文件项列表，每个包含 file_path, content, language 等信息

        Returns:
            分析结果列表
        """
        logger.info(f"开始并行处理 {len(file_items)} 个文件，最大并发数: {self.max_concurrent}")

        # 创建任务列表
        tasks = []
        for file_item in file_items:
            task = self.parse_code_file_detailed(
                file_item["file_path"], file_item["content"], file_item["language"], file_item.get("context", "")
            )
            tasks.append(task)

        # 并行执行所有任务
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 处理结果，将异常转换为错误结果
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    error_result = {"file_path": file_items[i]["file_path"], "analysis_items": [], "error": str(result)}
                    processed_results.append(error_result)
                    logger.error(f"文件 {file_items[i]['file_path']} 处理失败: {str(result)}")
                else:
                    processed_results.append(result)

            success_count = sum(1 for r in processed_results if "error" not in r)
            logger.info(f"并行处理完成: {success_count}/{len(file_items)} 个文件成功")

            return processed_results

        except Exception as e:
            logger.error(f"并行处理过程中发生错误: {str(e)}")
            # 返回错误结果
            return [{"file_path": item["file_path"], "analysis_items": [], "error": str(e)} for item in file_items]

    async def parse_files_in_batches(self, file_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        分批并行处理文件，避免一次性创建过多任务

        Args:
            file_items: 文件项列表

        Returns:
            分析结果列表
        """
        logger.info(f"分批处理 {len(file_items)} 个文件，批次大小: {self.batch_size}")

        all_results = []

        # 分批处理
        for i in range(0, len(file_items), self.batch_size):
            batch = file_items[i : i + self.batch_size]
            batch_num = i // self.batch_size + 1
            total_batches = (len(file_items) + self.batch_size - 1) // self.batch_size

            logger.info(f"处理第 {batch_num}/{total_batches} 批，包含 {len(batch)} 个文件")

            # 并行处理当前批次
            batch_results = await self.parse_files_parallel(batch)
            all_results.extend(batch_results)

            # 批次间短暂延迟，避免API限流
            if i + self.batch_size < len(file_items):
                await asyncio.sleep(1)

        return all_results

    def _parse_detailed_response(self, response: str, file_path: str) -> Dict[str, Any]:
        """解析详细分析的响应结果"""
        try:
            # 清理响应内容
            response = response.strip()

            # 尝试提取JSON部分
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                if end != -1:
                    response = response[start:end].strip()
            elif "```" in response:
                start = response.find("```") + 3
                end = response.find("```", start)
                if end != -1:
                    response = response[start:end].strip()

            # 解析JSON
            import json

            result = json.loads(response)

            # 验证结果格式
            if not isinstance(result, dict):
                raise ValueError("Invalid response format: not a dictionary")

            if "analysis_items" not in result:
                result["analysis_items"] = []

            # 验证每个分析项的格式
            valid_items = []
            for item in result.get("analysis_items", []):
                if isinstance(item, dict) and all(
                    key in item for key in ["title", "description", "source", "language", "code"]
                ):
                    valid_items.append(item)
                else:
                    logger.warning(f"Invalid analysis item format in {file_path}: {item}")

            result["analysis_items"] = valid_items
            result["file_path"] = file_path

            logger.info(f"Successfully parsed {len(valid_items)} analysis items from {file_path}")
            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response for {file_path}: {str(e)}")
            logger.debug(f"Response content: {response[:500]}...")
            return {"file_path": file_path, "analysis_items": [], "error": f"JSON parsing error: {str(e)}"}
        except Exception as e:
            logger.error(f"Failed to parse response for {file_path}: {str(e)}")
            return {"file_path": file_path, "analysis_items": [], "error": str(e)}
