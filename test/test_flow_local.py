"""
测试本地文件夹分析流程
使用 CLIP 仓库进行测试
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 首先创建一个简单的 dotenv 模块来读取 .env 文件
import os
import sys
from unittest.mock import MagicMock

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
    'aiohttp', 'openai', 'langchain', 'langchain_community', 'langchain_openai',
    'chromadb', 'requests', 'gitpython', 'git', 'jinja2', 'sqlalchemy',
    'sqlalchemy.ext', 'sqlalchemy.ext.declarative', 'sqlalchemy.orm',
    'pymysql', 'fastapi', 'uvicorn', 'pydantic'
]

for module in mock_modules:
    sys.modules[module] = MagicMock()

# 现在尝试导入流程类
try:
    from src.flows.file_analysis_flow import (
        LocalFolderAnalysisFlow,
        analyze_local_folder,
        create_analysis_flow
    )
    from src.utils.logger import logger
    DEPENDENCIES_AVAILABLE = True
    print("✅ 成功导入流程类")
except ImportError as e:
    print(f"⚠️ 依赖导入失败: {e}")
    print("🔄 使用简化版本进行测试...")
    DEPENDENCIES_AVAILABLE = False

    # 简化版本的 logger
    class SimpleLogger:
        def info(self, msg): print(f"ℹ️ {msg}")
        def error(self, msg): print(f"❌ {msg}")
        def warning(self, msg): print(f"⚠️ {msg}")

    logger = SimpleLogger()


async def test_local_folder_analysis():
    """测试本地文件夹分析流程"""

    # 设置测试路径
    clip_repo_path = r"E:\Code\Agent1\Code-reader\data\repos\CLIP"

    logger.info("🧪 开始测试本地文件夹分析流程")
    logger.info(f"📁 测试仓库路径: {clip_repo_path}")

    # 验证路径存在
    if not os.path.exists(clip_repo_path):
        logger.error(f"❌ 测试仓库路径不存在: {clip_repo_path}")
        return False

    if not DEPENDENCIES_AVAILABLE:
        logger.error("❌ 依赖不可用，跳过测试")
        return False

    try:
        # 测试 1: 使用 LocalFolderAnalysisFlow 直接测试（跳过向量化以避免依赖问题）
        logger.info("\n" + "="*60)
        logger.info("🧪 测试 1: LocalFolderAnalysisFlow (跳过向量化)")
        logger.info("="*60)

        flow = LocalFolderAnalysisFlow(use_vectorization=False, batch_size=3)
        shared_data = {"local_folder_path": clip_repo_path}

        await flow.run_async(shared_data)

        if shared_data.get("status") == "completed":
            logger.info("✅ 测试 1 成功完成")
            logger.info(f"� 结果文件: {shared_data.get('result_filepath')}")
        else:
            logger.error("❌ 测试 1 失败")
            logger.error(f"错误信息: {shared_data.get('error', 'Unknown error')}")
            return False

        # 测试 2: 使用便捷函数 analyze_local_folder
        logger.info("\n" + "="*60)
        logger.info("🧪 测试 2: analyze_local_folder 便捷函数")
        logger.info("="*60)

        result_convenience = await analyze_local_folder(
            local_folder_path=clip_repo_path,
            use_vectorization=False,  # 为了快速测试，跳过向量化
            batch_size=3
        )

        if result_convenience.get("status") == "completed":
            logger.info("✅ 测试 2 成功完成")
            logger.info(f"� 结果文件: {result_convenience.get('result_filepath')}")
        else:
            logger.error("❌ 测试 2 失败")
            logger.error(f"错误信息: {result_convenience.get('error', 'Unknown error')}")
            return False

        # 测试 3: 使用工厂函数创建流程
        logger.info("\n" + "="*60)
        logger.info("🧪 测试 3: create_analysis_flow 工厂函数")
        logger.info("="*60)

        factory_flow = create_analysis_flow("local_quick", batch_size=3)
        shared_data_factory = {"local_folder_path": clip_repo_path}

        await factory_flow.run_async(shared_data_factory)

        if shared_data_factory.get("status") == "completed":
            logger.info("✅ 测试 3 成功完成")
            logger.info(f"� 结果文件: {shared_data_factory.get('result_filepath')}")
        else:
            logger.error("❌ 测试 3 失败")
            logger.error(f"错误信息: {shared_data_factory.get('error', 'Unknown error')}")
            return False

        logger.info("\n" + "="*60)
        logger.info("🎉 所有测试成功完成！")
        logger.info("="*60)

        return True

    except Exception as e:
        logger.error(f"❌ 测试过程中发生异常: {str(e)}")
        import traceback
        logger.error(f"详细错误信息:\n{traceback.format_exc()}")
        return False


async def test_error_handling():
    """测试错误处理"""
    logger.info("\n" + "="*60)
    logger.info("🧪 测试错误处理")
    logger.info("="*60)

    if not DEPENDENCIES_AVAILABLE:
        logger.error("❌ 依赖不可用，跳过错误处理测试")
        return False

    # 测试不存在的路径
    try:
        flow = LocalFolderAnalysisFlow(use_vectorization=False)
        shared_data = {"local_folder_path": "/nonexistent/path"}

        await flow.run_async(shared_data)

        if shared_data.get("status") == "failed":
            logger.info("✅ 错误处理测试成功 - 正确处理了不存在的路径")
        else:
            logger.error("❌ 错误处理测试失败 - 应该返回失败状态")
            return False

    except Exception as e:
        logger.info(f"✅ 错误处理测试成功 - 正确抛出异常: {str(e)}")

    # 测试空路径
    try:
        flow = LocalFolderAnalysisFlow(use_vectorization=False)
        shared_data = {"local_folder_path": ""}

        await flow.run_async(shared_data)

        if shared_data.get("status") == "failed":
            logger.info("✅ 空路径错误处理测试成功")
        else:
            logger.error("❌ 空路径错误处理测试失败")
            return False

    except Exception as e:
        logger.info(f"✅ 空路径错误处理测试成功 - 正确抛出异常: {str(e)}")

    return True


def progress_callback(completed: int, current_file: str):
    """进度回调函数"""
    logger.info(f"📊 进度更新: 已完成 {completed} 个文件，当前处理: {current_file}")


async def test_with_progress_callback():
    """测试带进度回调的分析"""
    logger.info("\n" + "="*60)
    logger.info("🧪 测试带进度回调的分析")
    logger.info("="*60)

    clip_repo_path = r"E:\Code\Agent1\Code-reader\data\repos\CLIP"

    if not DEPENDENCIES_AVAILABLE:
        logger.error("❌ 依赖不可用，跳过进度回调测试")
        return False

    try:
        result = await analyze_local_folder(
            local_folder_path=clip_repo_path,
            use_vectorization=False,  # 快速测试
            batch_size=2,
            progress_callback=progress_callback
        )

        if result.get("status") == "completed":
            logger.info("✅ 带进度回调的测试成功完成")
            return True
        else:
            logger.error("❌ 带进度回调的测试失败")
            return False

    except Exception as e:
        logger.error(f"❌ 带进度回调的测试异常: {str(e)}")
        return False


async def main():
    """主测试函数"""
    logger.info("🚀 开始本地文件夹分析流程测试")

    # 运行主要测试
    success1 = await test_local_folder_analysis()

    # 运行错误处理测试
    success2 = await test_error_handling()

    # 运行进度回调测试
    success3 = await test_with_progress_callback()

    if success1 and success2 and success3:
        logger.info("\n🎉 所有测试都成功完成！")
        return True
    else:
        logger.error("\n❌ 部分测试失败")
        return False


if __name__ == "__main__":
    # 运行测试
    success = asyncio.run(main())

    if success:
        print("\n✅ 测试成功完成")
        sys.exit(0)
    else:
        print("\n❌ 测试失败")
        sys.exit(1)