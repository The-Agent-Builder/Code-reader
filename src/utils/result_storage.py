"""
结果存储管理模块
管理分析结果的目录结构与元信息记录，支持JSON/Markdown双格式存储
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from .logger import logger
from .error_handler import ResultStorageError
from .config import get_config


class ResultStorage:
    """分析结果存储管理器"""

    def __init__(self, base_path: Optional[str] = None):
        if base_path:
            self.base_path = Path(base_path)
        else:
            config = get_config()
            self.base_path = config.results_path
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.index_file = self.base_path / "index.json"
        self._load_index()

    def _load_index(self):
        """加载索引文件"""
        try:
            if self.index_file.exists():
                with open(self.index_file, "r", encoding="utf-8") as f:
                    self.index = json.load(f)
            else:
                self.index = {"analyses": []}

            # 扫描文件夹并更新索引
            self._scan_and_update_index()
        except Exception as e:
            logger.warning(f"Failed to load index file: {str(e)}")
            self.index = {"analyses": []}
            # 尝试重建索引
            self._scan_and_update_index()

    def _save_index(self):
        """保存索引文件"""
        try:
            with open(self.index_file, "w", encoding="utf-8") as f:
                json.dump(self.index, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save index file: {str(e)}")

    def _scan_and_update_index(self):
        """扫描结果文件夹并更新索引"""
        try:
            logger.info("🔍 扫描分析结果文件夹...")

            # 获取现有索引中的分析ID
            existing_ids = {analysis.get("analysis_id") for analysis in self.index["analyses"]}

            # 扫描文件夹
            discovered_count = 0
            for item in self.base_path.iterdir():
                if item.is_dir() and item.name != "__pycache__":
                    analysis_id = item.name

                    # 如果索引中已存在，跳过
                    if analysis_id in existing_ids:
                        continue

                    # 尝试从文件夹中加载分析结果
                    metadata = self._load_analysis_metadata(analysis_id)
                    if metadata:
                        self.index["analyses"].append(metadata)
                        discovered_count += 1
                        logger.info(f"📁 发现分析结果: {analysis_id}")

            if discovered_count > 0:
                # 按时间排序，最新的在前
                self.index["analyses"].sort(key=lambda x: x.get("created_at", ""), reverse=True)
                self._save_index()
                logger.info(f"✅ 发现并添加了 {discovered_count} 个分析结果到索引")
            else:
                logger.info("📋 没有发现新的分析结果")

        except Exception as e:
            logger.error(f"扫描分析结果文件夹失败: {str(e)}")

    def _load_analysis_metadata(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """从分析文件夹中加载元数据"""
        try:
            analysis_dir = self.base_path / analysis_id

            # 优先尝试加载 metadata.json
            metadata_file = analysis_dir / "metadata.json"
            if metadata_file.exists():
                with open(metadata_file, "r", encoding="utf-8") as f:
                    metadata = json.load(f)

                    # 检查统计信息是否为空，如果为空则尝试重新计算
                    stats = metadata.get("statistics", {})
                    total_files = stats.get("total_files", 0)

                    if total_files == 0:
                        # 尝试从analysis.json重新计算统计信息
                        enhanced_metadata = self._enhance_metadata_with_stats(metadata, analysis_dir)
                        if enhanced_metadata:
                            return enhanced_metadata

                    return metadata

            # 如果没有 metadata.json，尝试从其他文件构建元数据
            return self._build_metadata_from_files(analysis_id, analysis_dir)

        except Exception as e:
            logger.warning(f"加载分析元数据失败 {analysis_id}: {str(e)}")
            return None

    def _build_metadata_from_files(self, analysis_id: str, analysis_dir: Path) -> Optional[Dict[str, Any]]:
        """从文件夹中的文件构建元数据"""
        try:
            metadata = {
                "analysis_id": analysis_id,
                "repo_name": analysis_id,  # 默认使用文件夹名作为仓库名
                "status": "completed",
                "statistics": {"total_files": 0, "total_functions": 0, "total_classes": 0, "languages": {}},
            }

            # 尝试从 repo_info.json 获取仓库信息
            repo_info_file = analysis_dir / "repo_info.json"
            if repo_info_file.exists():
                with open(repo_info_file, "r", encoding="utf-8") as f:
                    repo_info = json.load(f)
                    metadata["repo_url"] = repo_info.get("clone_url", "")
                    metadata["repo_name"] = repo_info.get("full_name", analysis_id)
                    if "languages" in repo_info:
                        metadata["statistics"]["languages"] = repo_info["languages"]

            # 尝试从 analysis.json 获取分析信息
            analysis_file = analysis_dir / "analysis.json"
            if analysis_file.exists():
                with open(analysis_file, "r", encoding="utf-8") as f:
                    analysis_data = json.load(f)
                    if "analysis_time" in analysis_data:
                        metadata["analysis_time"] = analysis_data["analysis_time"]
                        metadata["created_at"] = analysis_data["analysis_time"]

                    # 统计代码分析结果
                    code_analysis = analysis_data.get("code_analysis", [])
                    if code_analysis:
                        total_functions = 0
                        total_classes = 0
                        for file_analysis in code_analysis:
                            if isinstance(file_analysis, dict):
                                total_functions += len(file_analysis.get("functions", []))
                                total_classes += len(file_analysis.get("classes", []))

                        metadata["statistics"]["total_files"] = len(code_analysis)
                        metadata["statistics"]["total_functions"] = total_functions
                        metadata["statistics"]["total_classes"] = total_classes
                    else:
                        # 如果没有详细的代码分析结果，尝试从本地仓库统计基本信息
                        local_path = analysis_data.get("local_path")
                        if local_path:
                            basic_stats = self._get_basic_file_stats(Path(local_path))
                            metadata["statistics"].update(basic_stats)

            # 如果没有时间信息，使用文件修改时间
            if "created_at" not in metadata:
                try:
                    # 使用最新的分析报告文件时间
                    report_files = list(analysis_dir.glob("analysis_report*.md"))
                    if report_files:
                        latest_file = max(report_files, key=lambda f: f.stat().st_mtime)
                        timestamp = datetime.fromtimestamp(latest_file.stat().st_mtime)
                        metadata["created_at"] = timestamp.isoformat()
                        metadata["analysis_time"] = timestamp.isoformat()
                    else:
                        metadata["created_at"] = datetime.now().isoformat()
                        metadata["analysis_time"] = datetime.now().isoformat()
                except:
                    metadata["created_at"] = datetime.now().isoformat()
                    metadata["analysis_time"] = datetime.now().isoformat()

            return metadata

        except Exception as e:
            logger.warning(f"构建元数据失败 {analysis_id}: {str(e)}")
            return None

    def _get_basic_file_stats(self, repo_path: Path) -> Dict[str, Any]:
        """从仓库路径获取基本的文件统计信息"""
        stats = {
            "total_files": 0,
            "total_functions": 0,
            "total_classes": 0,
        }

        try:
            if not repo_path.exists():
                return stats

            # 使用统一的文件过滤器
            from .file_filter import FileFilter, SUPPORTED_CODE_EXTENSIONS

            file_filter = FileFilter(repo_path)
            code_files = file_filter.scan_directory(repo_path, SUPPORTED_CODE_EXTENSIONS)

            total_functions = 0
            total_classes = 0
            total_files = len(code_files)

            for file_path in code_files:
                # 简单的函数和类统计（基于关键字匹配）
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()

                        # 根据文件类型统计函数和类
                        if file_path.suffix == ".py":
                            # Python: def 和 class
                            import re

                            functions = re.findall(r"^\s*def\s+\w+", content, re.MULTILINE)
                            classes = re.findall(r"^\s*class\s+\w+", content, re.MULTILINE)
                            total_functions += len(functions)
                            total_classes += len(classes)
                        elif file_path.suffix in {".js", ".ts"}:
                            # JavaScript/TypeScript: function 和 class
                            import re

                            functions = re.findall(r"function\s+\w+|=>\s*{|\w+\s*:\s*function", content)
                            classes = re.findall(r"class\s+\w+", content)
                            total_functions += len(functions)
                            total_classes += len(classes)
                        elif file_path.suffix == ".java":
                            # Java: public/private/protected methods 和 class
                            import re

                            functions = re.findall(r"(public|private|protected).*?\w+\s*\([^)]*\)\s*{", content)
                            classes = re.findall(r"(public|private)?\s*class\s+\w+", content)
                            total_functions += len(functions)
                            total_classes += len(classes)
                        # 可以继续添加其他语言的支持

                except Exception as e:
                    # 如果读取文件失败，跳过但不影响整体统计
                    logger.debug(f"无法读取文件 {file_path}: {str(e)}")
                    continue

            stats["total_files"] = total_files
            stats["total_functions"] = total_functions
            stats["total_classes"] = total_classes

            logger.info(f"📊 基本统计完成: {total_files} 文件, {total_functions} 函数, {total_classes} 类")

        except Exception as e:
            logger.warning(f"获取基本文件统计失败: {str(e)}")

        return stats

    def _enhance_metadata_with_stats(self, metadata: Dict[str, Any], analysis_dir: Path) -> Optional[Dict[str, Any]]:
        """增强元数据，添加统计信息"""
        try:
            # 尝试从analysis.json获取local_path
            analysis_file = analysis_dir / "analysis.json"
            if analysis_file.exists():
                with open(analysis_file, "r", encoding="utf-8") as f:
                    analysis_data = json.load(f)
                    local_path = analysis_data.get("local_path")

                    if local_path:
                        # 获取基本统计信息
                        basic_stats = self._get_basic_file_stats(Path(local_path))

                        # 更新元数据中的统计信息
                        if basic_stats["total_files"] > 0:
                            metadata["statistics"].update(basic_stats)
                            logger.info(f"📊 更新了 {metadata.get('analysis_id', 'Unknown')} 的统计信息")
                            return metadata

            return None

        except Exception as e:
            logger.warning(f"增强元数据失败: {str(e)}")
            return None

    def _generate_analysis_id(self, repo_info: Dict[str, Any]) -> str:
        """生成分析结果的唯一ID（使用仓库名）"""
        full_name = repo_info.get("full_name", "unknown")
        if "/" in full_name:
            # 从 "owner/repo" 中提取 "repo"
            repo_name = full_name.split("/")[-1]
        else:
            repo_name = full_name
        return repo_name

    def _create_analysis_directory(self, analysis_id: str) -> Path:
        """创建分析结果目录"""
        analysis_dir = self.base_path / analysis_id
        analysis_dir.mkdir(exist_ok=True)
        return analysis_dir

    def save_analysis_result(self, shared_data: Dict[str, Any]) -> str:
        """
        保存分析结果

        Args:
            shared_data: 包含完整分析结果的共享数据

        Returns:
            分析结果文件路径
        """
        try:
            # 生成分析ID
            analysis_id = self._generate_analysis_id(shared_data.get("repo_info", {}))
            analysis_dir = self._create_analysis_directory(analysis_id)

            # 保存JSON格式（过滤不可序列化的对象）
            json_path = analysis_dir / "analysis.json"
            serializable_data = self._make_serializable(shared_data)
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(serializable_data, f, ensure_ascii=False, indent=2)

            # 生成Markdown格式
            markdown_path = analysis_dir / "analysis.md"
            markdown_content = self._generate_markdown_report(shared_data)
            with open(markdown_path, "w", encoding="utf-8") as f:
                f.write(markdown_content)

            # 保存元数据
            metadata_path = analysis_dir / "metadata.json"
            metadata = self._generate_metadata(shared_data, analysis_id)
            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)

            # 更新索引
            self._update_index(metadata)

            logger.info(f"Analysis result saved to {analysis_dir}")
            return str(markdown_path)

        except Exception as e:
            import traceback

            logger.error(f"Detailed error in save_analysis_result: {traceback.format_exc()}")
            raise ResultStorageError(f"Failed to save analysis result: {str(e)}")

    def _make_serializable(self, data: Any) -> Any:
        """
        递归地将数据转换为JSON可序列化的格式
        过滤掉函数、类实例等不可序列化的对象
        """
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                # 跳过函数对象和其他不可序列化的对象
                if callable(value):
                    continue
                try:
                    result[key] = self._make_serializable(value)
                except (TypeError, ValueError):
                    # 如果无法序列化，跳过这个键值对
                    logger.warning(f"Skipping non-serializable key: {key}")
                    continue
            return result
        elif isinstance(data, (list, tuple)):
            result = []
            for item in data:
                try:
                    result.append(self._make_serializable(item))
                except (TypeError, ValueError):
                    # 跳过不可序列化的项
                    continue
            return result
        elif isinstance(data, (str, int, float, bool, type(None))):
            return data
        else:
            # 对于其他类型，尝试转换为字符串
            try:
                # 测试是否可以JSON序列化
                json.dumps(data)
                return data
            except (TypeError, ValueError):
                # 如果不能序列化，转换为字符串表示
                return str(data)

    def _generate_markdown_report(self, shared_data: Dict[str, Any]) -> str:
        """生成Markdown格式的分析报告"""
        repo_info = shared_data.get("repo_info", {})
        code_analysis = shared_data.get("code_analysis", [])

        # 构建Markdown内容
        md_lines = []

        # 标题和基本信息
        repo_name = repo_info.get("full_name", "Unknown Repository")
        md_lines.append(f"# {repo_name} - 代码分析报告")
        md_lines.append("")

        # 仓库信息
        md_lines.append("## 仓库信息")
        md_lines.append("")
        md_lines.append(f"- **描述**: {repo_info.get('description', 'N/A')}")
        md_lines.append(f"- **主要语言**: {repo_info.get('language', 'N/A')}")
        md_lines.append(f"- **创建时间**: {repo_info.get('created_at', 'N/A')}")
        md_lines.append(f"- **更新时间**: {repo_info.get('updated_at', 'N/A')}")
        md_lines.append(f"- **Stars**: {repo_info.get('stars', 0)}")
        md_lines.append(f"- **Forks**: {repo_info.get('forks', 0)}")
        md_lines.append("")

        # 语言统计
        languages = repo_info.get("languages", {})
        if languages and isinstance(languages, dict):
            md_lines.append("### 语言分布")
            md_lines.append("")

            # 安全地计算总字节数，只包含数字类型的值
            numeric_languages = {k: v for k, v in languages.items() if isinstance(v, (int, float))}
            total_bytes = sum(numeric_languages.values()) if numeric_languages else 0

            if numeric_languages:
                for lang, bytes_count in sorted(numeric_languages.items(), key=lambda x: x[1], reverse=True):
                    percentage = (bytes_count / total_bytes) * 100 if total_bytes > 0 else 0
                    md_lines.append(f"- **{lang}**: {percentage:.1f}% ({bytes_count:,} bytes)")
            else:
                # 如果没有数字类型的语言数据，显示原始数据
                for lang, value in languages.items():
                    md_lines.append(f"- **{lang}**: {value}")
            md_lines.append("")

        # 分析统计
        total_functions = sum(len(file_analysis.get("functions", [])) for file_analysis in code_analysis)
        total_classes = sum(len(file_analysis.get("classes", [])) for file_analysis in code_analysis)

        md_lines.append("## 分析统计")
        md_lines.append("")
        md_lines.append(f"- **分析文件数**: {len(code_analysis)}")
        md_lines.append(f"- **函数总数**: {total_functions}")
        md_lines.append(f"- **类总数**: {total_classes}")
        md_lines.append(f"- **分析时间**: {shared_data.get('analysis_time', 'N/A')}")
        md_lines.append("")

        # 详细分析结果
        md_lines.append("## 详细分析结果")
        md_lines.append("")

        for file_analysis in code_analysis:
            file_path = file_analysis.get("file_path", "Unknown File")
            md_lines.append(f"### {file_path}")
            md_lines.append("")

            # 函数
            functions = file_analysis.get("functions", [])
            if functions:
                md_lines.append("#### 函数")
                md_lines.append("")
                for func in functions:
                    md_lines.append(f"##### {func.get('title', 'Unknown Function')}")
                    md_lines.append("")
                    md_lines.append(f"**描述**: {func.get('description', 'N/A')}")
                    md_lines.append("")
                    md_lines.append(f"**位置**: {func.get('source', 'N/A')}")
                    md_lines.append("")
                    md_lines.append(f"**语言**: {func.get('language', 'N/A')}")
                    md_lines.append("")
                    md_lines.append("**代码**:")
                    md_lines.append("")
                    md_lines.append(f"```{func.get('language', '')}")
                    md_lines.append(func.get("code", ""))
                    md_lines.append("```")
                    md_lines.append("")

            # 类
            classes = file_analysis.get("classes", [])
            if classes:
                md_lines.append("#### 类")
                md_lines.append("")
                for cls in classes:
                    md_lines.append(f"##### {cls.get('title', 'Unknown Class')}")
                    md_lines.append("")
                    md_lines.append(f"**描述**: {cls.get('description', 'N/A')}")
                    md_lines.append("")
                    md_lines.append(f"**位置**: {cls.get('source', 'N/A')}")
                    md_lines.append("")
                    md_lines.append(f"**语言**: {cls.get('language', 'N/A')}")
                    md_lines.append("")
                    md_lines.append("**代码**:")
                    md_lines.append("")
                    md_lines.append(f"```{cls.get('language', '')}")
                    md_lines.append(cls.get("code", ""))
                    md_lines.append("```")
                    md_lines.append("")

        return "\n".join(md_lines)

    def _generate_metadata(self, shared_data: Dict[str, Any], analysis_id: str) -> Dict[str, Any]:
        """生成元数据"""
        repo_info = shared_data.get("repo_info", {})
        code_analysis = shared_data.get("code_analysis", [])

        return {
            "analysis_id": analysis_id,
            "repo_url": shared_data.get("repo_url", ""),
            "repo_name": repo_info.get("full_name", "Unknown"),
            "analysis_time": shared_data.get("analysis_time", datetime.now().isoformat()),
            "status": shared_data.get("status", "completed"),
            "statistics": {
                "total_files": len(code_analysis) if isinstance(code_analysis, list) else 0,
                "total_functions": self._safe_count_items(code_analysis, "functions"),
                "total_classes": self._safe_count_items(code_analysis, "classes"),
                "languages": repo_info.get("languages", {}) if isinstance(repo_info.get("languages"), dict) else {},
                "main_language": repo_info.get("language", "") if isinstance(repo_info.get("language"), str) else "",
            },
            "created_at": datetime.now().isoformat(),
        }

    def _safe_count_items(self, code_analysis: Any, item_type: str) -> int:
        """安全地计算代码分析中的项目数量"""
        try:
            if not isinstance(code_analysis, list):
                return 0

            total = 0
            for file_analysis in code_analysis:
                if isinstance(file_analysis, dict):
                    items = file_analysis.get(item_type, [])
                    if isinstance(items, list):
                        total += len(items)
            return total
        except Exception as e:
            logger.warning(f"Error counting {item_type}: {str(e)}")
            return 0

    def _update_index(self, metadata: Dict[str, Any]):
        """更新索引，确保同一个仓库只保留最新记录"""
        analysis_id = metadata.get("analysis_id")
        repo_name = metadata.get("repo_name")

        # 移除同一个仓库的旧记录
        self.index["analyses"] = [
            analysis
            for analysis in self.index["analyses"]
            if analysis.get("analysis_id") != analysis_id and analysis.get("repo_name") != repo_name
        ]

        # 添加新记录
        self.index["analyses"].append(metadata)

        # 按时间排序，最新的在前
        self.index["analyses"].sort(key=lambda x: x.get("created_at", ""), reverse=True)

        # 保存索引
        self._save_index()

    def get_analysis_list(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取分析结果列表"""
        # 清理重复记录
        self._cleanup_duplicates()
        return self.index["analyses"][:limit]

    def _cleanup_duplicates(self):
        """清理重复的分析记录，保留最新的"""
        seen_repos = {}
        unique_analyses = []

        # 按时间排序，最新的在前
        sorted_analyses = sorted(self.index["analyses"], key=lambda x: x.get("created_at", ""), reverse=True)

        for analysis in sorted_analyses:
            repo_name = analysis.get("repo_name", "")
            analysis_id = analysis.get("analysis_id", "")

            # 标准化仓库名（转换为小写进行比较）
            normalized_repo_name = repo_name.lower() if repo_name else ""

            # 使用标准化的仓库名作为唯一标识
            if normalized_repo_name and normalized_repo_name not in seen_repos:
                seen_repos[normalized_repo_name] = True
                unique_analyses.append(analysis)
            elif not normalized_repo_name and analysis_id:
                # 如果没有仓库名，使用analysis_id作为备用标识
                existing_ids = [a.get("analysis_id") for a in unique_analyses]
                if analysis_id not in existing_ids:
                    unique_analyses.append(analysis)

        # 如果发现重复记录，更新索引
        if len(unique_analyses) != len(self.index["analyses"]):
            logger.info(f"Cleaned up duplicates: {len(self.index['analyses'])} -> {len(unique_analyses)}")
            self.index["analyses"] = unique_analyses
            self._save_index()

    def get_analysis_by_id(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取分析结果"""
        try:
            analysis_dir = self.base_path / analysis_id
            if not analysis_dir.exists():
                logger.warning(f"Analysis directory not found: {analysis_id}")
                return None

            # 优先使用新的文件结构
            repo_info_path = analysis_dir / "repo_info.json"
            analysis_report_path = analysis_dir / "analysis_report.md"
            metadata_path = analysis_dir / "metadata.json"

            # 如果新文件结构存在，使用新结构
            if repo_info_path.exists() and analysis_report_path.exists():
                return self._load_new_format(analysis_id, analysis_dir)

            # 如果只有 repo_info.json，创建基本结果
            if repo_info_path.exists():
                return self._load_minimal_format(analysis_id, analysis_dir)

            # 否则使用旧的文件结构
            json_path = analysis_dir / "analysis.json"
            if json_path.exists():
                return self._load_old_format(analysis_id, analysis_dir)

            logger.warning(f"No valid analysis files found for: {analysis_id}")
            return None

        except Exception as e:
            logger.error(f"Failed to load analysis {analysis_id}: {str(e)}")

        return None

    def _load_new_format(self, analysis_id: str, analysis_dir: Path) -> Dict[str, Any]:
        """加载新格式的分析结果"""
        repo_info_path = analysis_dir / "repo_info.json"
        analysis_report_path = analysis_dir / "analysis_report.md"
        metadata_path = analysis_dir / "metadata.json"

        # 读取仓库信息
        with open(repo_info_path, "r", encoding="utf-8") as f:
            repo_info = json.load(f)

        # 读取分析报告
        with open(analysis_report_path, "r", encoding="utf-8") as f:
            analysis_report = f.read()

        # 解析分析报告
        analysis_items = self._parse_analysis_report(analysis_report)

        # 读取元数据（如果存在）
        statistics = {}
        analysis_time = None
        if metadata_path.exists():
            try:
                with open(metadata_path, "r", encoding="utf-8") as f:
                    metadata = json.load(f)
                statistics = metadata.get("statistics", {})
                analysis_time = metadata.get("created_at")

                # 如果统计信息为空，尝试重新计算
                if statistics.get("total_files", 0) == 0:
                    enhanced_metadata = self._enhance_metadata_with_stats(metadata, analysis_dir)
                    if enhanced_metadata:
                        statistics = enhanced_metadata.get("statistics", statistics)

            except Exception as e:
                logger.warning(f"Failed to load metadata for {analysis_id}: {str(e)}")

        # 构建返回数据
        return {
            "analysis_id": analysis_id,
            "repo_info": repo_info,
            "code_analysis": [{"analysis_items": analysis_items}],
            "statistics": statistics,
            "analysis_time": analysis_time,
        }

    def _load_minimal_format(self, analysis_id: str, analysis_dir: Path) -> Dict[str, Any]:
        """加载最小格式的分析结果（只有 repo_info.json）"""
        repo_info_path = analysis_dir / "repo_info.json"
        metadata_path = analysis_dir / "metadata.json"

        # 读取仓库信息
        with open(repo_info_path, "r", encoding="utf-8") as f:
            repo_info = json.load(f)

        # 读取元数据（如果存在）
        statistics = {}
        analysis_time = None
        if metadata_path.exists():
            try:
                with open(metadata_path, "r", encoding="utf-8") as f:
                    metadata = json.load(f)
                statistics = metadata.get("statistics", {})
                analysis_time = metadata.get("created_at")
            except Exception as e:
                logger.warning(f"Failed to load metadata for {analysis_id}: {str(e)}")

        # 如果没有统计信息，从 repo_info 中提取语言信息
        if not statistics and "languages" in repo_info:
            statistics = {
                "total_files": 0,
                "total_functions": 0,
                "total_classes": 0,
                "languages": repo_info["languages"],
            }

        # 构建返回数据
        return {
            "analysis_id": analysis_id,
            "repo_info": repo_info,
            "code_analysis": [],  # 空的代码分析结果
            "statistics": statistics,
            "analysis_time": analysis_time,
            "status": "incomplete",  # 标记为不完整
            "message": "分析未完成或数据不完整",
        }

    def _parse_analysis_report(self, report_content: str) -> List[Dict[str, Any]]:
        """解析分析报告，按照 TITLE、DESCRIPTION、SOURCE、LANGUAGE、CODE 格式"""
        items = []
        sections = report_content.split("----------------------------------------")

        for section in sections:
            section = section.strip()
            if not section:
                continue

            item = {}
            lines = section.split("\n")
            current_field = None
            current_content = []

            for line in lines:
                # 对于代码字段，保持原始行（包括缩进），对其他字段去除首尾空白
                original_line = line
                stripped_line = line.strip()

                if stripped_line.startswith("TITLE:"):
                    if current_field and current_content:
                        item[current_field.lower()] = "\n".join(current_content).strip()
                    current_field = "TITLE"
                    current_content = [stripped_line[6:].strip()]
                elif stripped_line.startswith("DESCRIPTION:"):
                    if current_field and current_content:
                        item[current_field.lower()] = "\n".join(current_content).strip()
                    current_field = "DESCRIPTION"
                    current_content = [stripped_line[12:].strip()]
                elif stripped_line.startswith("SOURCE:"):
                    if current_field and current_content:
                        item[current_field.lower()] = "\n".join(current_content).strip()
                    current_field = "SOURCE"
                    current_content = [stripped_line[7:].strip()]
                elif stripped_line.startswith("LANGUAGE:"):
                    if current_field and current_content:
                        item[current_field.lower()] = "\n".join(current_content).strip()
                    current_field = "LANGUAGE"
                    current_content = [stripped_line[9:].strip()]
                elif stripped_line.startswith("CODE:"):
                    if current_field and current_content:
                        item[current_field.lower()] = "\n".join(current_content).strip()
                    current_field = "CODE"
                    current_content = []
                elif stripped_line.startswith("```") and current_field == "CODE":
                    # 跳过代码块标记
                    continue
                elif current_field:
                    # 对于CODE字段，使用原始行保持缩进；对其他字段使用stripped行
                    if current_field == "CODE":
                        current_content.append(original_line)
                    else:
                        current_content.append(stripped_line)

            # 添加最后一个字段
            if current_field and current_content:
                if current_field == "CODE":
                    # 只移除代码块标记，保持原始缩进和空行
                    code_lines = [l for l in current_content if not l.strip().startswith("```")]
                    # 移除开头和结尾的空行，但保持中间的空行和缩进
                    while code_lines and not code_lines[0].strip():
                        code_lines.pop(0)
                    while code_lines and not code_lines[-1].strip():
                        code_lines.pop()
                    item[current_field.lower()] = "\n".join(code_lines)
                else:
                    item[current_field.lower()] = "\n".join(current_content).strip()

            if item:
                items.append(item)

        return items

    def _load_old_format(self, analysis_id: str, analysis_dir: Path) -> Dict[str, Any]:
        """加载旧格式的分析结果"""
        json_path = analysis_dir / "analysis.json"
        metadata_path = analysis_dir / "metadata.json"

        # 读取主要分析数据
        with open(json_path, "r", encoding="utf-8") as f:
            analysis_data = json.load(f)

        # 读取元数据（包含统计信息）
        if metadata_path.exists():
            try:
                with open(metadata_path, "r", encoding="utf-8") as f:
                    metadata = json.load(f)

                # 合并统计信息
                if "statistics" in metadata:
                    analysis_data["statistics"] = metadata["statistics"]

                # 添加其他有用的元数据
                analysis_data["analysis_time"] = metadata.get("created_at")
                analysis_data["analysis_id"] = metadata.get("analysis_id", analysis_id)

            except Exception as e:
                logger.warning(f"Failed to load metadata for {analysis_id}: {str(e)}")

        # 处理代码分析数据，确保格式正确
        if "code_analysis" in analysis_data:
            analysis_data["code_analysis"] = self._process_code_analysis(analysis_data["code_analysis"])

        # 确保仓库信息格式正确
        if "repo_info" in analysis_data:
            analysis_data["repo_info"] = self._process_repo_info(analysis_data["repo_info"])

        return analysis_data

    def _process_code_analysis(self, code_analysis: Any) -> List[Dict[str, Any]]:
        """处理代码分析数据，确保格式正确"""
        if not isinstance(code_analysis, list):
            return []

        processed_analysis = []
        for file_analysis in code_analysis:
            if not isinstance(file_analysis, dict):
                continue

            # 确保有必要的字段
            processed_file = {
                "file_path": file_analysis.get("file_path", ""),
                "functions": [],
                "classes": [],
                "analysis_items": file_analysis.get("analysis_items", []),
            }

            # 处理 analysis_items，将其转换为 functions 和 classes
            analysis_items = file_analysis.get("analysis_items", [])
            if isinstance(analysis_items, list):
                for item in analysis_items:
                    if isinstance(item, dict):
                        # 根据标题或描述判断是函数还是类
                        title = item.get("title", "")
                        if "类" in title or "class" in title.lower():
                            processed_file["classes"].append(
                                {
                                    "title": item.get("title", ""),
                                    "description": item.get("description", ""),
                                    "source": item.get("source", ""),
                                    "language": item.get("language", ""),
                                    "code": item.get("code", ""),
                                }
                            )
                        else:
                            processed_file["functions"].append(
                                {
                                    "title": item.get("title", ""),
                                    "description": item.get("description", ""),
                                    "source": item.get("source", ""),
                                    "language": item.get("language", ""),
                                    "code": item.get("code", ""),
                                }
                            )

            processed_analysis.append(processed_file)

        return processed_analysis

    def _process_repo_info(self, repo_info: Any) -> Dict[str, Any]:
        """处理仓库信息，确保格式正确"""
        if not isinstance(repo_info, dict):
            return {}

        # 标准化仓库信息字段
        processed_info = {
            "full_name": repo_info.get("full_name", repo_info.get("name", "")),
            "name": repo_info.get("name", ""),
            "description": repo_info.get("description", ""),
            "language": repo_info.get("language", repo_info.get("primary_language", "")),
            "languages": repo_info.get("languages", {}),
            "stars": repo_info.get("stars", repo_info.get("stargazers_count", 0)),
            "forks": repo_info.get("forks", repo_info.get("forks_count", 0)),
            "watchers": repo_info.get("watchers", repo_info.get("watchers_count", 0)),
            "created_at": repo_info.get("created_at", ""),
            "updated_at": repo_info.get("updated_at", ""),
            "topics": repo_info.get("topics", []),
            "license": repo_info.get("license", ""),
            "url": repo_info.get("url", ""),
            "clone_url": repo_info.get("clone_url", ""),
            "readme": repo_info.get("readme", ""),
        }

        return processed_info

    def get_analysis_result(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """获取分析结果详情（别名方法）"""
        return self.get_analysis_by_id(analysis_id)

    def delete_analysis(self, analysis_id: str) -> bool:
        """删除分析结果及所有相关数据"""
        try:
            # 获取分析信息以确定仓库名
            analysis_info = self.get_analysis_by_id(analysis_id)
            repo_name = None

            if analysis_info:
                repo_name = analysis_info.get("repo_name") or analysis_info.get("repo_info", {}).get("name")

            # 如果没有找到仓库名，尝试从analysis_id推断（通常analysis_id就是repo_name）
            if not repo_name:
                repo_name = analysis_id

            deleted_items = []

            # 1. 删除分析结果目录
            analysis_dir = self.base_path / analysis_id
            if analysis_dir.exists():
                import shutil

                shutil.rmtree(analysis_dir)
                deleted_items.append(f"分析结果: {analysis_dir}")
                logger.info(f"Deleted analysis directory: {analysis_dir}")

            # 2. 删除仓库文件（如果存在）
            if repo_name:
                from ..utils.config import get_config

                config = get_config()

                # 删除克隆的仓库
                repo_path = Path(config.local_repo_path) / repo_name
                if repo_path.exists():
                    import shutil

                    shutil.rmtree(repo_path)
                    deleted_items.append(f"仓库文件: {repo_path}")
                    logger.info(f"Deleted repository: {repo_path}")

                # 删除向量数据库
                vectorstore_path = Path(config.vectorstore_path) / repo_name
                if vectorstore_path.exists():
                    import shutil

                    shutil.rmtree(vectorstore_path)
                    deleted_items.append(f"向量数据库: {vectorstore_path}")
                    logger.info(f"Deleted vectorstore: {vectorstore_path}")

            # 3. 从索引中移除
            self.index["analyses"] = [a for a in self.index["analyses"] if a.get("analysis_id") != analysis_id]
            self._save_index()
            deleted_items.append("索引记录")

            logger.info(f"Successfully deleted analysis {analysis_id}. Deleted items: {', '.join(deleted_items)}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete analysis {analysis_id}: {str(e)}")
            return False
