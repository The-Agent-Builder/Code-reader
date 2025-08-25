"""
SaveResultsNode - 保存分析结果及元数据
Design: Node
"""

from typing import Dict, Any
from datetime import datetime
from pocketflow import Node

from ..utils.result_storage import ResultStorage
from ..utils.logger import logger
from ..utils.error_handler import ResultStorageError


class SaveResultsNode(Node):
    """保存分析结果及元数据节点"""

    def __init__(self):
        super().__init__()
        self.result_storage = ResultStorage()

    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据仓库名和哈希生成文件夹路径

        Data Access:
        - Read: shared.repo_info, shared.code_analysis
        """
        logger.info("📋 最终阶段: 结果保存 (SaveResultsNode)")
        shared["current_stage"] = "saving_results"

        required_keys = ["repo_info", "code_analysis"]
        for key in required_keys:
            if key not in shared:
                logger.error(f"❌ Missing required data: {key}")
                raise ResultStorageError(f"Missing required data: {key}")

        # 添加分析时间和状态
        shared["analysis_time"] = datetime.now().isoformat()
        shared["status"] = "success"

        logger.info("💾 准备保存分析结果")
        return shared

    def exec(self, shared_data: Dict[str, Any]) -> str:
        """
        将分析结构转换为 Markdown 文本
        """
        try:
            result_filepath = self.result_storage.save_analysis_result(shared_data)
            logger.info(f"Analysis results saved to: {result_filepath}")
            return result_filepath
        except Exception as e:
            raise ResultStorageError(f"Failed to save results: {str(e)}")

    def post(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: str) -> str:
        """
        将结果写入磁盘，记录到索引文件中

        Data Access:
        - Write: shared.result_filepath, 本地磁盘文件
        """
        shared["result_filepath"] = exec_res
        logger.info("Analysis results saved successfully")
        return "default"
