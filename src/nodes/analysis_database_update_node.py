"""
AnalysisDatabaseUpdateNode - 将分析结果保存到数据库
通过API接口将分析项保存到数据库中
"""

import asyncio
import aiohttp
from typing import Dict, Any, List
from pocketflow import AsyncNode

from ..utils.logger import logger
from ..utils.config import get_config


class AnalysisDatabaseUpdateNode(AsyncNode):
    """分析结果数据库更新节点 - 将分析结果通过API保存到数据库"""

    def __init__(self):
        super().__init__()
        config = get_config()
        self.api_base_url = config.api_base_url  # 后端API地址

    async def exec_async(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """
        将分析结果保存到数据库

        Data Access:
        - Read: shared.web_code_analysis
        - Write: shared.database_update_results
        """
        logger.info("=" * 60)
        logger.info("📋 阶段: 分析结果数据库更新 (AnalysisDatabaseUpdateNode)")

        shared["current_stage"] = "database_update"

        # 获取分析结果 - 支持多种分析结果类型
        analysis_results = shared.get("web_code_analysis", []) or shared.get("single_file_analysis", [])
        if not analysis_results:
            logger.warning("没有找到分析结果，跳过数据库更新")
            shared["database_update_results"] = {
                "status": "skipped",
                "message": "没有分析结果需要保存",
                "saved_items": 0,
                "failed_items": 0,
            }
            return shared

        logger.info(f"🔄 开始保存 {len(analysis_results)} 个文件的分析结果")

        # 统计信息
        total_items = 0
        saved_items = 0
        failed_items = 0
        save_results = []

        # 逐个文件处理分析结果
        for file_result in analysis_results:
            # 支持两种ID字段名：file_analysis_id（Web分析）和 file_id（单文件分析）
            file_analysis_id = file_result.get("file_analysis_id") or file_result.get("file_id")
            file_path = file_result.get("file_path")
            analysis_items = file_result.get("analysis_items", [])

            if not file_analysis_id or not analysis_items:
                logger.warning(f"跳过无效的文件结果: {file_path}")
                continue

            logger.info(f"📝 保存文件 {file_path} 的 {len(analysis_items)} 个分析项")

            # 逐个保存分析项
            for item in analysis_items:
                total_items += 1

                # 准备API请求数据
                item_data = self._prepare_analysis_item_data(item, file_analysis_id)

                # 调用API保存
                save_result = await self._save_analysis_item(item_data)
                save_results.append(save_result)

                if save_result["success"]:
                    saved_items += 1
                    logger.debug(f"✅ 保存成功: {item.get('title', 'Unknown')}")
                else:
                    failed_items += 1
                    logger.error(
                        f"❌ 保存失败: {item.get('title', 'Unknown')} - {save_result.get('error', 'Unknown error')}"
                    )

        # 更新共享状态
        shared["database_update_results"] = {
            "status": "completed",
            "total_items": total_items,
            "saved_items": saved_items,
            "failed_items": failed_items,
            "success_rate": f"{(saved_items / total_items * 100):.1f}%" if total_items > 0 else "0%",
            "save_results": save_results,
        }

        logger.info(f"✅ 数据库更新完成:")
        logger.info(f"   - 总分析项: {total_items}")
        logger.info(f"   - 保存成功: {saved_items}")
        logger.info(f"   - 保存失败: {failed_items}")
        logger.info(f"   - 成功率: {shared['database_update_results']['success_rate']}")

        return shared

    def _prepare_analysis_item_data(self, item: Dict[str, Any], file_analysis_id: int) -> Dict[str, Any]:
        """
        准备分析项数据，转换为API接口所需的格式
        """
        # 从分析项中提取目标类型和名称
        title = item.get("title", "")
        source = item.get("source", "")

        # 推断目标类型
        target_type, target_name = self._infer_target_info(title, source)

        # 提取行号信息
        start_line, end_line = self._extract_line_numbers(source)

        return {
            "file_analysis_id": file_analysis_id,
            "title": title,
            "description": item.get("description", ""),
            "target_type": target_type,
            "target_name": target_name,
            "source": source,
            "language": item.get("language", ""),
            "code": item.get("code", ""),
            "start_line": start_line,
            "end_line": end_line,
        }

    def _infer_target_info(self, title: str, source: str) -> tuple[str, str]:
        """
        从标题和源码位置推断目标类型和名称
        """
        import re

        title_lower = title.lower()

        # 检查是否是类
        if "class" in title_lower or "类" in title:
            # 尝试提取类名
            class_patterns = [
                r"class\s+([A-Za-z_][A-Za-z0-9_]*)",
                r"类\s*([A-Za-z_][A-Za-z0-9_]*)",
                r"([A-Za-z_][A-Za-z0-9_]*)\s*类",
            ]

            for pattern in class_patterns:
                match = re.search(pattern, title, re.IGNORECASE)
                if match:
                    return "class", match.group(1)

            return "class", "Unknown"

        # 检查是否是函数/方法
        elif any(keyword in title_lower for keyword in ["function", "method", "def", "函数", "方法"]):
            # 尝试提取函数名
            func_patterns = [
                r"def\s+([A-Za-z_][A-Za-z0-9_]*)",
                r"function\s+([A-Za-z_][A-Za-z0-9_]*)",
                r"([A-Za-z_][A-Za-z0-9_]*)\s*\(",
                r"方法\s*([A-Za-z_][A-Za-z0-9_]*)",
                r"函数\s*([A-Za-z_][A-Za-z0-9_]*)",
            ]

            for pattern in func_patterns:
                match = re.search(pattern, title, re.IGNORECASE)
                if match:
                    return "function", match.group(1)

            return "function", "Unknown"

        # 默认为文件级别
        return "file", ""

    def _extract_line_numbers(self, source: str) -> tuple[int, int]:
        """
        从源码位置字符串中提取行号
        """
        import re

        if not source:
            return None, None

        # 匹配行号模式，如 "file.py:10-20" 或 "file.py:10"
        line_match = re.search(r":(\d+)(?:-(\d+))?", source)
        if line_match:
            start_line = int(line_match.group(1))
            end_line = int(line_match.group(2)) if line_match.group(2) else start_line
            return start_line, end_line

        return None, None

    async def _save_analysis_item(self, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        通过API保存单个分析项到数据库
        """
        try:
            url = f"{self.api_base_url}/api/repository/analysis-items"

            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=item_data) as response:
                    if response.status == 201:
                        # 保存成功
                        response_data = await response.json()
                        return {
                            "success": True,
                            "item_data": item_data,
                            "response": response_data,
                            "status_code": response.status,
                        }
                    else:
                        # 保存失败
                        try:
                            error_data = await response.json()
                            error_message = error_data.get("message", f"HTTP {response.status}")
                        except:
                            error_message = f"HTTP {response.status}"

                        return {
                            "success": False,
                            "item_data": item_data,
                            "error": error_message,
                            "status_code": response.status,
                        }

        except Exception as e:
            return {"success": False, "item_data": item_data, "error": str(e), "status_code": None}
