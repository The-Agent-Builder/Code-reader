#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于远程 RAG API 的知识库构建测试（逐文件过程展示）
- 仓库示例：data/repos/CLIP/
- 仅打印中文过程说明；不会真正运行于此环境中
- 运行方式（本地）：python -m test.test_utils_rag_api_client
"""

import os
import sys
import asyncio
import json

from pathlib import Path

# 确保可以从 src 导入
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from utils.rag_api_client import RAGVectorStoreProvider  # type: ignore # noqa: E402


BASE_URL = os.getenv("RAG_BASE_URL", "http://nodeport.sensedeal.vip:32421")
REPO_DIR = PROJECT_ROOT / "data" / "repos" / "CLIP"
REPO_FULL_NAME = "openai/CLIP"  # 仅用于索引命名与元信息

# 与实现保持一致，用于区分“文档/代码”类别的简单规则
DOC_EXTS = {".md", ".mdx", ".rst", ".txt", ".adoc"}


async def run_test():
    print("🚀 远程 RAG API 知识库构建测试（逐文件预览）")
    print("仓库路径:", REPO_DIR)
    print("服务地址:", BASE_URL)

    if not REPO_DIR.exists():
        print("⚠️ 本地仓库目录不存在，请先在 data/repos/ 下准备 CLIP 仓库副本。")
        return

    # 实例化 Provider（远程 RAG API 方案）
    provider = RAGVectorStoreProvider(BASE_URL)

    # 健康检查（不强制退出，仅提示）
    ok = provider.rag_client.check_health()
    print("🔍 健康检查:", "通过" if ok else "未通过（请确认服务可用）")

    # 逐文件预扫描与元素提取（仅用于打印过程，不会提前提交）
    print("\n=== 逐文件预览（提取元素，仅打印） ===")
    total_docs = 0
    all_documents = []

    try:
        files = provider._get_code_files(REPO_DIR)  # 使用相同的文件过滤规则
        for idx, file_path in enumerate(sorted(files), 1):
            try:
                rel = str(file_path.relative_to(REPO_DIR))
            except Exception:
                rel = str(file_path)

            category = "文档" if file_path.suffix.lower() in DOC_EXTS else "代码"
            elements = provider.code_splitter.extract_code_elements(file_path)
            n = len(elements)
            total_docs += n

            # 组装完整文档结构，准备保存为 JSON
            for element in elements:
                if element.get("element_type") in ("function", "class"):
                    desired_title = element.get("element_name", element.get("title", ""))
                else:
                    desired_title = element.get("title") or element.get("element_name") or file_path.stem
                try:
                    file_rel_for_json = str(file_path.relative_to(REPO_DIR))
                except Exception:
                    file_rel_for_json = element.get("file_path", str(file_path))
                desired_category = "文档" if file_path.suffix.lower() in DOC_EXTS else "代码"
                doc = {
                    "title": desired_title,
                    "file": file_rel_for_json,
                    "content": element.get("content", ""),
                    "category": desired_category,
                    "language": element.get("language"),
                    "repo_name": REPO_FULL_NAME,
                    "start_line": element.get("start_line", 1),
                    "end_line": element.get("end_line", 1),
                }
                all_documents.append(doc)

            # 展示前两个标题示例（尽量取函数/类名）
            samples = []
            for e in elements[:2]:
                title = e.get("element_name") or e.get("title") or file_path.stem
                samples.append(title)

            sample_str = ", ".join(samples) if samples else "-"
            print(f"{idx:03d}. 📄 {rel} | 类别: {category} | 元素: {n} | 示例: {sample_str}")
    except Exception as e:
        print("❌ 预扫描阶段出错:", str(e))
        return

    # 保存所有 documents 为 JSON 到当前测试文件所在目录
    try:
        out_path = Path(__file__).parent / f"documents_{REPO_DIR.name}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(all_documents, f, ensure_ascii=False, indent=2)
        print(f"\n💾 已保存所有 documents 到: {out_path} (共 {len(all_documents)} 条)")
    except Exception as e:
        print("⚠️ 保存 documents JSON 失败:", str(e))

    # 实际提交构建（远程 RAG 服务内部会按批次创建/追加）
    print("\n=== 开始创建知识库（按批次提交） ===")
    print(f"预计总文档数: {total_docs}（实际提交时以批次计数为准）")

    shared_repo_info = {"full_name": REPO_FULL_NAME}

    try:
        index_name = await provider.build_vectorstore(REPO_DIR, shared_repo_info)
        print("\n✅ 创建完成")
        print("索引名称:", index_name)
        print("仓库标识:", REPO_FULL_NAME)
    except Exception as e:
        print("\n💥 创建失败:", str(e))


if __name__ == "__main__":
    asyncio.run(run_test())
