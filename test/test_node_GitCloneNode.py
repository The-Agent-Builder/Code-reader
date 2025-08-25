import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.nodes import GitCloneNode


async def run_test():
    # 目标 GitHub 仓库
    # repo_url = "https://github.com/The-Pocket/PocketFlow/"
    repo_url = "https://github.com/openai/CLIP"

    # 与流程一致的共享数据
    shared = {"repo_url": repo_url}

    # 创建并运行节点（遵循 AsyncNode 的运行方式）
    node = GitCloneNode()

    print("=== GitCloneNode 测试 ===")
    print(f"目标仓库: {repo_url}")

    try:
        condition = await node.run_async(shared)
        local_path_str = shared.get("local_path", "")
        local_path = Path(local_path_str) if local_path_str else None

        exists = bool(local_path and local_path.exists())
        is_git = bool(local_path and (local_path / ".git").exists())

        print(f"执行结果: {condition == 'default' and exists}")
        print(f"本地路径: {local_path_str}")
        print(f"路径已创建: {exists}")
        print(f"有效Git仓库: {is_git}")
        print(f"当前阶段: {shared.get('current_stage', '')}")

    except Exception as e:
        print("执行结果: False")
        print(f"错误信息: {e}")


if __name__ == "__main__":
    asyncio.run(run_test())
