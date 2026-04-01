# -*- coding: utf-8 -*-
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.fusion.rag_engine import _get_vector_store, get_rag_status

print("=== RAG 状态 ===")
status = get_rag_status()
for k, v in status.items():
    print(f"  {k}: {v}")

print("\n=== 测试向量存储 ===")
vs = _get_vector_store()
if vs:
    print("向量存储已加载")
    results = vs.similarity_search("钓鱼网站特征", k=3)
    print(f"检索结果数量: {len(results)}")
    for i, r in enumerate(results):
        print(f"结果{i+1}: {r.page_content[:100]}...")
else:
    print("向量存储未加载")
