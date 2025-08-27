import asyncio
import sys
import os
from pathlib import Path
from typing import Optional
from unittest.mock import MagicMock

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# 首先创建一个简单的 dotenv 模块来读取 .env 文件
def load_dotenv_simple(dotenv_path='.env', override=False):
    """简单的 load_dotenv 实现，从 .env 文件读取环境变量"""
    if not os.path.exists(dotenv_path):
        return False

    try:
        with open(dotenv_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()

                    # 移除引号
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]

                    if override or key not in os.environ:
                        os.environ[key] = value
        return True
    except Exception as e:
        print(f"⚠️ 读取 .env 文件失败: {e}")
        return False

# 创建模拟的 dotenv 模块
class MockDotenv:
    @staticmethod
    def load_dotenv(dotenv_path=None, override=False):
        if dotenv_path is None:
            return load_dotenv_simple('.env', override)
        else:
            return load_dotenv_simple(dotenv_path, override)

# 先加载环境变量
print("📋 从 .env 文件加载环境变量...")
if load_dotenv_simple('.env', override=True):
    print("✅ 成功从 .env 文件加载环境变量")
else:
    print("⚠️ 无法从 .env 文件加载环境变量，使用默认值")

# 创建模拟的依赖模块来绕过导入问题
sys.modules['dotenv'] = MockDotenv()

# 模拟其他缺失的模块
mock_modules = [
    'aiohttp', 'openai', 'chromadb', 'requests', 'gitpython', 'git', 'jinja2',
    'sqlalchemy', 'sqlalchemy.ext', 'sqlalchemy.ext.declarative', 'sqlalchemy.orm',
    'pymysql', 'fastapi', 'uvicorn', 'pydantic'
]

for module in mock_modules:
    sys.modules[module] = MagicMock()

# 特殊处理 langchain 模块，需要更复杂的结构
langchain_mock = MagicMock()
langchain_mock.text_splitter = MagicMock()
langchain_mock.text_splitter.RecursiveCharacterTextSplitter = MagicMock()
langchain_mock.schema = MagicMock()
langchain_mock.schema.Document = MagicMock()
langchain_mock.vectorstores = MagicMock()
langchain_mock.vectorstores.Chroma = MagicMock()

sys.modules['langchain'] = langchain_mock
sys.modules['langchain.text_splitter'] = langchain_mock.text_splitter
sys.modules['langchain.schema'] = langchain_mock.schema
sys.modules['langchain.vectorstores'] = langchain_mock.vectorstores

# langchain_community 模块
langchain_community_mock = MagicMock()
langchain_community_mock.vectorstores = MagicMock()
langchain_community_mock.vectorstores.Chroma = MagicMock()
sys.modules['langchain_community'] = langchain_community_mock
sys.modules['langchain_community.vectorstores'] = langchain_community_mock.vectorstores

# langchain_openai 模块
langchain_openai_mock = MagicMock()
langchain_openai_mock.OpenAIEmbeddings = MagicMock()
sys.modules['langchain_openai'] = langchain_openai_mock

from src.flows.analysis_flow import analyze_repository

REPO_URL = "https://github.com/The-Pocket/PocketFlow/"


def on_progress(current_file: Optional[str] = None):
    """Simple progress callback used by CodeParsingBatchNode."""
    if current_file:
        print(f"[progress] parsing: {current_file}")


async def run_test_quick():
    """Run the QuickAnalysisFlow (skips vectorization)."""
    shared = await analyze_repository(
        REPO_URL,
        use_vectorization=False,  # quick mode: no vector store required
        batch_size=5,
        progress_callback=on_progress,
    )

    # Minimal, direct console output
    print("=== Analysis Flow (Quick) ===")
    print(f"repo: {REPO_URL}")
    print(f"status: {shared.get('status')}")
    print(f"stage: {shared.get('current_stage')}")
    print(f"files_analyzed: {len(shared.get('code_analysis', []))}")
    print(f"report: {shared.get('analysis_report_path', '')}")
    print(f"result_file: {shared.get('result_filepath', '')}")
    if shared.get("error"):
        print(f"error: {shared.get('error')}")


async def run_test_full():
    """Run the Full GitHubAnalysisFlow (includes vectorization/RAG)."""
    shared = await analyze_repository(
        REPO_URL,
        use_vectorization=True,
        batch_size=5,
        progress_callback=on_progress,
    )

    print("=== Analysis Flow (Full, with RAG) ===")
    print(f"repo: {REPO_URL}")
    print(f"status: {shared.get('status')}")
    print(f"stage: {shared.get('current_stage')}")
    print(f"vector_index: {shared.get('vectorstore_index', '')}")
    print(f"files_analyzed: {len(shared.get('code_analysis', []))}")
    print(f"report: {shared.get('analysis_report_path', '')}")
    print(f"result_file: {shared.get('result_filepath', '')}")
    if shared.get("error"):
        print(f"error: {shared.get('error')}")


if __name__ == "__main__":
    # Default to full flow to perform vectorization (RAG)
    asyncio.run(run_test_full())
