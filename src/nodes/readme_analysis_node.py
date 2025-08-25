"""
README分析和生成节点 - 对GitHub仓库的README进行深度分析和完善
Design: AsyncNode, max_retries=2, wait=20
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
from pocketflow import AsyncNode

from ..utils.llm_parser import LLMParser
from ..utils.rag_api_client import RAGAPIClient
from ..utils.logger import logger
from ..utils.error_handler import LLMParsingError
from ..utils.config import get_config


class ReadmeAnalysisNode(AsyncNode):
    """README分析和生成节点"""

    def __init__(self):
        super().__init__(max_retries=2, wait=20)
        self.llm_parser = LLMParser()
        config = get_config()
        self.rag_client = RAGAPIClient(config.rag_base_url)

    async def prep_async(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """
        准备README分析所需的数据

        Data Access:
        - Read: shared.local_path, shared.repo_info, shared.code_analysis, shared.vectorstore_index
        """
        logger.info("=" * 60)
        logger.info("📋 阶段: README分析和生成 (ReadmeAnalysisNode)")
        shared["current_stage"] = "readme_analysis"

        local_path = shared.get("local_path")
        repo_info = shared.get("repo_info", {})
        code_analysis = shared.get("code_analysis", [])
        vectorstore_index = shared.get("vectorstore_index")

        if not local_path:
            logger.error("❌ README分析需要提供本地仓库路径")
            raise LLMParsingError("Local path is required for README analysis")

        local_path = Path(local_path)
        if not local_path.exists():
            logger.error(f"❌ 本地仓库路径不存在: {local_path}")
            raise LLMParsingError(f"Local repository path does not exist: {local_path}")

        # 查找现有的README文件
        existing_readme = self._find_existing_readme(local_path)
        existing_readme_content = ""

        if existing_readme:
            try:
                with open(existing_readme, "r", encoding="utf-8") as f:
                    existing_readme_content = f.read()
                logger.info(f"📄 找到现有README文件: {existing_readme.name}")
            except Exception as e:
                logger.warning(f"⚠️ 读取README文件失败: {str(e)}")

        # 准备分析数据
        analysis_data = {
            "local_path": local_path,
            "repo_info": repo_info,
            "code_analysis": code_analysis,
            "vectorstore_index": vectorstore_index,
            "existing_readme_path": str(existing_readme) if existing_readme else None,
            "existing_readme_content": existing_readme_content,
            "readme_quality": self._assess_readme_quality(existing_readme_content),
        }

        logger.info(f"🔍 准备分析README: 现有内容长度={len(existing_readme_content)}")
        return analysis_data

    def _find_existing_readme(self, repo_path: Path) -> Optional[Path]:
        """查找现有的README文件"""
        readme_patterns = [
            "README.md",
            "readme.md",
            "Readme.md",
            "README.MD",
            "README.txt",
            "readme.txt",
            "README.rst",
            "readme.rst",
            "README",
            "readme",
        ]

        for pattern in readme_patterns:
            readme_path = repo_path / pattern
            if readme_path.exists() and readme_path.is_file():
                return readme_path

        return None

    def _assess_readme_quality(self, content: str) -> Dict[str, Any]:
        """评估README质量"""
        if not content:
            return {
                "quality_score": 0,
                "has_content": False,
                "word_count": 0,
                "sections": [],
                "needs_improvement": True,
                "improvement_reason": "没有README文件",
            }

        content = content.strip()
        word_count = len(content.split())
        lines = content.split("\n")

        # 检查常见的README章节
        sections = []
        section_patterns = [
            r"#.*(?:installation|安装)",
            r"#.*(?:usage|使用|用法)",
            r"#.*(?:features|功能|特性)",
            r"#.*(?:requirements|依赖|要求)",
            r"#.*(?:contributing|贡献)",
            r"#.*(?:license|许可|授权)",
            r"#.*(?:documentation|文档)",
            r"#.*(?:examples|示例|例子)",
        ]

        import re

        for line in lines:
            for pattern in section_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    sections.append(line.strip())
                    break

        # 质量评分逻辑
        quality_score = 0
        if word_count > 50:
            quality_score += 30
        if word_count > 200:
            quality_score += 20
        if len(sections) >= 3:
            quality_score += 30
        if len(sections) >= 5:
            quality_score += 20

        needs_improvement = quality_score < 70 or word_count < 100

        improvement_reason = ""
        if word_count < 50:
            improvement_reason = "内容过少，缺乏详细说明"
        elif word_count < 100:
            improvement_reason = "内容较少，需要更多详细信息"
        elif len(sections) < 3:
            improvement_reason = "缺少重要章节（如安装、使用说明等）"
        elif quality_score < 70:
            improvement_reason = "整体质量需要提升，缺少完整的项目说明"

        return {
            "quality_score": quality_score,
            "has_content": True,
            "word_count": word_count,
            "sections": sections,
            "needs_improvement": needs_improvement,
            "improvement_reason": improvement_reason,
        }

    async def exec_async(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行README分析和生成
        """
        try:
            repo_info = analysis_data["repo_info"]
            code_analysis = analysis_data["code_analysis"]
            existing_readme_content = analysis_data["existing_readme_content"]
            readme_quality = analysis_data["readme_quality"]
            vectorstore_index = analysis_data["vectorstore_index"]

            logger.info(f"🔍 开始README分析: 质量评分={readme_quality['quality_score']}")

            # 1. 获取项目上下文信息
            project_context = await self._get_project_context(repo_info, code_analysis, vectorstore_index)

            # 2. 生成或改进README
            if readme_quality["needs_improvement"]:
                logger.info(f"📝 需要改进README: {readme_quality['improvement_reason']}")

                if readme_quality["has_content"]:
                    # 改进现有README
                    new_readme_content = await self._improve_existing_readme(
                        existing_readme_content, project_context, repo_info, readme_quality
                    )
                    action_type = "improved"
                else:
                    # 生成全新README
                    new_readme_content = await self._generate_new_readme(project_context, repo_info)
                    action_type = "generated"
            else:
                logger.info("✅ 现有README质量良好，进行轻微优化")
                new_readme_content = await self._optimize_existing_readme(
                    existing_readme_content, project_context, repo_info
                )
                action_type = "optimized"

            return {
                "readme_content": new_readme_content,
                "action_type": action_type,
                "original_quality": readme_quality,
                "project_context": project_context,
                "success": True,
            }

        except Exception as e:
            logger.error(f"❌ README分析失败: {str(e)}")
            return {"readme_content": "", "action_type": "failed", "error": str(e), "success": False}

    async def _get_project_context(
        self, repo_info: Dict[str, Any], code_analysis: List[Dict[str, Any]], vectorstore_index: Optional[str]
    ) -> Dict[str, Any]:
        """获取项目上下文信息"""
        try:
            # 基础项目信息
            context = {
                "repo_name": repo_info.get("name", "Unknown"),
                "full_name": repo_info.get("full_name", ""),
                "description": repo_info.get("description", ""),
                "language": repo_info.get("language", ""),
                "topics": repo_info.get("topics", []),
                "license": repo_info.get("license", {}).get("name", "") if repo_info.get("license") else "",
                "stars": repo_info.get("stargazers_count", 0),
                "forks": repo_info.get("forks_count", 0),
            }

            # 从代码分析中提取关键信息
            if code_analysis:
                context.update(self._extract_code_insights(code_analysis))

            # 如果有向量存储，获取项目概览
            if vectorstore_index:
                project_overview = await self._get_project_overview_from_rag(vectorstore_index, context)
                context["project_overview"] = project_overview

            return context

        except Exception as e:
            logger.warning(f"⚠️ 获取项目上下文失败: {str(e)}")
            return {
                "repo_name": repo_info.get("name", "Unknown"),
                "description": repo_info.get("description", ""),
                "language": repo_info.get("language", ""),
            }

    def _extract_code_insights(self, code_analysis: List[Dict[str, Any]]) -> Dict[str, Any]:
        """从代码分析中提取关键洞察"""
        insights = {
            "total_files": len(code_analysis),
            "languages": set(),
            "main_components": [],
            "key_features": [],
            "architecture_patterns": [],
        }

        for file_analysis in code_analysis:
            # 收集编程语言
            if file_analysis.get("language"):
                insights["languages"].add(file_analysis["language"])

            # 分析关键组件
            analysis_items = file_analysis.get("analysis_items", [])
            for item in analysis_items:
                title = item.get("title", "")
                description = item.get("description", "")

                # 识别主要组件（类、主要函数等）
                if any(keyword in title.lower() for keyword in ["class", "main", "app", "server", "client", "manager"]):
                    insights["main_components"].append(
                        {
                            "name": title,
                            "description": description[:100] + "..." if len(description) > 100 else description,
                            "file": file_analysis.get("file_path", ""),
                        }
                    )

                # 识别架构模式
                if any(
                    pattern in description.lower()
                    for pattern in ["singleton", "factory", "observer", "mvc", "api", "rest"]
                ):
                    insights["architecture_patterns"].append(title)

        insights["languages"] = list(insights["languages"])
        insights["main_components"] = insights["main_components"][:10]  # 限制数量
        insights["architecture_patterns"] = list(set(insights["architecture_patterns"]))[:5]

        return insights

    async def _get_project_overview_from_rag(self, vectorstore_index: str, context: Dict[str, Any]) -> str:
        """使用RAG获取项目概览"""
        try:
            # 构建查询来获取项目概览
            queries = [
                f"{context['repo_name']} 项目概述 功能特性",
                f"{context['language']} 项目架构 设计模式",
                "主要功能 核心特性 使用场景",
                "安装配置 使用方法 示例",
            ]

            overview_parts = []
            for query in queries:
                try:
                    results = self.rag_client.search_knowledge(query=query, index_name=vectorstore_index, top_k=3)

                    for result in results:
                        doc = result.get("document", {})
                        content = doc.get("content", "")
                        if content and len(content) > 50:
                            overview_parts.append(content[:200] + "...")

                except Exception as e:
                    logger.warning(f"RAG查询失败: {query} - {str(e)}")
                    continue

            return "\n".join(overview_parts[:5]) if overview_parts else ""

        except Exception as e:
            logger.warning(f"⚠️ 获取项目概览失败: {str(e)}")
            return ""

    async def _generate_new_readme(self, project_context: Dict[str, Any], repo_info: Dict[str, Any]) -> str:
        """生成全新的README"""
        prompt = self._build_readme_generation_prompt(project_context, repo_info, mode="generate")

        try:
            response = await self.llm_parser._make_api_request(prompt)
            return response.strip()
        except Exception as e:
            logger.error(f"❌ 生成README失败: {str(e)}")
            return self._create_fallback_readme(project_context, repo_info)

    async def _improve_existing_readme(
        self,
        existing_content: str,
        project_context: Dict[str, Any],
        repo_info: Dict[str, Any],
        readme_quality: Dict[str, Any],
    ) -> str:
        """改进现有README"""
        prompt = self._build_readme_improvement_prompt(existing_content, project_context, repo_info, readme_quality)

        try:
            response = await self.llm_parser._make_api_request(prompt)
            return response.strip()
        except Exception as e:
            logger.error(f"❌ 改进README失败: {str(e)}")
            return existing_content  # 返回原内容作为备选

    async def _optimize_existing_readme(
        self, existing_content: str, project_context: Dict[str, Any], repo_info: Dict[str, Any]
    ) -> str:
        """优化现有README"""
        prompt = self._build_readme_optimization_prompt(existing_content, project_context, repo_info)

        try:
            response = await self.llm_parser._make_api_request(prompt)
            return response.strip()
        except Exception as e:
            logger.error(f"❌ 优化README失败: {str(e)}")
            return existing_content  # 返回原内容作为备选

    def _build_readme_generation_prompt(
        self, project_context: Dict[str, Any], repo_info: Dict[str, Any], mode: str = "generate"
    ) -> str:
        """构建README生成的prompt"""
        repo_name = project_context.get("repo_name", "Unknown")
        description = project_context.get("description", "")
        language = project_context.get("language", "")
        languages = project_context.get("languages", [])
        main_components = project_context.get("main_components", [])
        project_overview = project_context.get("project_overview", "")

        components_text = ""
        if main_components:
            components_text = "\n主要组件:\n" + "\n".join(
                [f"- {comp['name']}: {comp['description']}" for comp in main_components[:5]]
            )

        return f"""
你是一个专业的中文技术文档编写专家。请为GitHub项目 "{repo_name}" 生成一个完整、专业、详细的中文README.md文档。

项目信息:
- 项目名称: {repo_name}
- 项目描述: {description}
- 主要语言: {language}
- 支持语言: {', '.join(languages) if languages else language}
- Stars: {project_context.get('stars', 0)}
- Forks: {project_context.get('forks', 0)}
- 许可证: {project_context.get('license', 'Unknown')}

{components_text}

项目概览:
{project_overview}

请生成一个完整的中文README.md文档，包含以下章节：

1. **项目标题和徽章** - 包含项目名称、简短中文描述、相关徽章
2. **项目简介** - 用中文详细介绍项目的目的、特性和价值
3. **功能特性** - 用中文列出主要功能和特色
4. **快速开始** - 包含中文的安装、配置和基本使用步骤
5. **安装指南** - 详细的中文安装说明和依赖要求
6. **使用说明** - 详细的中文使用方法和示例代码
7. **API文档** - 如果适用，提供中文API接口说明
8. **配置说明** - 中文配置文件和环境变量说明
9. **示例** - 实际使用示例和代码片段（注释用中文）
10. **贡献指南** - 如何参与项目贡献的中文说明
11. **许可证** - 许可证信息
12. **联系方式** - 维护者信息和支持渠道

重要要求：
- **必须使用中文编写所有文档内容**
- 使用专业的中文技术文档写作风格
- 内容要详细、准确、实用
- 包含适当的代码示例和配置示例（代码注释用中文）
- 使用Markdown格式，包含适当的标题、列表、代码块
- 确保文档结构清晰，易于中文读者阅读和导航
- 根据项目的实际技术栈和架构特点定制中文内容
- 所有章节标题、说明文字、示例注释都必须是中文

请直接输出完整的中文README.md内容，不要包含任何解释性文字。
"""

    def _build_readme_improvement_prompt(
        self,
        existing_content: str,
        project_context: Dict[str, Any],
        repo_info: Dict[str, Any],
        readme_quality: Dict[str, Any],
    ) -> str:
        """构建README改进的prompt"""
        improvement_reason = readme_quality.get("improvement_reason", "")
        missing_sections = self._identify_missing_sections(existing_content)

        return f"""
你是一个专业的中文技术文档编写专家。请改进以下GitHub项目的README.md文档，生成中文版本。

项目信息:
- 项目名称: {project_context.get("repo_name", "Unknown")}
- 项目描述: {project_context.get("description", "")}
- 主要语言: {project_context.get("language", "")}

当前README质量评估:
- 质量评分: {readme_quality.get("quality_score", 0)}/100
- 改进原因: {improvement_reason}
- 缺少的章节: {', '.join(missing_sections) if missing_sections else '无'}

现有README内容:
```markdown
{existing_content}
```

项目技术信息:
{self._format_project_context_for_prompt(project_context)}

请改进这个README文档，要求：
1. **必须使用中文编写所有文档内容**
2. 保留现有的有价值内容，但翻译成中文
3. 补充缺失的重要章节（用中文）
4. 改进内容的详细程度和专业性（用中文表达）
5. 确保文档结构清晰完整
6. 添加必要的代码示例和使用说明（注释用中文）
7. 使用专业的中文技术文档写作风格
8. 所有章节标题、说明文字、示例注释都必须是中文
9. 如果原文是英文，请翻译成准确的中文技术术语

请直接输出改进后的完整中文README.md内容。
"""

    def _build_readme_optimization_prompt(
        self, existing_content: str, project_context: Dict[str, Any], repo_info: Dict[str, Any]
    ) -> str:
        """构建README优化的prompt"""
        return f"""
你是一个专业的中文技术文档编写专家。请对以下README.md文档进行优化和完善，输出中文版本。

项目信息:
- 项目名称: {project_context.get("repo_name", "Unknown")}
- 项目描述: {project_context.get("description", "")}

现有README内容:
```markdown
{existing_content}
```

请进行以下优化：
1. **必须使用中文编写所有文档内容**
2. 改进语言表达，使其更加专业和清晰（用中文）
3. 优化文档结构和格式
4. 补充必要的技术细节（用中文说明）
5. 确保代码示例的准确性（注释用中文）
6. 改进章节组织和导航
7. 如果原文是英文，请翻译成准确的中文技术术语
8. 所有章节标题、说明文字、示例注释都必须是中文

请直接输出优化后的完整中文README.md内容。
"""

    def _identify_missing_sections(self, content: str) -> List[str]:
        """识别缺失的README章节"""
        if not content:
            return ["所有章节"]

        content_lower = content.lower()
        missing = []

        required_sections = {
            "安装": ["install", "安装", "setup"],
            "使用": ["usage", "使用", "用法", "how to"],
            "功能": ["feature", "功能", "特性"],
            "示例": ["example", "示例", "例子"],
            "贡献": ["contribut", "贡献"],
            "许可": ["license", "许可", "授权"],
        }

        for section_name, keywords in required_sections.items():
            if not any(keyword in content_lower for keyword in keywords):
                missing.append(section_name)

        return missing

    def _format_project_context_for_prompt(self, context: Dict[str, Any]) -> str:
        """格式化项目上下文信息用于prompt"""
        lines = []

        if context.get("languages"):
            lines.append(f"编程语言: {', '.join(context['languages'])}")

        if context.get("main_components"):
            lines.append("主要组件:")
            for comp in context["main_components"][:5]:
                lines.append(f"  - {comp['name']}: {comp['description']}")

        if context.get("architecture_patterns"):
            lines.append(f"架构模式: {', '.join(context['architecture_patterns'])}")

        if context.get("project_overview"):
            lines.append(f"项目概览: {context['project_overview'][:300]}...")

        return "\n".join(lines) if lines else "无额外技术信息"

    def _create_fallback_readme(self, project_context: Dict[str, Any], repo_info: Dict[str, Any]) -> str:
        """创建备用README内容"""
        repo_name = project_context.get("repo_name", "Unknown Project")
        description = project_context.get("description", "")
        language = project_context.get("language", "")

        return f"""# {repo_name}

{description}

## 项目简介

这是一个基于 {language} 的项目。

## 功能特性

- 待补充功能特性
- 支持多种操作模式
- 提供完整的API接口

## 快速开始

### 环境要求

- {language} 运行环境
- 相关依赖包

### 安装步骤

```bash
# 克隆项目仓库
git clone <repository-url>
cd {repo_name.lower().replace(' ', '-')}

# 安装项目依赖
# 请根据项目实际情况添加安装命令
```

### 基本使用

```bash
# 运行项目
# 请根据项目实际情况添加使用示例
```

## 配置说明

请根据项目需要进行相应配置。

## 示例代码

```{language.lower()}
# 示例代码
# 请根据项目实际情况添加代码示例
```

## 贡献指南

欢迎参与项目贡献！请遵循以下步骤：

1. Fork 本项目
2. 创建功能分支
3. 提交更改
4. 发起 Pull Request

## 问题反馈

如有问题或建议，请提交 Issue。

## 许可证

本项目采用相应开源许可证，详情请查看 LICENSE 文件。
"""

    async def post_async(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """
        保存生成的README文件到结果目录

        Data Access:
        - Write: shared.enhanced_readme_path
        - Write: 本地磁盘文件 (enhanced_readme.md)
        """
        try:
            if not exec_res.get("success"):
                logger.error(f"❌ README分析失败: {exec_res.get('error', 'Unknown error')}")
                return "default"

            readme_content = exec_res.get("readme_content", "")
            action_type = exec_res.get("action_type", "unknown")

            if not readme_content:
                logger.warning("⚠️ 生成的README内容为空")
                return "default"

            # 获取仓库信息
            repo_info = prep_res["repo_info"]
            repo_name = repo_info.get("name", "unknown")

            # 创建仓库专用的结果目录
            from pathlib import Path

            repo_results_dir = Path("./data/results") / repo_name
            repo_results_dir.mkdir(parents=True, exist_ok=True)

            # 保存增强的README文件
            enhanced_readme_path = repo_results_dir / "enhanced_readme.md"

            with open(enhanced_readme_path, "w", encoding="utf-8") as f:
                f.write(readme_content)

            # 更新共享数据
            shared["enhanced_readme_path"] = str(enhanced_readme_path)
            shared["readme_action_type"] = action_type
            shared["readme_analysis_result"] = exec_res

            # 记录操作结果
            action_messages = {
                "generated": "生成了全新的README文档",
                "improved": "改进了现有的README文档",
                "optimized": "优化了现有的README文档",
                "failed": "README分析失败",
            }

            message = action_messages.get(action_type, f"完成了README {action_type}")
            logger.info(f"✅ {message}: {enhanced_readme_path}")

            # 保存分析元数据
            await self._save_readme_metadata(repo_results_dir, exec_res, prep_res)

            return "default"

        except Exception as e:
            logger.error(f"❌ 保存README文件失败: {str(e)}")
            return "default"

    async def _save_readme_metadata(self, results_dir: Path, exec_res: Dict[str, Any], prep_res: Dict[str, Any]):
        """保存README分析的元数据"""
        try:
            import json
            from datetime import datetime

            metadata = {
                "analysis_time": datetime.now().isoformat(),
                "action_type": exec_res.get("action_type", "unknown"),
                "original_quality": exec_res.get("original_quality", {}),
                "project_context": exec_res.get("project_context", {}),
                "readme_length": len(exec_res.get("readme_content", "")),
                "success": exec_res.get("success", False),
            }

            if exec_res.get("error"):
                metadata["error"] = exec_res["error"]

            metadata_path = results_dir / "readme_analysis_metadata.json"
            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)

            logger.info(f"📄 README分析元数据已保存: {metadata_path}")

        except Exception as e:
            logger.warning(f"⚠️ 保存README元数据失败: {str(e)}")
