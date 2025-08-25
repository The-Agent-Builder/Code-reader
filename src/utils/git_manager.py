"""
Git 管理器模块
封装 git clone、清理缓存路径、权限管理，使用唯一命名规则避免多用户冲突
"""

import os
import shutil
import asyncio
import time
import stat
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse
import git

from .logger import logger
from .error_handler import GitCloneError
from .config import get_config


class GitManager:
    """Git 仓库管理器"""

    def __init__(self, base_path: Optional[str] = None):
        if base_path:
            self.base_path = Path(base_path)
        else:
            config = get_config()
            self.base_path = config.local_repo_path
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _normalize_repo_url(self, repo_url: str) -> str:
        """标准化仓库URL格式"""
        # 检查输入是否为None或空字符串
        if not repo_url:
            raise GitCloneError("Repository URL cannot be None or empty")

        # 确保repo_url是字符串类型
        if not isinstance(repo_url, str):
            raise GitCloneError(f"Repository URL must be a string, got {type(repo_url)}")

        if repo_url.startswith("git@github.com:"):
            # SSH格式转换为HTTPS格式
            repo_path = repo_url.replace("git@github.com:", "").replace(".git", "")
            return f"https://github.com/{repo_path}"
        elif repo_url.startswith("https://github.com/"):
            return repo_url.replace(".git", "")
        else:
            # 假设是 owner/repo 格式
            return f"https://github.com/{repo_url}"

    def _safe_remove_directory(self, path: Path):
        """安全删除目录，处理Windows权限问题"""
        if not path.exists():
            return

        try:
            # 首先尝试正常删除
            shutil.rmtree(path)
            logger.info(f"🗑️ 成功删除目录: {path}")
        except PermissionError:
            # Windows下可能遇到权限问题，尝试修改权限后删除
            logger.warning(f"⚠️ 权限问题，尝试修改权限后删除: {path}")
            try:
                # 递归修改所有文件和目录的权限
                for root, dirs, files in os.walk(path):
                    for dir_name in dirs:
                        dir_path = os.path.join(root, dir_name)
                        os.chmod(dir_path, stat.S_IWRITE | stat.S_IREAD | stat.S_IEXEC)
                    for file_name in files:
                        file_path = os.path.join(root, file_name)
                        os.chmod(file_path, stat.S_IWRITE | stat.S_IREAD)

                # 再次尝试删除
                shutil.rmtree(path)
                logger.info(f"🗑️ 修改权限后成功删除目录: {path}")
            except Exception as e:
                logger.error(f"❌ 无法删除目录 {path}: {str(e)}")
                raise

    def get_local_path(self, repo_url: str) -> Path:
        """获取仓库的本地存储路径"""
        repo_name = self._extract_repo_name(repo_url)
        return self.base_path / repo_name

    def _extract_repo_name(self, repo_url: str) -> str:
        """从URL中提取仓库名称"""
        normalized_url = self._normalize_repo_url(repo_url)
        parsed = urlparse(normalized_url)
        path_parts = parsed.path.strip("/").split("/")
        if len(path_parts) >= 2:
            # 直接返回仓库名，不包含owner
            return path_parts[1]
        return "unknown_repo"

    async def clone_repository(self, repo_url: str, force_refresh: bool = False) -> Path:
        """
        克隆 GitHub HTTPS 仓库到本地缓存

        Args:
            repo_url: GitHub HTTPS URL (如: https://github.com/The-Pocket/PocketFlow)
            force_refresh: 是否强制重新克隆

        Returns:
            本地仓库路径
        """
        local_path = self.get_local_path(repo_url)

        try:
            # 如果目录已存在且不强制刷新，直接返回
            if local_path.exists() and not force_refresh:
                if self._is_valid_git_repo(local_path):
                    logger.info(f"📁 仓库已存在，使用缓存: {local_path}")
                    return local_path
                else:
                    logger.warning(f"⚠️ 无效的git仓库，删除并重新克隆: {local_path}")
                    self._safe_remove_directory(local_path)

            # 如果强制刷新，删除现有目录
            if force_refresh and local_path.exists():
                logger.info(f"🔄 强制刷新，删除现有仓库: {local_path}")
                self._safe_remove_directory(local_path)

            # 确保父目录存在
            local_path.parent.mkdir(parents=True, exist_ok=True)

            # 直接克隆 GitHub HTTPS 仓库
            logger.info(f"📥 开始克隆仓库: {repo_url} -> {local_path}")
            await self._simple_git_clone(repo_url, str(local_path))

            # 验证克隆结果
            if not self._is_valid_git_repo(local_path):
                raise GitCloneError(f"克隆完成但仓库无效: {repo_url}")

            logger.info(f"✅ 仓库克隆成功: {local_path}")
            return local_path

        except GitCloneError:
            # 清理失败的克隆
            if local_path.exists():
                self._safe_remove_directory(local_path)
            raise
        except Exception as e:
            # 清理失败的克隆
            if local_path.exists():
                self._safe_remove_directory(local_path)
            raise GitCloneError(f"克隆仓库失败 {repo_url}: {str(e)}")

    async def _simple_git_clone(self, repo_url: str, local_path: str):
        """
        简单直接的 Git 克隆，专门用于 GitHub HTTPS URL

        Args:
            repo_url: GitHub HTTPS URL
            local_path: 本地目标路径
        """
        try:
            logger.info(f"🔄 执行 Git 克隆命令...")
            logger.info(f"🔄 命令: git clone {repo_url} {local_path}")

            # 执行 git clone 命令（完整克隆）- 添加超时设置
            process = await asyncio.create_subprocess_exec(
                "git",
                "clone",
                repo_url,
                local_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            # 添加超时控制 - 120秒超时（适应大仓库）
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=120.0)
            except asyncio.TimeoutError:
                # 超时时杀死进程
                try:
                    process.kill()
                    await process.wait()
                except:
                    pass
                raise GitCloneError(f"Git 克隆超时 (120秒): {repo_url}")

            if process.returncode != 0:
                error_msg = stderr.decode("utf-8", errors="ignore") if stderr else "未知错误"
                stdout_msg = stdout.decode("utf-8", errors="ignore") if stdout else ""

                logger.error(f"❌ Git 克隆失败:")
                logger.error(f"   返回码: {process.returncode}")
                logger.error(f"   错误信息: {error_msg}")
                if stdout_msg:
                    logger.error(f"   标准输出: {stdout_msg}")

                # 分析常见错误原因
                if "not found" in error_msg.lower() or "repository not found" in error_msg.lower():
                    raise GitCloneError(f"仓库不存在或无访问权限: {repo_url}")
                elif "connection" in error_msg.lower() or "timeout" in error_msg.lower():
                    raise GitCloneError(f"网络连接问题: {error_msg}")
                elif "permission denied" in error_msg.lower():
                    raise GitCloneError(f"权限不足: {error_msg}")
                else:
                    raise GitCloneError(f"Git 克隆失败: {error_msg}")

            logger.info(f"✅ Git 克隆成功")

        except FileNotFoundError:
            raise GitCloneError("Git 命令未找到，请确保已安装 Git")
        except GitCloneError:
            raise
        except asyncio.TimeoutError:
            raise GitCloneError(f"Git 克隆超时: {repo_url}")
        except Exception as e:
            logger.error(f"❌ Git 克隆异常详情: {type(e).__name__}: {str(e)}")
            raise GitCloneError(f"执行 Git 命令时发生错误: {type(e).__name__}: {str(e)}")

    async def _wait_for_clone_completion(self, local_path: Path, lock_file: Path, max_wait: int = 300):
        """
        等待其他进程完成克隆

        Args:
            local_path: 本地仓库路径
            lock_file: 锁文件路径
            max_wait: 最大等待时间（秒）
        """
        start_time = time.time()
        wait_interval = 2  # 每2秒检查一次

        while lock_file.exists() and (time.time() - start_time) < max_wait:
            logger.info(f"⏳ 等待其他进程完成克隆... ({int(time.time() - start_time)}s)")
            await asyncio.sleep(wait_interval)

            # 如果目录已经存在且有效，说明克隆完成了
            if local_path.exists() and self._is_valid_git_repo(local_path):
                logger.info(f"✅ 检测到克隆已完成")
                break

        # 如果超时，删除可能的僵尸锁文件
        if lock_file.exists() and (time.time() - start_time) >= max_wait:
            logger.warning(f"⚠️ 等待超时，删除可能的僵尸锁文件: {lock_file}")
            lock_file.unlink()

    async def _async_git_clone(self, repo_url: str, local_path: str):
        """异步执行git clone命令"""
        try:
            logger.info(f"🔄 执行 Git 克隆命令...")
            logger.info(f"   命令: git clone {repo_url} {local_path}")

            # 使用asyncio.create_subprocess_exec执行git命令（完整克隆）
            process = await asyncio.create_subprocess_exec(
                "git",
                "clone",
                repo_url,
                local_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown git error"
                stdout_msg = stdout.decode() if stdout else "No output"

                logger.error(f"❌ Git 克隆失败:")
                logger.error(f"   返回码: {process.returncode}")
                logger.error(f"   错误信息: {error_msg}")
                logger.error(f"   标准输出: {stdout_msg}")

                # 检查常见错误类型
                if "Repository not found" in error_msg or "not found" in error_msg:
                    logger.error("   可能原因: 仓库不存在或无访问权限")
                elif "Permission denied" in error_msg:
                    logger.error("   可能原因: 权限不足，可能需要配置 SSH 密钥或访问令牌")
                elif "Connection" in error_msg or "timeout" in error_msg:
                    logger.error("   可能原因: 网络连接问题")

                raise GitCloneError(f"Git clone failed: {error_msg}")

            logger.info(f"✅ Git 克隆成功")

        except FileNotFoundError:
            # 如果git命令不存在，尝试使用GitPython
            logger.warning("⚠️ Git 命令未找到，尝试使用 GitPython 作为备选方案")
            try:
                git.Repo.clone_from(repo_url, local_path)  # 完整克隆
                logger.info(f"✅ GitPython 克隆成功")
            except Exception as e:
                logger.error(f"❌ GitPython 克隆也失败: {str(e)}")
                raise GitCloneError(f"GitPython clone failed: {str(e)}")

    def _is_valid_git_repo(self, path: Path) -> bool:
        """检查路径是否为有效的git仓库"""
        try:
            git_dir = path / ".git"
            return git_dir.exists() and (git_dir.is_dir() or git_dir.is_file())
        except Exception:
            return False

    def cleanup_repository(self, repo_url: str) -> bool:
        """清理指定仓库的本地缓存"""
        try:
            local_path = self.get_local_path(repo_url)
            if local_path.exists():
                shutil.rmtree(local_path)
                logger.info(f"Cleaned up repository cache at {local_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to cleanup repository {repo_url}: {str(e)}")
            return False

    def cleanup_all(self) -> int:
        """清理所有本地仓库缓存"""
        count = 0
        try:
            if self.base_path.exists():
                for item in self.base_path.iterdir():
                    if item.is_dir():
                        shutil.rmtree(item)
                        count += 1
                logger.info(f"Cleaned up {count} repository caches")
            return count
        except Exception as e:
            logger.error(f"Failed to cleanup all repositories: {str(e)}")
            return count

    def get_repo_size(self, repo_url: str) -> int:
        """获取本地仓库大小（字节）"""
        try:
            local_path = self.get_local_path(repo_url)
            if not local_path.exists():
                return 0

            total_size = 0
            for dirpath, _, filenames in os.walk(local_path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    total_size += os.path.getsize(filepath)
            return total_size
        except Exception as e:
            logger.error(f"Failed to get repository size: {str(e)}")
            return 0
