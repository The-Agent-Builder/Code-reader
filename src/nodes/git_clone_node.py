"""
GitCloneNode - 克隆远程仓库到本地缓存路径
Design: AsyncNode, max_retries=3, wait=15
"""

from typing import Dict, Any
from pathlib import Path
from pocketflow import AsyncNode

from ..utils.git_manager import GitManager
from ..utils.logger import logger
from ..utils.error_handler import GitCloneError


class GitCloneNode(AsyncNode):
    """克隆远程仓库到本地缓存路径节点"""

    def __init__(self):
        super().__init__(max_retries=3, wait=15)
        self.git_manager = GitManager()

    async def prep_async(self, shared: Dict[str, Any]) -> str:
        """
        根据 repo_url 生成唯一命名的本地缓存路径

        Data Access:
        - Read: shared.repo_url
        """
        logger.info("=" * 60)
        logger.info("📋 阶段 2/4: 仓库克隆 (GitCloneNode)")
        shared["current_stage"] = "git_clone"
        repo_url = shared.get("repo_url")
        if not repo_url:
            logger.error("❌ git clone 需要提供仓库 URL")
            raise GitCloneError("Repository URL is required")
        logger.info(f"🔄 准备克隆仓库: {repo_url}")
        return repo_url

    async def exec_async(self, repo_url: str) -> Path:
        """
        执行 git clone 命令，支持 HTTPS/SSH 方式配置
        """
        try:
            local_path = await self.git_manager.clone_repository(repo_url)
            # logger.info(f"Repository cloned to: {local_path}")
            return local_path
        except Exception as e:
            logger.error(f"❌ 克隆仓库失败: {str(e)}")
            raise GitCloneError(f"Failed to clone repository: {str(e)}")

    async def post_async(self, shared: Dict[str, Any], prep_res: str, exec_res: Path) -> str:
        """
        若成功则设置 shared.local_path, 失败时抛出 GitCloneError

        Data Access:
        - Write: shared.local_path
        """
        shared["local_path"] = str(exec_res)

        # logger.info(f"Local repository path set: {exec_res}")
        return "default"
