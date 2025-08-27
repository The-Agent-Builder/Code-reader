"""
SaveToMySQLNode - 将分析结果保存到 MySQL (SQLAlchemy)
支持从本地文件和流程共享数据两种方式读取数据
Design: Node
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from pocketflow import Node

from ..utils.logger import logger
from ..utils.db import get_session, init_db
from ..utils.config import get_config
from ..models.mysql_models import Repository, AnalysisTask, FileAnalysis, SearchTarget, AnalysisItem


class SaveToMySQLNode(Node):
    """将分析结果保存到 MySQL 的节点。

    支持两种数据源模式：
    1. 从流程共享数据读取 (原有模式)
       需要 shared 中包含：
       - repo_url
       - repo_info
       - code_analysis (CodeParsingBatchNode 的输出)

    2. 从本地文件读取 (新增模式)
       需要 shared 中包含：
       - results_path: 结果文件路径，如 "data/results/PocketFlow"
       或者
       - repo_name: 仓库名称，将自动从 RESULTS_PATH 环境变量构建路径
    """

    def __init__(self, use_local_files: bool = False):
        super().__init__()
        self.use_local_files = use_local_files
        self.config = get_config()
        # 确保表存在
        init_db()

    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("📋 阶段: 将结果保存到 MySQL (SaveToMySQLNode)")
        shared["current_stage"] = "saving_to_mysql"

        if self.use_local_files:
            # 从本地文件读取模式
            logger.info("🗂️ 使用本地文件模式读取分析结果")

            # 确定结果文件路径
            if "results_path" in shared:
                results_path = Path(shared["results_path"])
            elif "repo_name" in shared:
                results_base_path = Path(self.config.results_path)
                results_path = results_base_path / shared["repo_name"]
            else:
                raise ValueError("本地文件模式需要提供 'results_path' 或 'repo_name'")

            if not results_path.exists():
                raise ValueError(f"结果文件路径不存在: {results_path}")

            shared["_results_path"] = results_path
            logger.info(f"📁 结果文件路径: {results_path}")
        else:
            # 从流程共享数据读取模式 (原有逻辑)
            logger.info("🔄 使用流程共享数据模式")
            required = ["repo_url", "repo_info", "code_analysis"]
            for k in required:
                if k not in shared:
                    raise ValueError(f"Missing required shared data: {k}")

        return shared

    def _load_local_files(self, results_path: Path) -> Dict[str, Any]:
        """从本地文件加载分析结果数据"""
        logger.info("📖 开始从本地文件加载分析结果")

        # 定义需要的文件
        files_to_load = {
            "repo_info": "repo_info.json",
            "metadata": "metadata.json",
            "analysis_report": "analysis_report.json",
        }

        loaded_data = {}

        # 加载各个文件
        for key, filename in files_to_load.items():
            file_path = results_path / filename
            if file_path.exists():
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        loaded_data[key] = json.load(f)
                    logger.info(f"✅ 成功加载 {filename}")
                except Exception as e:
                    logger.warning(f"⚠️ 加载 {filename} 失败: {e}")
                    loaded_data[key] = {}
            else:
                logger.warning(f"⚠️ 文件不存在: {file_path}")
                loaded_data[key] = {}

        # 构建统一的数据结构
        repo_info = loaded_data["repo_info"]
        metadata = loaded_data["metadata"]
        analysis_report = loaded_data["analysis_report"]

        # 提取仓库信息
        repo_url = repo_info.get("url") or repo_info.get("clone_url", "")

        # 提取文件分析数据
        files_data = analysis_report.get("files", [])

        # 转换为与流程数据兼容的格式
        code_analysis = []
        for file_data in files_data:
            file_analysis = {
                "file_path": file_data.get("file_path", ""),
                "language": file_data.get("language", "unknown"),
                "analysis_items": file_data.get("analysis_items", []),
                "error": None,  # 本地文件中通常不包含错误信息
            }
            code_analysis.append(file_analysis)

        result = {
            "repo_url": repo_url,
            "repo_info": repo_info,
            "code_analysis": code_analysis,
            "metadata": metadata,
            "analysis_report": analysis_report,
        }

        logger.info(f"📊 加载完成: {len(code_analysis)} 个文件的分析结果")
        return result

    def exec(self, shared: Dict[str, Any]) -> str:
        session_maker = get_session()
        session = session_maker()
        try:
            # 根据模式获取数据
            if self.use_local_files:
                # 从本地文件加载数据
                results_path = shared["_results_path"]
                data = self._load_local_files(results_path)
                repo_info = data["repo_info"]
                code_analysis = data["code_analysis"]
                repo_url = data["repo_url"]
                metadata = data.get("metadata", {})
            else:
                # 从流程共享数据获取 (原有逻辑)
                repo_info = shared.get("repo_info", {})
                code_analysis: List[Dict[str, Any]] = shared.get("code_analysis", [])
                repo_url = shared.get("repo_url", "")
                metadata = {}

            # 1) upsert Repository
            repo = Repository(
                user_id=1,  # 默认用户ID，可以根据需要调整
                name=repo_info.get("name") or repo_info.get("full_name", "unknown").split("/")[-1],
                full_name=repo_info.get("full_name"),
                local_path=shared.get("local_path", ""),  # 从共享数据获取本地路径
                status=1,  # 默认状态为存在
            )
            session.add(repo)
            session.flush()  # 获取 repo.id

            # 2) create AnalysisTask
            # 从 metadata 或 shared 中获取时间信息
            if self.use_local_files and metadata:
                analysis_time_str = metadata.get("analysis_time") or metadata.get("created_at")
                if analysis_time_str:
                    try:
                        # 尝试解析 ISO 格式时间
                        analysis_time = datetime.fromisoformat(analysis_time_str.replace("Z", "+00:00"))
                    except:
                        analysis_time = datetime.now()
                else:
                    analysis_time = datetime.now()

                # 从 metadata 获取统计信息
                stats = metadata.get("statistics", {})
                total_files = stats.get("total_files", len(code_analysis))
                successful_files = len([r for r in code_analysis if not r.get("error")])
                failed_files = total_files - successful_files
            else:
                analysis_time = datetime.now()
                total_files = len(code_analysis)
                successful_files = sum(1 for r in code_analysis if not r.get("error"))
                failed_files = sum(1 for r in code_analysis if r.get("error"))

            task = AnalysisTask(
                repository_id=repo.id,
                total_files=total_files,
                successful_files=successful_files,
                failed_files=failed_files,
                code_lines=0,  # 可以根据实际需要计算
                module_count=0,  # 可以根据实际需要计算
                status="completed",
                start_time=analysis_time,
                end_time=analysis_time,
            )
            session.add(task)
            session.flush()

            # 3) create FileAnalysis + SearchTarget + AnalysisItem
            for file_res in code_analysis:
                file_path = file_res.get("file_path")
                language = file_res.get("language") or "unknown"
                err = file_res.get("error")

                file_row = FileAnalysis(
                    task_id=task.id,
                    file_path=file_path,
                    language=language,
                    status=("failed" if err else "success"),
                    error_message=(str(err) if err else None),
                )
                session.add(file_row)
                session.flush()

                items = file_res.get("analysis_items", [])
                # 尝试读取带分组的形式（如果 code_parsing 节点写入 shared 时附带了 search_target）
                for item in items:
                    search_target_text = item.get("search_target") or item.get("file_path") or file_path
                    # 解析 target 类型
                    target_type = "file"
                    target_name: Optional[str] = None
                    if search_target_text.startswith("文件-类("):
                        target_type = "class"
                        target_name = search_target_text[len("文件-类(") : -1]
                    elif search_target_text.startswith("文件-函数("):
                        target_type = "function"
                        target_name = search_target_text[len("文件-函数(") : -1]
                    else:
                        target_type = "file"
                        target_name = file_path

                    target_identifier = search_target_text
                    target_row = SearchTarget(
                        file_analysis_id=file_row.id,
                        target_type=target_type,
                        target_name=target_name,
                        target_identifier=target_identifier,
                    )
                    session.add(target_row)
                    session.flush()

                    # AnalysisItem
                    ai = AnalysisItem(
                        file_analysis_id=file_row.id,
                        search_target_id=target_row.id,
                        title=item.get("title", "Unknown"),
                        description=item.get("description"),
                        source=item.get("source"),
                        language=item.get("language"),
                        code=item.get("code"),
                        start_line=_extract_start_line(item.get("source")),
                        end_line=_extract_end_line(item.get("source")),
                    )
                    session.add(ai)

            session.commit()
            logger.info(f"✅ MySQL 保存完成: repo_id={repo.id}, task_id={task.id}")
            return "default"
        except Exception as e:
            session.rollback()
            logger.error(f"❌ 保存到 MySQL 失败: {e}")
            raise
        finally:
            session.close()

    def post(self, shared: Dict[str, Any], _prep_res: Dict[str, Any], _exec_res: str) -> str:
        shared["mysql_saved"] = True
        data_source = "本地文件" if self.use_local_files else "流程数据"
        logger.info(f"✅ MySQL 保存完成 (数据源: {data_source})")
        return "default"


def _extract_start_line(source: Optional[str]) -> Optional[int]:
    if not source:
        return None
    try:
        if ":" in source:
            part = source.split(":", 1)[1]
            if "-" in part:
                return int(part.split("-", 1)[0])
            return int(part)
    except Exception:
        return None
    return None


def _extract_end_line(source: Optional[str]) -> Optional[int]:
    if not source:
        return None
    try:
        if ":" in source:
            part = source.split(":", 1)[1]
            if "-" in part:
                return int(part.split("-", 1)[1])
            return int(part)
    except Exception:
        return None
    return None
