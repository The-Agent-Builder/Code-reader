"""
LocalFolderNode - 处理本地文件夹路径，生成仓库信息
Design: Node
"""

import os
from typing import Dict, Any
from pathlib import Path
from datetime import datetime
from pocketflow import Node

from ..utils.logger import logger
from ..utils.error_handler import GitCloneError


class LocalFolderNode(Node):
    """处理本地文件夹路径，生成仓库信息节点"""

    def __init__(self):
        super().__init__()

    def prep(self, shared: Dict[str, Any]) -> str:
        """
        验证本地文件夹路径是否存在

        Data Access:
        - Read: shared.local_folder_path
        """
        logger.info("=" * 60)
        logger.info("📋 阶段 1/3: 本地文件夹处理 (LocalFolderNode)")
        shared["current_stage"] = "local_folder_processing"

        local_folder_path = shared.get("local_folder_path")
        if not local_folder_path:
            logger.error("❌ 本地文件夹路径为空或不存在")
            raise GitCloneError("Local folder path is required")

        logger.info(f"🔍 准备处理本地文件夹: {local_folder_path}")
        return local_folder_path

    def exec(self, local_folder_path: str) -> Path:
        """
        验证路径存在性并返回Path对象
        """
        try:
            local_path = Path(local_folder_path)

            if not local_path.exists():
                logger.error(f"❌ 本地文件夹路径不存在: {local_path}")
                raise GitCloneError(f"Local folder path does not exist: {local_path}")

            if not local_path.is_dir():
                logger.error(f"❌ 路径不是文件夹: {local_path}")
                raise GitCloneError(f"Path is not a directory: {local_path}")

            logger.info(f"✅ 本地文件夹验证成功: {local_path}")
            return local_path

        except Exception as e:
            logger.error(f"❌ 处理本地文件夹失败: {str(e)}")
            raise GitCloneError(f"Failed to process local folder: {str(e)}")

    def post(self, shared: Dict[str, Any], prep_res: str, exec_res: Path) -> str:
        """
        生成仓库信息并更新共享数据

        Data Access:
        - Write: shared.local_path, shared.repo_info
        """
        try:
            # 设置本地路径
            shared["local_path"] = exec_res

            # 生成仓库信息
            folder_name = exec_res.name
            repo_info = {
                "name": folder_name,
                "full_name": f"{folder_name}",
                "description": f"Local repository analysis for {folder_name}",
                "language": self._detect_primary_language(exec_res),
                "size": self._calculate_folder_size(exec_res),
            }

            shared["repo_info"] = repo_info

            logger.info(f"✅ 本地文件夹处理完成: {folder_name}")
            logger.info(f"📊 检测到主要语言: {repo_info['language']}")
            logger.info(f"📁 文件夹大小: {repo_info['size']} bytes")

            return "default"

        except Exception as e:
            logger.error(f"❌ 生成仓库信息失败: {str(e)}")
            raise GitCloneError(f"Failed to generate repo info: {str(e)}")

    def _detect_primary_language(self, folder_path: Path) -> str:
        """
        检测文件夹中的主要编程语言
        """
        language_extensions = {
            ".py": "Python",
            ".js": "JavaScript",
            ".ts": "TypeScript",
            ".java": "Java",
            ".cpp": "C++",
            ".c": "C",
            ".cs": "C#",
            ".php": "PHP",
            ".rb": "Ruby",
            ".go": "Go",
            ".rs": "Rust",
            ".swift": "Swift",
            ".kt": "Kotlin",
            ".scala": "Scala",
            ".r": "R",
            ".m": "Objective-C",
            ".sh": "Shell",
            ".pl": "Perl",
            ".lua": "Lua",
            ".dart": "Dart",
            ".vue": "Vue",
            ".jsx": "JavaScript",
            ".tsx": "TypeScript",
        }

        language_counts = {}

        try:
            for file_path in folder_path.rglob("*"):
                if file_path.is_file():
                    suffix = file_path.suffix.lower()
                    if suffix in language_extensions:
                        language = language_extensions[suffix]
                        language_counts[language] = language_counts.get(language, 0) + 1

            if language_counts:
                # 返回文件数量最多的语言
                primary_language = max(language_counts, key=language_counts.get)
                return primary_language
            else:
                return "Unknown"

        except Exception as e:
            logger.warning(f"⚠️ 语言检测失败: {str(e)}")
            return "Unknown"

    def _calculate_folder_size(self, folder_path: Path) -> int:
        """
        计算文件夹大小（字节）
        """
        try:
            total_size = 0
            for file_path in folder_path.rglob("*"):
                if file_path.is_file():
                    try:
                        total_size += file_path.stat().st_size
                    except (OSError, IOError):
                        # 跳过无法访问的文件
                        continue
            return total_size
        except Exception as e:
            logger.warning(f"⚠️ 文件夹大小计算失败: {str(e)}")
            return 0
