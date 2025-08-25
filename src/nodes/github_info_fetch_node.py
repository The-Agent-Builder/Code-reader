"""
GitHubInfoFetchNode - 获取 GitHub 仓库基本信息
Design: AsyncNode, max_retries=3, wait=10
"""

from typing import Dict, Any
from pocketflow import AsyncNode

from ..utils.github_client import GitHubClient
from ..utils.logger import logger
from ..utils.error_handler import GitHubAPIError


class GitHubInfoFetchNode(AsyncNode):
    """获取 GitHub 仓库基本信息节点"""

    def __init__(self):
        super().__init__(max_retries=3, wait=10)

    async def prep_async(self, shared: Dict[str, Any]) -> str:
        """
        校验 URL 格式，提取仓库 owner 和 repo 名称

        Data Access:
        - Read: shared.repo_url
        """
        logger.info("=" * 60)
        logger.info("📋 阶段 1/4: GitHub 仓库信息获取 (GitHubInfoFetchNode)")
        shared["current_stage"] = "github_info_fetch"
        repo_url = shared.get("repo_url")
        logger.info(f"🔍 准备获取仓库信息: {repo_url}")
        if not repo_url:
            logger.error("❌ GitHub仓库 URL 为空或不存在")
            raise GitHubAPIError("Repository URL is required")
        return repo_url

    async def exec_async(self, repo_url: str) -> Dict[str, Any]:
        """
        调用 GitHub API 获取仓库详细信息
        """
        async with GitHubClient() as client:
            repo_info = await client.get_repo_info(repo_url)
            logger.info(f"✅ 获取到仓库信息:{repo_info.get('full_name')}")
            return repo_info

    async def post_async(self, shared: Dict[str, Any], prep_res: str, exec_res: Dict[str, Any]) -> str:
        """
        更新 shared.repo_info, 保存仓库信息到JSON文件, 返回 "default"

        Data Access:
        - Write: shared.repo_info
        - Write: data/results/{repo_name}/repo_info.json
        """
        shared["repo_info"] = exec_res
        # logger.info("保存仓库信息到 shared.repo_info")

        # 保存仓库信息到JSON文件
        await self._save_repo_info_to_file(exec_res)

        return "default"

    async def _save_repo_info_to_file(self, repo_info: Dict[str, Any]):
        """
        将仓库信息保存到JSON文件

        Args:
            repo_info: 仓库信息字典
        """
        try:
            import json
            import os
            from pathlib import Path

            # 获取results路径（使用环境变量或默认值）
            results_path = Path(os.getenv("RESULTS_PATH", "./data/results"))

            # 提取仓库名
            full_name = repo_info.get("full_name", "unknown")
            if "/" in full_name:
                repo_name = full_name.split("/")[-1]
            else:
                repo_name = full_name

            # 创建仓库结果目录
            repo_dir = results_path / repo_name
            repo_dir.mkdir(parents=True, exist_ok=True)

            # 保存仓库信息到JSON文件
            repo_info_file = repo_dir / "repo_info.json"
            with open(repo_info_file, "w", encoding="utf-8") as f:
                json.dump(repo_info, f, ensure_ascii=False, indent=2)

            logger.info(f"✅ 仓库基础信息已保存到: {repo_info_file}")

        except Exception as e:
            logger.error(f"❌ 保存仓库信息失败: {str(e)}")
