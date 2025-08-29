"""
DatabaseUpdateNode - 数据库更新节点，将索引信息更新到数据库
Design: AsyncNode, max_retries=3, wait=5
"""

import aiohttp
import logging
from typing import Dict, Any, Tuple
from pocketflow import AsyncNode

from ..utils.config import get_config

# 设置logger
logger = logging.getLogger(__name__)


class DatabaseUpdateNode(AsyncNode):
    """数据库更新节点 - 将索引信息更新到数据库"""

    def __init__(self):
        super().__init__(max_retries=3, wait=5)
        self.config = get_config()
        # 从配置中获取后端API地址
        self.api_base_url = self.config.api_base_url

    async def prep_async(self, shared: Dict[str, Any]) -> Tuple[int, str]:
        """
        准备数据库更新操作

        Data Access:
        - Read: shared.task_id (任务ID)
        - Read: shared.vectorstore_index (向量索引名称)
        """
        logger.info("=" * 60)
        logger.info("📋 阶段: 数据库更新 (DatabaseUpdateNode)")

        task_id = shared.get("task_id")
        vectorstore_index = shared.get("vectorstore_index")

        if not task_id:
            logger.error("❌ 缺少任务ID")
            raise ValueError("Task ID is required for database update")

        if not vectorstore_index:
            logger.error("❌ 缺少向量索引名称")
            raise ValueError("Vectorstore index is required for database update")

        logger.info(f"🔍 准备更新任务 {task_id} 的索引信息: {vectorstore_index}")
        return task_id, vectorstore_index

    async def exec_async(self, prep_res: Tuple[int, str]) -> bool:
        """
        执行数据库更新操作
        """
        task_id, vectorstore_index = prep_res

        try:
            # 构建API URL
            api_url = f"{self.api_base_url}/api/repository/analysis-tasks/{task_id}"

            # 准备更新数据
            update_data = {"task_index": vectorstore_index, "status": "completed"}

            logger.info(f"🔄 发送PUT请求到: {api_url}")
            logger.info(f"📝 更新数据: {update_data}")

            # 发送PUT请求
            async with aiohttp.ClientSession() as session:
                async with session.put(
                    api_url,
                    json=update_data,
                    headers={"Content-Type": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"✅ 数据库更新成功: {result.get('message', 'Success')}")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ 数据库更新失败: HTTP {response.status} - {error_text}")
                        raise Exception(f"Database update failed: HTTP {response.status}")

        except Exception as e:
            logger.error(f"❌ 数据库更新过程中出错: {str(e)}")
            raise

    async def post_async(self, shared: Dict[str, Any], prep_res: Tuple, exec_res: bool) -> str:
        """
        数据库更新后处理

        Data Access:
        - Write: shared.database_updated (更新状态)
        """
        # prep_res 包含 (task_id, vectorstore_index)，这里不需要使用
        if exec_res:
            shared["database_updated"] = True
            logger.info("✅ 数据库索引更新完成")
        else:
            shared["database_updated"] = False
            logger.error("❌ 数据库索引更新失败")

        return "default"
