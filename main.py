#!/usr/bin/env python3
"""
GitHub 代码仓库解析工具主程序
基于 PocketFlow 构建的智能代码分析平台
"""
import sys
import asyncio
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 加载配置
from src.utils.config import get_config
from src.utils.logger import logger

# 进度条相关
try:
    from tqdm import tqdm

    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False
    logger.warning("tqdm not available, progress bar will be disabled")


def check_environment():
    """检查环境配置"""
    try:
        config = get_config()
        logger.info("Environment configuration loaded successfully")
        # 只检查关键配置
        logger.info(f"LLM配置: 并发数={config.llm_max_concurrent}, 批次大小={config.llm_batch_size}")
        return True
    except Exception as e:
        logger.error(f"Environment configuration error: {str(e)}")
        return False


def create_directories():
    """创建必要的目录"""
    directories = ["data/repos", "data/results", "data/vectorstores", "data/cache/llm", "logs", "static", "templates"]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {directory}")


class ProgressTracker:
    """进度跟踪器"""

    def __init__(self):
        self.pbar = None
        self.current_stage = ""

    def start_analysis(self, total_files: int, repo_name: str):
        """开始分析，初始化进度条"""
        if TQDM_AVAILABLE:
            self.pbar = tqdm(
                total=total_files,
                desc=f"🔍 分析 {repo_name}",
                unit="文件",
                bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} 文件 [{elapsed}<{remaining}]",
            )
        else:
            logger.info(f"🔍 开始分析 {repo_name}，共 {total_files} 个文件")

    def update_progress(self, completed: int, current_file: str = ""):
        """更新进度"""
        if self.pbar:
            # 更新到当前完成数量
            self.pbar.n = completed
            if current_file:
                self.pbar.set_description(f"🔍 分析中: {current_file}")
            self.pbar.refresh()
        else:
            if current_file:
                logger.info(f"📄 正在分析: {current_file} ({completed}/{self.pbar.total if self.pbar else '?'})")

    def set_stage(self, stage: str):
        """设置当前阶段"""
        self.current_stage = stage
        if self.pbar:
            self.pbar.set_description(f"📋 {stage}")
        else:
            logger.info(f"📋 当前阶段: {stage}")

    def finish(self):
        """完成分析"""
        if self.pbar:
            self.pbar.set_description("✅ 分析完成")
            self.pbar.close()
        else:
            logger.info("✅ 分析完成")


# 全局进度跟踪器
progress_tracker = ProgressTracker()


async def analyze_repository_with_progress(repo_url: str, use_vectorization: bool = False):
    """带进度条的仓库分析函数"""
    from src.flows.analysis_flow import analyze_repository
    from src.utils.git_manager import GitManager
    from src.utils.config import get_config

    # 获取配置中的批处理大小
    config = get_config()
    batch_size = config.llm_batch_size

    # 提取仓库名
    repo_name = repo_url.split("/")[-1].replace(".git", "")

    logger.info(f"🚀 开始分析仓库: {repo_url}")

    try:
        # 预估文件数量（如果本地已有缓存）
        git_manager = GitManager()
        local_path = git_manager.get_local_path(repo_url)

        total_files = 0
        if local_path.exists():
            # 统计源码文件数量
            supported_extensions = {
                ".py",
                ".js",
                ".ts",
                ".java",
                ".cpp",
                ".c",
                ".h",
                ".hpp",
                ".cs",
                ".go",
                ".rs",
                ".php",
                ".rb",
                ".swift",
                ".kt",
                ".scala",
                ".ipynb",  # 添加 Jupyter Notebook 支持
            }
            ignore_dirs = {".git", "__pycache__", "node_modules", ".venv", "venv", "env"}

            for file_path in local_path.rglob("*"):
                if (
                    file_path.is_file()
                    and file_path.suffix.lower() in supported_extensions
                    and not any(ignore_dir in file_path.parts for ignore_dir in ignore_dirs)
                ):
                    total_files += 1

        if total_files > 0:
            progress_tracker.start_analysis(total_files, repo_name)

        # 执行分析
        result = await analyze_repository(
            repo_url=repo_url,
            use_vectorization=use_vectorization,
            batch_size=batch_size,
            progress_callback=progress_tracker.update_progress,
        )

        # 完成进度条
        progress_tracker.finish()

        if result.get("status") == "completed":
            logger.info("🎉 分析完成!")
            logger.info(f"📁 结果文件: {result.get('result_filepath')}")

            # 显示统计信息
            code_analysis = result.get("code_analysis", [])
            if code_analysis:
                total_items = sum(len(file_result.get("analysis_items", [])) for file_result in code_analysis)
                logger.info(f"📊 分析统计:")
                logger.info(f"  📄 分析文件数: {len(code_analysis)}")
                logger.info(f"  🔍 分析项总数: {total_items}")
        else:
            logger.error(f"❌ 分析失败: {result.get('error')}")

        return result

    except Exception as e:
        progress_tracker.finish()
        logger.error(f"❌ 分析过程中发生错误: {str(e)}")
        raise


async def test_analysis():
    """测试分析功能"""
    # 测试仓库URL
    test_repo = "https://github.com/The-Pocket/PocketFlow"

    logger.info(f"🧪 测试分析功能，仓库: {test_repo}")

    try:
        result = await analyze_repository_with_progress(
            repo_url=test_repo, use_vectorization=False  # 快速测试，不使用向量化
        )

        if result.get("status") == "completed":
            logger.info("✅ 测试分析完成!")
        else:
            logger.error(f"❌ 测试分析失败: {result.get('error')}")

    except Exception as e:
        logger.error(f"❌ 测试分析错误: {str(e)}")


def start_web_server():
    """启动Web服务器"""
    import uvicorn

    config = get_config()

    logger.info(f"Starting web server at http://{config.app_host}:{config.app_port}")

    uvicorn.run("src.api.main:app", host=config.app_host, port=config.app_port, reload=config.debug, log_level="info")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="GitHub 代码仓库解析工具")
    parser.add_argument(
        "--mode",
        choices=["web", "test", "analyze"],
        default="web",
        help="运行模式: web(启动Web服务), test(测试分析功能), analyze(命令行分析)",
    )
    parser.add_argument("--repo", type=str, help="要分析的仓库URL (analyze模式)")
    parser.add_argument("--vectorization", action="store_true", help="启用向量化")

    args = parser.parse_args()

    # 检查环境
    if not check_environment():
        sys.exit(1)

    # 创建目录
    create_directories()

    if args.mode == "web":
        # 启动Web服务器
        start_web_server()

    elif args.mode == "test":
        # 测试分析功能
        asyncio.run(test_analysis())

    elif args.mode == "analyze":
        # 命令行分析
        if not args.repo:
            logger.error("❌ 请提供 --repo URL 参数进行分析")
            sys.exit(1)

        async def run_analysis():
            from src.utils.config import get_config

            config = get_config()

            logger.info(f"🔍 命令行分析模式")
            logger.info(f"📋 参数配置:")
            logger.info(f"  🌐 仓库URL: {args.repo}")
            logger.info(f"  🔍 向量化: {'启用' if args.vectorization else '禁用'}")
            logger.info(f"  📦 批处理大小: {config.llm_batch_size} (来自配置文件)")

            result = await analyze_repository_with_progress(repo_url=args.repo, use_vectorization=args.vectorization)

            if result.get("status") == "completed":
                logger.info("🎉 命令行分析完成!")
                logger.info(f"📁 结果文件: {result.get('result_filepath')}")
            else:
                logger.error(f"❌ 命令行分析失败: {result.get('error')}")

        asyncio.run(run_analysis())


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        sys.exit(1)
