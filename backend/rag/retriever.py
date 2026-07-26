"""知识检索器 — 整合嵌入+向量搜索，提供统一的 RAG 接口"""

from typing import Optional
from .embedder import Embedder
from .store import VectorStore


class KnowledgeRetriever:
    """FM 知识库 RAG 检索器"""

    def __init__(self, embedder: Embedder, store: VectorStore):
        self.embedder = embedder
        self.store = store

    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        category_filter: Optional[str] = None,
    ) -> list[dict]:
        """检索相关知识"""
        filter_dict = None
        if category_filter:
            filter_dict = {"category": category_filter}

        # 生成查询向量
        embeddings = await self.embedder.embed([query])
        query_vec = embeddings[0]

        # 检索
        results = self.store.query(query_vec, n_results=top_k, filter=filter_dict)
        return results

    async def retrieve_context(
        self,
        query: str,
        top_k: int = 5,
    ) -> str:
        """检索并格式化为上下文字符串（直接注入到 LLM prompt）"""
        results = await self.retrieve(query, top_k=top_k)

        if not results:
            return ""

        parts = ["## 📚 相关知识库资料\n"]
        for i, r in enumerate(results, 1):
            score_pct = round(r["score"] * 100)
            meta = r.get("metadata", {})
            source = meta.get("source", "FM知识库")
            category = meta.get("category", "通用")

            parts.append(f"### 资料 {i} [{category}] (相关度: {score_pct}%)")
            parts.append(f"来源: {source}")
            parts.append(f"{r['content'][:800]}")  # 截断过长内容
            parts.append("")

        return "\n".join(parts)

    async def is_ready(self) -> bool:
        return self.store.is_available() and self.store.count() > 0
