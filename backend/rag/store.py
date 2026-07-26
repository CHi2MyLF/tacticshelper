"""向量存储 — 基于 ChromaDB 的持久化向量数据库 (懒加载)"""

import os
import json
from pathlib import Path
from typing import Optional

HAS_CHROMADB = False


def _ensure_chromadb():
    global HAS_CHROMADB
    if not HAS_CHROMADB:
        try:
            import chromadb
            globals()["chromadb"] = chromadb
            HAS_CHROMADB = True
        except ImportError:
            pass
    return HAS_CHROMADB

STORAGE_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "chroma"


class VectorStore:
    """向量存储封装"""

    def __init__(self, collection_name: str = "fm_knowledge"):
        self.collection_name = collection_name
        self.client = None
        self.collection = None
        self._init_done = False

    def _lazy_init(self):
        if self._init_done:
            return
        self._init_done = True
        if _ensure_chromadb():
            STORAGE_DIR.mkdir(parents=True, exist_ok=True)
            import chromadb
            from chromadb.config import Settings
            self.client = chromadb.PersistentClient(
                path=str(STORAGE_DIR),
                settings=Settings(anonymized_telemetry=False),
            )
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )

    def add(
        self,
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict] = None,
        ids: list[str] = None,
    ) -> None:
        """批量添加文档"""
        self._lazy_init()
        if self.collection is None:
            return

        if ids is None:
            count = self.collection.count()
            ids = [f"doc_{count + i}" for i in range(len(documents))]

        self.collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas or [{}] * len(documents),
            ids=ids,
        )

    def query(
        self,
        query_embedding: list[float],
        n_results: int = 5,
        filter: dict = None,
    ) -> list[dict]:
        """相似度搜索"""
        if self.collection is None or self.collection.count() == 0:
            return []

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(n_results, self.collection.count()),
            where=filter,
            include=["documents", "metadatas", "distances"],
        )

        docs = []
        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                docs.append({
                    "content": doc,
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else 0,
                    "score": 1 - results["distances"][0][i] if results["distances"] else 0,
                })

        return docs

    def count(self) -> int:
        self._lazy_init()
        if self.collection is None:
            return 0
        return self.collection.count()

    def clear(self) -> None:
        """清空集合"""
        if self.collection is not None:
            all_ids = self.collection.get()["ids"]
            if all_ids:
                self.collection.delete(ids=all_ids)

    def is_available(self) -> bool:
        return self.collection is not None
