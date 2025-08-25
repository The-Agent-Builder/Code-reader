import asyncio
import json
import os
import sys
from pathlib import Path

# 确保可以从项目根目录导入 src 模块
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.nodes import VectorizeRepoNode  # noqa: E402


async def run_test():
    """
    参照 src/flows/analysis_flow.py 的处理方式，单独测试 VectorizeRepoNode。

    - 使用本地已存在的 GitHub 仓库副本：data/repos/PocketFlow/
    - 打印关键步骤与结果（中文、简洁）
    - 控制台输出将搭配项目内 logger 的中文日志，便于观察 RAG 构建全过程
    """

    # 指定本地仓库路径（相对路径更稳妥，与请求的绝对路径等价）
    repo_dir = Path(r"E:\Code\Agent1\p-test6\data\repos\PocketFlow")

    # 按照流程共享数据结构准备（analysis_flow 中节点链路的前置产物）
    shared = {
        "repo_url": "https://github.com/The-Pocket/PocketFlow/",  # 仅用于记录
        "local_path": str(repo_dir),
        # 至少需要 full_name，VectorizeRepoNode/Provider 用于生成索引名/本地兼容路径
        "repo_info": {
            "full_name": "The-Pocket/PocketFlow",
            "description": "PocketFlow 流程和节点库（测试向量化）",
        },
    }

    # 环境检查提示（不强制失败，仅提示）
    rag_url = os.getenv("RAG_BASE_URL", "")
    if not rag_url:
        print("[提示] 未检测到 RAG_BASE_URL 环境变量，运行测试前请在 .env 中配置并确保 /health 可访问。")

    print("=== VectorizeRepoNode 测试（参照 analysis_flow）===")
    print(f"目标本地仓库: {repo_dir}")
    print(f"仓库标识: {shared['repo_info']['full_name']}")
    print("—— 将开始向量化构建（RAG）——")

    node = VectorizeRepoNode()

    try:
        # 执行节点（内部会依次调用 prep_async/exec_async/post_async，并带有重试机制）
        condition = await node.run_async(shared)

        print("\n=== 构建结果摘要 ===")
        print(f"节点执行成功: {condition == 'default'}")
        print(f"RAG 索引名称: {shared.get('vectorstore_index', '')}")
        print(f"本地元数据路径: {shared.get('vectorstore_path', '')}/metadata.json")
        print(f"当前阶段: {shared.get('current_stage', '')}")

        # 读取本地元数据（由 Provider 写入），辅助观察构建详情
        meta_path = Path(shared.get("vectorstore_path", "")) / "metadata.json"
        if meta_path.exists():
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
                print("\n=== RAG 构建元数据（来自 metadata.json） ===")
                print(f"索引名称: {meta.get('index_name', '')}")
                print(f"文档总数: {meta.get('document_count', 0)}")
                print(f"处理文件数: {meta.get('processed_files', 0)}")
                print(f"RAG 服务地址: {meta.get('rag_api_url', '')}")
            except Exception as e:
                print(f"[警告] 读取元数据失败: {e}")
        else:
            print("[提示] 未找到本地元数据文件（可能使用远程 RAG 且未成功落地，或构建失败）。")

        print("\n=== 过程说明（简要）===")
        print("1) 健康检查：访问 RAG /health")
        print("2) 扫描源码：过滤非代码/忽略目录，提取 Python 函数/类或其它语言文本分块")
        print("3) 文档组装：包含标题/内容/语言/文件路径/元素类型/起止行号/难度/仓库名等元信息")
        print("4) 批量上传：首批创建索引，其余批次追加（每批约100条，含限流间隔）")
        print("5) 元数据落地：保存到 ./data/vectorstores/<repo_name>/metadata.json 便于调试")
        print("6) 流水线注册：shared.vectorstore_index/shared.vectorstore_path 供后续检索节点使用")

    except Exception as e:
        print("\n💥 向量化构建失败：")
        print(str(e))
        # 可选打印部分共享信息，帮助排查
        print("当前阶段:", shared.get("current_stage", ""))
        print("本地路径:", shared.get("local_path", ""))
        print("仓库标识:", shared.get("repo_info", {}).get("full_name", ""))


if __name__ == "__main__":
    asyncio.run(run_test())
