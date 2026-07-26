"""知识库加载器 — 将 FM 专业知识文档向量化并存入 ChromaDB"""

import json
from pathlib import Path
from .embedder import Embedder
from .store import VectorStore

KNOWLEDGE_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "knowledge"


class KnowledgeLoader:
    """FM 知识库批量加载"""

    def __init__(self, embedder: Embedder, store: VectorStore):
        self.embedder = embedder
        self.store = store

    async def load_all(self) -> int:
        """加载所有知识文档到向量存储"""
        if not self.store.is_available():
            return 0

        if not KNOWLEDGE_DIR.exists():
            return 0

        loaded = 0
        for filepath in sorted(KNOWLEDGE_DIR.glob("*.json")):
            count = await self._load_file(filepath)
            loaded += count

        return loaded

    async def _load_file(self, filepath: Path) -> int:
        """加载单个知识文件"""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        documents = []
        metadatas = []
        ids = []

        # 知识条目可以是 list[dict] 或单个 dict 含 "entries"
        entries = data if isinstance(data, list) else data.get("entries", [data])

        for i, entry in enumerate(entries):
            title = entry.get("title", "")
            content = entry.get("content", "")
            category = entry.get("category", "通用")
            source = entry.get("source", filepath.stem)

            if not content:
                continue

            # 构建文档文本
            doc_text = f"# {title}\n\n{content}" if title else content

            # 分块（简单按段落切分）
            chunks = self._chunk_text(doc_text, max_chars=600)

            for j, chunk in enumerate(chunks):
                documents.append(chunk)
                metadatas.append({
                    "source": source,
                    "category": category,
                    "title": title,
                    "chunk": j,
                })
                ids.append(f"{filepath.stem}_{i}_{j}")

        if documents:
            # 批量嵌入
            embeddings = await self.embedder.embed(documents)
            self.store.add(documents, embeddings, metadatas, ids)

        return len(documents)

    def _chunk_text(self, text: str, max_chars: int = 600) -> list[str]:
        """将文本切分为多个块"""
        if len(text) <= max_chars:
            return [text]

        chunks = []
        paragraphs = text.split("\n\n")

        current = ""
        for para in paragraphs:
            if len(current) + len(para) < max_chars:
                current += para + "\n\n"
            else:
                if current:
                    chunks.append(current.strip())
                current = para + "\n\n"

        if current.strip():
            chunks.append(current.strip())

        return chunks or [text]

    async def reload(self) -> int:
        """清空并重新加载"""
        self.store.clear()
        return await self.load_all()
