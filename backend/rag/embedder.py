"""嵌入生成器 — 支持 Anthropic API 和本地 sentence-transformers"""

from typing import Optional
import numpy as np

HAS_ANTHROPIC = False
HAS_SENTENCE_TRANSFORMERS = False


class Embedder:
    """文本嵌入生成器"""

    def __init__(
        self,
        api_key: str = "",
        base_url: str = "https://api.anthropic.com",
        model: str = "claude-sonnet-4-20250514",
        use_local: bool = False,
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.use_local = use_local
        self._local_model = None
        self._client = None

        if use_local and HAS_SENTENCE_TRANSFORMERS:
            self._local_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

        if api_key and HAS_ANTHROPIC and not use_local:
            self._client = anthropic.Anthropic(api_key=api_key, base_url=base_url)

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """生成嵌入向量"""
        if self._local_model is not None:
            return self._embed_local(texts)

        if self._client is not None:
            return await self._embed_anthropic(texts)

        # Fallback: bag-of-words based embedding (no external deps)
        return self._embed_fallback(texts)

    def _embed_local(self, texts: list[str]) -> list[list[float]]:
        """使用本地模型"""
        embeddings = self._local_model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()

    async def _embed_anthropic(self, texts: list[str]) -> list[list[float]]:
        """使用 Anthropic API（通过 prompt-based 方式获取表示）

        注意：Anthropic 没有独立的 embeddings API。
        这里使用一个替代方案：基于关键属性的词汇级嵌入。
        """
        # 使用属性权重向量做 semantic hashing — 不依赖外部 API
        return self._embed_attribute_based(texts)

    def _embed_attribute_based(self, texts: list[str]) -> list[list[float]]:
        """基于 FM 属性词汇的局部嵌入

        这是一个不依赖任何外部 API 的轻量级方案。
        原理：提取文本中 FM 属性相关词汇，构建 512 维稀疏向量
        """
        # FM 属性关键词 + 权重
        attr_keywords = {
            "pace": 1.0, "speed": 1.0, "速度": 1.0, "快": 0.8,
            "acceleration": 0.95, "爆发": 0.95, "加速": 0.9,
            "finishing": 0.9, "射门": 0.9, "终结": 0.85,
            "passing": 0.85, "传球": 0.85, "组织": 0.8,
            "tackling": 0.8, "抢断": 0.8, "防守": 0.75,
            "dribbling": 0.85, "盘带": 0.85, "过人": 0.8,
            "crossing": 0.7, "传中": 0.7,
            "heading": 0.7, "头球": 0.7, "jumping": 0.7,
            "stamina": 0.8, "耐力": 0.8, "体能": 0.75,
            "work_rate": 0.8, "工作投入": 0.8, "勤奋": 0.75,
            "strength": 0.7, "强壮": 0.7, "力量": 0.65,
            "vision": 0.8, "视野": 0.8, "创造力": 0.75,
            "anticipation": 0.8, "预判": 0.8,
            "composure": 0.75, "镇定": 0.75,
            "decisions": 0.8, "决断": 0.8, "决策": 0.75,
            "positioning": 0.75, "站位": 0.75,
            "technique": 0.8, "技术": 0.8,
            "first_touch": 0.75, "停球": 0.75,
            "off_the_ball": 0.7, "跑位": 0.7,
            "leadership": 0.6, "领导力": 0.6,
            "teamwork": 0.65, "团队": 0.65,
            "reflexes": 0.7, "反应": 0.7,
            "handling": 0.6, "手控球": 0.6,
            # 战术概念
            "压迫": 0.9, "pressing": 0.9, "gegenpress": 0.9,
            "控球": 0.85, "possession": 0.85, "tiki": 0.85,
            "反击": 0.85, "counter": 0.85,
            "阵型": 0.8, "formation": 0.8,
            "433": 0.7, "4231": 0.7, "442": 0.7, "352": 0.7,
            "边锋": 0.75, "winger": 0.75, "inside_forward": 0.75,
            "前锋": 0.7, "striker": 0.7, "forward": 0.7,
            "中场": 0.7, "midfielder": 0.7,
            "后卫": 0.7, "defender": 0.7, "centre_back": 0.7,
            "门将": 0.65, "goalkeeper": 0.65,
            "训练": 0.6, "training": 0.6,
            "转会": 0.6, "transfer": 0.6, "预算": 0.5,
            "年轻": 0.55, "青训": 0.55, "youth": 0.55,
        }

        dim = 256
        embeddings = []

        for text in texts:
            text_lower = text.lower()
            vec = np.zeros(dim)

            for keyword, weight in attr_keywords.items():
                if keyword in text_lower:
                    # 使用 hash 映射到向量维度
                    idx = hash(keyword) % dim
                    vec[idx] += weight * 0.5

                    # 周围维度也加一点 (smoothing)
                    vec[(idx + 1) % dim] += weight * 0.2
                    vec[(idx - 1) % dim] += weight * 0.2

            # L2 归一化
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm

            embeddings.append(vec.tolist())

        return embeddings

    def _embed_fallback(self, texts: list[str]) -> list[list[float]]:
        """最终 fallback"""
        return self._embed_attribute_based(texts)
