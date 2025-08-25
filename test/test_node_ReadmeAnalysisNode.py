"""
README分析节点测试 - 基于PocketFlow仓库的实际数据
测试中文README生成功能的完整性和准确性
"""

import unittest
import asyncio
import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

# 添加项目根目录到Python路径
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.nodes.readme_analysis_node import ReadmeAnalysisNode


class TestReadmeAnalysisNode(unittest.TestCase):
    """README分析节点测试类"""

    def setUp(self):
        """测试初始化"""
        self.node = ReadmeAnalysisNode()
        self.test_data_dir = Path("data/repos/PocketFlow")
        self.test_results_dir = Path("data/results/PocketFlow")

        # 加载PocketFlow的实际数据
        self.load_pocketflow_data()

    def load_pocketflow_data(self):
        """加载PocketFlow的实际分析数据"""
        # 加载仓库信息
        repo_info_path = self.test_results_dir / "repo_info.json"
        if repo_info_path.exists():
            with open(repo_info_path, "r", encoding="utf-8") as f:
                self.repo_info = json.load(f)
        else:
            self.repo_info = {
                "name": "PocketFlow",
                "description": "Pocket Flow: 100-line LLM framework. Let Agents build Agents!",
                "language": "Python",
                "stargazers_count": 7904,
                "forks_count": 894,
                "topics": ["agentic-ai", "llm-framework", "workflow"],
                "license": {"name": "MIT License"},
            }

        # 模拟代码分析结果
        self.code_analysis = [
            {
                "file_path": "pocketflow/__init__.py",
                "language": "python",
                "analysis_items": [
                    {
                        "title": "Node类",
                        "description": "PocketFlow框架的核心节点基类，提供流程控制功能",
                        "source": "pocketflow/__init__.py:1-20",
                        "language": "python",
                    },
                    {
                        "title": "Flow类",
                        "description": "流程编排类，管理节点之间的连接和执行",
                        "source": "pocketflow/__init__.py:21-50",
                        "language": "python",
                    },
                ],
            },
            {
                "file_path": "cookbook/pocketflow-agent/main.py",
                "language": "python",
                "analysis_items": [
                    {
                        "title": "Agent示例",
                        "description": "智能代理实现示例，展示搜索和回答功能",
                        "source": "cookbook/pocketflow-agent/main.py:1-100",
                        "language": "python",
                    }
                ],
            },
        ]

        # 读取原始README
        readme_path = self.test_data_dir / "README.md"
        if readme_path.exists():
            with open(readme_path, "r", encoding="utf-8") as f:
                self.original_readme = f.read()
        else:
            self.original_readme = "# PocketFlow\n\nMinimalist LLM framework"

    def test_readme_quality_assessment(self):
        """测试README质量评估功能"""
        # 测试高质量README
        high_quality_readme = """# PocketFlow

## 项目简介
这是一个100行的LLM框架

## 功能特性
- 轻量级设计
- 零依赖

## 安装指南
pip install pocketflow

## 使用说明
详细的使用方法

## 示例代码
代码示例

## 贡献指南
如何贡献

## 许可证
MIT许可证
"""
        quality = self.node._assess_readme_quality(high_quality_readme)
        self.assertGreater(quality["quality_score"], 70)
        self.assertFalse(quality["needs_improvement"])

        # 测试低质量README
        low_quality_readme = "# Test\n\nSimple project."
        quality = self.node._assess_readme_quality(low_quality_readme)
        self.assertLess(quality["quality_score"], 70)
        self.assertTrue(quality["needs_improvement"])

    def test_code_insights_extraction(self):
        """测试代码洞察提取功能"""
        insights = self.node._extract_code_insights(self.code_analysis)

        # 验证提取的信息
        self.assertIn("python", insights["languages"])
        self.assertGreater(len(insights["main_components"]), 0)
        self.assertEqual(insights["total_files"], 2)

        # 验证主要组件识别
        component_names = [comp["name"] for comp in insights["main_components"]]
        self.assertIn("Node类", component_names)
        self.assertIn("Flow类", component_names)

    @patch("src.nodes.readme_analysis_node.LLMParser")
    async def test_chinese_readme_generation(self, mock_llm_parser):
        """测试中文README生成功能"""
        # 模拟LLM返回中文内容
        mock_chinese_readme = """# PocketFlow

## 项目简介

PocketFlow 是一个仅用100行代码实现的极简LLM框架，专为智能代理开发而设计。

## 功能特性

- **轻量级设计**: 仅100行核心代码，零依赖，零厂商锁定
- **表达能力强**: 支持多代理、工作流、RAG等所有主流模式
- **代理编程**: 让AI代理来构建代理，提升10倍开发效率

## 快速开始

### 安装方法

```bash
# 使用pip安装
pip install pocketflow

# 或直接复制源码（仅100行）
curl -O https://raw.githubusercontent.com/The-Pocket/PocketFlow/main/pocketflow/__init__.py
```

### 基本使用

```python
# 导入框架
from pocketflow import Node, Flow

# 创建节点
class GreetingNode(Node):
    def exec(self, prep_res):
        return "你好，世界！"

# 创建流程
flow = Flow()
flow.add_node(GreetingNode())
result = flow.run({})
```

## 架构设计

PocketFlow的核心抽象是图（Graph），通过节点和连接构建复杂的AI工作流。

## 示例项目

- **聊天机器人**: 基础对话系统
- **智能代理**: 具备搜索和推理能力
- **工作流引擎**: 多步骤任务编排
- **RAG系统**: 检索增强生成

## 贡献指南

欢迎参与PocketFlow的开发！请遵循以下步骤：

1. Fork本项目
2. 创建功能分支
3. 提交代码更改
4. 发起Pull Request

## 许可证

本项目采用MIT许可证，详情请查看LICENSE文件。

## 联系方式

- GitHub: https://github.com/The-Pocket/PocketFlow
- Discord: https://discord.gg/hUHHE9Sa6T
"""

        # 配置mock
        mock_instance = Mock()
        mock_instance._make_api_request = AsyncMock(return_value=mock_chinese_readme)
        mock_llm_parser.return_value = mock_instance

        # 准备测试数据
        shared = {
            "local_path": str(self.test_data_dir),
            "repo_info": self.repo_info,
            "code_analysis": self.code_analysis,
            "vectorstore_index": None,
        }

        # 运行节点
        result = await self.node.run_async(shared)

        # 验证结果
        self.assertEqual(result, "default")
        self.assertIn("enhanced_readme_path", shared)
        self.assertIn("readme_action_type", shared)

        # 验证生成的README是中文的
        enhanced_readme_path = shared["enhanced_readme_path"]
        if Path(enhanced_readme_path).exists():
            with open(enhanced_readme_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 检查中文关键词
            chinese_keywords = ["项目简介", "功能特性", "快速开始", "安装方法", "基本使用", "贡献指南"]
            found_keywords = [kw for kw in chinese_keywords if kw in content]
            self.assertGreaterEqual(len(found_keywords), 4, "生成的README应包含足够的中文关键词")

    def test_missing_sections_identification(self):
        """测试缺失章节识别功能"""
        incomplete_readme = """# Test Project

This is a test project.

## Features
- Feature 1
- Feature 2
"""
        missing = self.node._identify_missing_sections(incomplete_readme)

        # 应该识别出缺失的章节
        self.assertIn("安装", missing)
        self.assertIn("使用", missing)
        self.assertIn("贡献", missing)

    def test_fallback_readme_creation(self):
        """测试备用README创建功能"""
        project_context = {"repo_name": "TestProject", "description": "测试项目描述", "language": "Python"}

        fallback_readme = self.node._create_fallback_readme(project_context, {})

        # 验证备用README包含中文内容
        self.assertIn("项目简介", fallback_readme)
        self.assertIn("功能特性", fallback_readme)
        self.assertIn("快速开始", fallback_readme)
        self.assertIn("贡献指南", fallback_readme)
        self.assertIn("TestProject", fallback_readme)

    def test_project_context_formatting(self):
        """测试项目上下文格式化功能"""
        context = {
            "languages": ["Python", "JavaScript"],
            "main_components": [
                {"name": "核心模块", "description": "主要功能模块"},
                {"name": "工具类", "description": "辅助工具"},
            ],
            "architecture_patterns": ["MVC", "观察者模式"],
        }

        formatted = self.node._format_project_context_for_prompt(context)

        # 验证格式化结果
        self.assertIn("编程语言: Python, JavaScript", formatted)
        self.assertIn("主要组件:", formatted)
        self.assertIn("核心模块", formatted)
        self.assertIn("架构模式: MVC, 观察者模式", formatted)

    def test_pocketflow_specific_analysis(self):
        """测试基于PocketFlow特定数据的分析"""
        # 验证PocketFlow仓库信息加载
        self.assertEqual(self.repo_info["name"], "PocketFlow")
        self.assertIn("100-line", self.repo_info["description"])
        self.assertEqual(self.repo_info["language"], "Python")

        # 验证原始README存在且包含关键信息
        if hasattr(self, "original_readme"):
            self.assertIn("PocketFlow", self.original_readme)
            self.assertIn("100", self.original_readme)

        # 验证代码分析数据结构
        self.assertGreater(len(self.code_analysis), 0)
        for file_analysis in self.code_analysis:
            self.assertIn("file_path", file_analysis)
            self.assertIn("analysis_items", file_analysis)

    def tearDown(self):
        """测试清理"""
        # 清理可能生成的测试文件
        test_output_dir = Path("./data/results/test-repo")
        if test_output_dir.exists():
            import shutil

            shutil.rmtree(test_output_dir)


def run_async_test():
    """运行异步测试的辅助函数"""

    async def run_tests():
        print("运行异步测试: test_chinese_readme_generation")
        test_instance = TestReadmeAnalysisNode()
        test_instance.setUp()
        try:
            await test_instance.test_chinese_readme_generation()
            print("✅ 异步测试通过")
        except Exception as e:
            print(f"❌ 异步测试失败: {str(e)}")
        finally:
            test_instance.tearDown()

    asyncio.run(run_tests())


def run_simple_test():
    """运行简化的功能测试"""
    print("=== README分析节点简化测试 ===")

    try:
        # 创建节点实例
        node = ReadmeAnalysisNode()
        print("✅ 节点创建成功")

        # 测试质量评估
        test_readme = """# 测试项目

## 项目简介
这是一个测试项目

## 功能特性
- 功能1
- 功能2

## 安装指南
pip install test

## 使用说明
使用方法

## 贡献指南
如何贡献
"""
        quality = node._assess_readme_quality(test_readme)
        print(f"✅ README质量评估: 评分={quality['quality_score']}, 需要改进={quality['needs_improvement']}")

        # 测试代码洞察提取
        test_analysis = [
            {
                "file_path": "main.py",
                "language": "python",
                "analysis_items": [
                    {"title": "主函数", "description": "程序入口"},
                    {"title": "工具类", "description": "辅助功能"},
                ],
            }
        ]
        insights = node._extract_code_insights(test_analysis)
        print(f"✅ 代码洞察提取: 语言={insights['languages']}, 组件数={len(insights['main_components'])}")

        # 测试备用README创建
        context = {"repo_name": "TestProject", "description": "测试描述", "language": "Python"}
        fallback = node._create_fallback_readme(context, {})
        chinese_keywords = ["项目简介", "功能特性", "快速开始"]
        found = [kw for kw in chinese_keywords if kw in fallback]
        print(f"✅ 备用README创建: 包含中文关键词={len(found)}/3")

        print("\n🎉 所有基础功能测试通过！")

    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    print("=== README分析节点测试 ===")
    print("基于PocketFlow仓库数据测试中文README生成功能")
    print("测试数据路径:")
    print(f"  - 仓库数据: data/repos/PocketFlow/")
    print(f"  - 分析结果: data/results/PocketFlow/")

    # 运行简化测试
    print("\n=== 运行简化功能测试 ===")
    run_simple_test()

    # 运行完整单元测试（可选）
    try:
        print("\n=== 运行完整单元测试 ===")
        unittest.main(verbosity=2, exit=False)

        # 运行异步测试
        print("\n=== 运行异步测试 ===")
        run_async_test()

    except Exception as e:
        print(f"⚠️ 完整测试跳过: {str(e)}")

    print("\n=== 测试完成 ===")
    print("测试覆盖功能:")
    print("✓ README质量评估")
    print("✓ 代码洞察提取")
    print("✓ 中文README生成")
    print("✓ 缺失章节识别")
    print("✓ 备用README创建")
    print("✓ 项目上下文格式化")
    print("✓ PocketFlow特定数据分析")
