#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG API 检索测试（CLIP 索引）
- 参照 example/rag/demo.py 的 /search 接口
- 使用固定参数：
  vector_field: "content"
  index: "document_20250815_02xi"
- 运行：python -m test.test_utils_rag_api_index
"""

import os
import requests
from datetime import datetime

BASE_URL = os.getenv("RAG_BASE_URL", "http://nodeport.sensedeal.vip:32421")
VECTOR_FIELD = "content"
INDEX_NAME = "document_20250815_02xi"
TOP_K = int(os.getenv("RAG_TOP_K", "5"))


def check_health():
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=10)
        ok = r.status_code == 200
        print("🔍 健康检查:", "通过" if ok else f"失败({r.status_code})")
        return ok
    except Exception as e:
        print("🔍 健康检查: 异常", e)
        return False


def search(query: str):
    payload = {
        "query": query,
        "vector_field": VECTOR_FIELD,
        "index": INDEX_NAME,
        "top_k": TOP_K,
    }
    try:
        resp = requests.post(
            f"{BASE_URL}/search",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=30,
        )
        if resp.status_code != 200:
            print("❌ 搜索失败:", resp.text)
            return
        data = resp.json()
        results = data.get("results", [])
        total = data.get("total")
        took = data.get("took")
        print(f"📊 找到 {total} 个相关文档，耗时 {took}ms")
        for i, item in enumerate(results[:TOP_K], 1):
            # 参照 demo.py 的返回结构
            score = item.get("score")
            doc = item.get("document", {})
            title = doc.get("title") or "(无标题)"
            file_path = doc.get("file") or doc.get("file_path") or "(未知文件)"
            snippet = doc.get("content") or ""
            if len(snippet) > 120:
                snippet = snippet[:120] + "…"
            print(f"  {i:02d}. [{score}] {title} | {file_path}")
            if snippet:
                print(f"      {snippet}")
    except Exception as e:
        print("❌ 请求异常:", str(e))


def main():
    print("🚀 RAG 索引检索测试（CLIP）")
    print("时间:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("服务地址:", BASE_URL)
    print("索引:", INDEX_NAME)
    print("向量字段:", VECTOR_FIELD)
    check_health()

    queries = [
        "CLIP 模型的文本编码器是如何实现的？",
        "Bottleneck 类的作用",
        "simple_tokenizer 的 BPE 逻辑",
        "AttentionPool2d 是什么",
        "如何在 README 中运行示例",
    ]
    for q in queries:
        print(f"\n🔎 查询: {q}")
        search(q)


if __name__ == "__main__":
    main()
