import asyncio
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.nodes import GitHubInfoFetchNode


async def run_test():
    # Target GitHub repository (as requested)
    repo_url = "https://github.com/The-Pocket/PocketFlow/"

    # Shared storage as used by flows/nodes
    shared = {"repo_url": repo_url}

    # Create and run the node (AsyncNode)
    node = GitHubInfoFetchNode()
    condition = await node.run_async(shared)

    # Console output: brief and direct
    repo_info = shared.get("repo_info", {})
    full_name = repo_info.get("full_name", "unknown")

    print("=== GitHubInfoFetchNode 测试 ===")
    print(f"执行结果: {condition=='default'}")
    print(f"仓库名称: {full_name}")
    print(f"简介: {repo_info.get('description', '')}")
    print(
        "====== 统计信息 ======",
        f"\nstar={repo_info.get('stargazers_count', 0)}",
        f"\nfork={repo_info.get('forks_count', 0)}",
        f"\nwatch={repo_info.get('watchers_count', 0)}",
    )
    print(
        "====== 元信息 ======",
        f"\n主要语言={repo_info.get('primary_language', '未知')}",
        f"\n许可证={repo_info.get('license', '未知')}",
        f"\n默认分支={repo_info.get('default_branch', '')}",
        f"\n最近更新时间={repo_info.get('last_updated', '')}",
    )

    # 保存文件位置（与节点逻辑一致）
    results_path = Path(os.getenv("RESULTS_PATH", "./data/results"))
    repo_name = full_name.split("/")[-1] if "/" in full_name else full_name
    repo_info_file = results_path / repo_name / "repo_info.json"
    print(f"\n保存路径: {repo_info_file}")


if __name__ == "__main__":
    asyncio.run(run_test())
