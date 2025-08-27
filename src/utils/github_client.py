"""
GitHub API 客户端模块
封装 GitHub REST API 调用逻辑，支持 token 认证、限流控制、错误重试机制
"""

import asyncio
import time
from typing import Dict, Optional, Any, Tuple
import aiohttp
from urllib.parse import urlparse

from .logger import logger
from .error_handler import GitHubAPIError
from .config import get_config


class GitHubClient:
    """GitHub API 客户端"""

    def __init__(self, token: Optional[str] = None):
        if token:
            self.token = token
        else:
            config = get_config()
            self.token = config.github_token
        self.base_url = "https://api.github.com"
        self.session = None
        self.rate_limit_remaining = 5000
        self.rate_limit_reset = 0

        if not self.token:
            logger.warning("未提供GitHub令牌，API速率限制将受到限制")

    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession(headers=self._get_headers(), timeout=aiohttp.ClientTimeout(total=30))
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()
        return False

    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        headers = {"Accept": "application/vnd.github.v3+json", "User-Agent": "GitHub-Analyzer/1.0"}
        if self.token:
            headers["Authorization"] = f"token {self.token}"
        return headers

    def _parse_repo_url(self, repo_url: str) -> Tuple[str, str]:
        """解析仓库URL，提取owner和repo名称"""
        try:
            # 检查输入是否为None或空字符串
            if not repo_url:
                raise ValueError("Repository URL cannot be None or empty")

            # 确保repo_url是字符串类型
            if not isinstance(repo_url, str):
                raise ValueError(f"Repository URL must be a string, got {type(repo_url)}")

            # 处理不同格式的GitHub URL
            if repo_url.startswith("git@github.com:"):
                # SSH格式: git@github.com:owner/repo.git
                path = repo_url.replace("git@github.com:", "").replace(".git", "")
            elif "github.com" in repo_url:
                # HTTPS格式: https://github.com/owner/repo
                parsed = urlparse(repo_url)
                path = parsed.path.strip("/").replace(".git", "")
            else:
                # 直接格式: owner/repo
                path = repo_url

            parts = path.split("/")
            if len(parts) >= 2:
                return parts[0], parts[1]
            else:
                raise ValueError(f"Invalid repository URL format: {repo_url}")
        except Exception as e:
            raise GitHubAPIError(f"Failed to parse repository URL: {repo_url}, error: {str(e)}")

    async def _check_rate_limit(self):
        """检查并处理API限流"""
        if self.rate_limit_remaining <= 1 and time.time() < self.rate_limit_reset:
            wait_time = self.rate_limit_reset - time.time() + 1
            logger.warning(f"Rate limit exceeded, waiting {wait_time:.1f} seconds")
            await asyncio.sleep(wait_time)

    async def _make_request(self, url: str, max_retries: int = 3) -> Dict[str, Any]:
        """发起API请求"""
        await self._check_rate_limit()

        for attempt in range(max_retries):
            try:
                async with self.session.get(url) as response:
                    # 更新限流信息
                    self.rate_limit_remaining = int(response.headers.get("X-RateLimit-Remaining", 0))
                    self.rate_limit_reset = int(response.headers.get("X-RateLimit-Reset", 0))

                    if response.status == 200:
                        return await response.json()
                    elif response.status == 403:
                        raise GitHubAPIError("API rate limit exceeded or access forbidden")
                    elif response.status == 404:
                        raise GitHubAPIError("Repository not found")
                    else:
                        response.raise_for_status()

            except aiohttp.ClientError as e:
                if attempt == max_retries - 1:
                    raise GitHubAPIError(f"Request failed after {max_retries} attempts: {str(e)}")

                wait_time = 2**attempt
                logger.warning(f"Request failed (attempt {attempt + 1}), retrying in {wait_time}s")
                await asyncio.sleep(wait_time)

        raise GitHubAPIError("Max retries exceeded")

    async def get_repo_info(self, repo_url: str) -> Dict[str, Any]:
        """
        获取仓库基本信息

        Returns:
            包含完整仓库信息的字典，包括：
            - 基本信息：name, description, language等
            - 统计信息：stars, forks, watchers等
            - 语言分布：详细的语言占比信息
            - 其他信息：topics, license, README等
        """
        owner, repo = self._parse_repo_url(repo_url)

        # logger.info(f"正在获取仓库信息: {owner}/{repo}")

        # 获取基本仓库信息
        repo_url_api = f"{self.base_url}/repos/{owner}/{repo}"
        repo_data = await self._make_request(repo_url_api)

        # 获取语言统计（详细版本）
        languages_info = await self._get_languages_detailed(owner, repo)

        # 获取README内容
        readme_content = await self._get_readme_content(owner, repo)

        # 格式化更新时间
        updated_at = repo_data.get("updated_at", "")
        if updated_at:
            try:
                from datetime import datetime

                dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
                formatted_updated_at = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
            except:
                formatted_updated_at = updated_at
        else:
            formatted_updated_at = "未知"

        # 构建完整的仓库信息
        return {
            "url": repo_url,
            "name": repo_data.get("name", "未知"),
            "description": repo_data.get("description", "") or "无描述",
            "primary_language": repo_data.get("language", "") or "未知",
            "language": repo_data.get("language", "") or "未知",  # 保持兼容性
            "languages": languages_info,
            "stars": self._format_number(repo_data.get("stargazers_count", 0)),
            "forks": self._format_number(repo_data.get("forks_count", 0)),
            "watchers": self._format_number(repo_data.get("watchers_count", 0)),
            "topics": repo_data.get("topics", []),
            "license": repo_data.get("license", {}).get("name", "未知") if repo_data.get("license") else "未知",
            "created_at": repo_data.get("created_at", ""),
            "updated_at": repo_data.get("updated_at", ""),
            "last_updated": formatted_updated_at,
            "readme": readme_content,
            "full_name": repo_data.get("full_name", f"{owner}/{repo}"),
            "clone_url": repo_data.get("clone_url", ""),
            "ssh_url": repo_data.get("ssh_url", ""),
            "stargazers_count": repo_data.get("stargazers_count", 0),  # 原始数字
            "forks_count": repo_data.get("forks_count", 0),  # 原始数字
            "watchers_count": repo_data.get("watchers_count", 0),  # 原始数字
            "open_issues_count": repo_data.get("open_issues_count", 0),
            "default_branch": repo_data.get("default_branch", "main"),
            "size": repo_data.get("size", 0),  # KB
            "archived": repo_data.get("archived", False),
            "disabled": repo_data.get("disabled", False),
            "private": repo_data.get("private", False),
            "fork": repo_data.get("fork", False),
            "source": "GitHub API",
        }

    async def _get_languages_detailed(self, owner: str, repo: str) -> Dict[str, Any]:
        """
        获取详细的语言占比信息（参照spider_example.py实现）

        Returns:
            包含语言占比和字节数的详细信息
        """
        try:
            languages_url = f"{self.base_url}/repos/{owner}/{repo}/languages"
            languages_data = await self._make_request(languages_url)

            if not languages_data:
                return {"message": "未检测到编程语言"}

            # 计算总字节数
            total_bytes = sum(languages_data.values())

            # 计算每种语言的占比
            languages_percentage = {}
            for language, bytes_count in languages_data.items():
                percentage = (bytes_count / total_bytes) * 100
                languages_percentage[language] = {"bytes": bytes_count, "percentage": round(percentage, 2)}

            # 按占比排序
            sorted_languages = dict(
                sorted(languages_percentage.items(), key=lambda x: x[1]["percentage"], reverse=True)
            )

            return sorted_languages

        except Exception as e:
            logger.warning(f"Failed to fetch languages for {owner}/{repo}: {str(e)}")
            return {"error": f"语言数据获取失败: {str(e)}"}

    def _format_number(self, num: int) -> str:
        """格式化数字显示（参照spider_example.py实现）"""
        if num >= 1000:
            return f"{num/1000:.1f}k"
        return str(num)

    async def _get_readme_content(self, owner: str, repo: str) -> str:
        """获取README文件内容"""
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/readme"
            readme_data = await self._make_request(url)

            # GitHub API返回base64编码的内容
            import base64

            content = base64.b64decode(readme_data["content"]).decode("utf-8")
            return content
        except Exception as e:
            logger.warning(f"Failed to fetch README for {owner}/{repo}: {str(e)}")
            return ""
