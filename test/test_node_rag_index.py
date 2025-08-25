import sys
import os
from typing import Any, Dict, List
from pathlib import Path

# 确保可以从项目根目录导入 src 模块
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv, find_dotenv

# 加载项目根目录的 .env（包含 RAG_BASE_URL 等），override=True 以覆盖现有环境变量
load_dotenv(find_dotenv(), override=True)

from src.utils.rag_api_client import RAGAPIClient  # noqa: E402


def _fmt(s: Any, max_len: int = 120) -> str:
    """将对象转为字符串并截断，便于控制台展示。"""
    try:
        text = str(s) if s is not None else ""
    except Exception:
        text = repr(s)
    text = text.replace("\n", " ")
    return text if len(text) <= max_len else text[: max_len - 1] + "…"


def _get(d: Dict[str, Any], keys: List[str], default: Any = "") -> Any:
    """从多种可能的键中取值，第一个存在的返回。"""
    for k in keys:
        if k in d and d[k] is not None:
            return d[k]
    return default


def _extract_title(item: Dict[str, Any]) -> str:
    # 兼容不同返回结构
    # 可能是直接的 'title'，或在 'metadata' 中
    title = _get(item, ["title"]) or _get(item.get("metadata", {}), ["title"])
    return str(title or "(无标题)")


def _extract_file_path(item: Dict[str, Any]) -> str:
    fp = (
        _get(item, ["file_path"]) or _get(item.get("metadata", {}), ["file_path"]) or _get(item, ["source", "path"], "")
    )
    return str(fp)


def _extract_language(item: Dict[str, Any]) -> str:
    lang = _get(item, ["language"]) or _get(item.get("metadata", {}), ["language"]) or ""
    return str(lang)


def _extract_content(item: Dict[str, Any]) -> str:
    # 常见字段 content/page_content/text
    return _get(item, ["content", "page_content", "text"], "")


def run_index_test(index_name: str, queries: List[str], top_k: int = 5) -> int:
    print("=== RAG 索引测试 ===")
    print(f"索引名称: {index_name}")

    base_url = os.getenv("RAG_BASE_URL", "").strip()
    if not base_url:
        print("[错误] 未设置 RAG_BASE_URL 环境变量，请在 .env 中配置。")
        return 2

    client = RAGAPIClient(base_url)

    # 健康检查
    print("[步骤] 1) 健康检查 -> /health")
    ok = client.check_health()
    print("[结果] RAG 服务可用" if ok else "[结果] RAG 服务不可用")
    if not ok:
        return 3

    # 执行查询
    print("\n[步骤] 2) 索引检索 /search")
    for qi, q in enumerate(queries, start=1):
        print(f"\n— 查询 {qi}: {q}")
        try:
            results = client.search_knowledge(query=q, index_name=index_name, vector_field="content", top_k=top_k)
        except Exception as e:
            print(f"[错误] 查询失败: {e}")
            continue

        if not results:
            print("[提示] 无检索结果（索引不存在/无匹配/服务返回空）。")
            continue

        # 展示前若干条
        for i, item in enumerate(results[:top_k], start=1):
            title = _extract_title(item)
            file_path = _extract_file_path(item)
            language = _extract_language(item)
            content = _extract_content(item)

            print(f"  {i}. 标题: {_fmt(title, 80)}")
            if file_path:
                print(f"     文件: {_fmt(file_path, 100)}")
            if language:
                print(f"     语言: {language}")
            if content:
                print(f"     摘要: {_fmt(content, 160)}")

    print("\n[步骤] 3) 完成")
    return 0


if __name__ == "__main__":
    # 默认索引与查询，可从命令行覆盖
    default_index = "document_20250815_02xi"
    index = sys.argv[1] if len(sys.argv) > 1 else default_index

    # 若命令行提供查询，使用之；否则使用一组通用的中文查询
    default_queries = [
        "项目介绍",
        "安装与使用",
        "主要模块",
    ]
    queries = sys.argv[2:] if len(sys.argv) > 2 else default_queries

    # 可通过环境变量调整 top_k
    try:
        top_k = int(os.getenv("RAG_TOP_K", "5"))
    except Exception:
        top_k = 5

    exit_code = run_index_test(index, queries, top_k=top_k)
    sys.exit(exit_code)
