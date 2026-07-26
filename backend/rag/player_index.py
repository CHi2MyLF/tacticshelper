"""球员语义索引 — 属性向量化 + 相似球员搜索"""

import numpy as np
from typing import Optional, Union

# 用于向量化的属性列表（权重基于 FM-Arena 测试）
PLAYER_ATTR_VECTOR = [
    # 身体 (最重要)
    ("pace", 2.0), ("acceleration", 2.0), ("stamina", 1.0),
    ("strength", 0.8), ("jumping_reach", 0.9), ("agility", 0.8),
    ("balance", 0.7), ("natural_fitness", 0.5),
    # 技术
    ("finishing", 1.2), ("dribbling", 1.2), ("passing", 1.2),
    ("first_touch", 1.0), ("technique", 1.0), ("crossing", 0.7),
    ("heading", 0.7), ("long_shots", 0.6), ("marking", 0.8),
    ("tackling", 0.8),
    # 精神
    ("anticipation", 1.0), ("composure", 1.0), ("decisions", 1.0),
    ("vision", 1.0), ("off_the_ball", 0.8), ("positioning", 0.8),
    ("work_rate", 0.9), ("determination", 0.6), ("teamwork", 0.6),
    ("flair", 0.4), ("bravery", 0.4), ("leadership", 0.3),
    # 门将特殊
    ("reflexes", 0.6), ("handling", 0.5), ("one_on_ones", 0.5),
    ("aerial_reach", 0.5), ("command_of_area", 0.4),
]


class PlayerIndex:
    """球员语义搜索索引"""

    def __init__(self):
        self.players: list[dict] = []
        self.vectors: Optional[np.ndarray] = None

    def build(self, players: list[dict]) -> None:
        """构建球员向量索引"""
        self.players = players
        vectors = []

        for p in players:
            vec = []
            for attr, weight in PLAYER_ATTR_VECTOR:
                val = p.get(attr, 0) or 0
                vec.append(val * weight / 20.0)  # 归一化到 [0, 1]

            # 添加位置编码（one-hot）
            positions = ["GK", "DC", "DL", "DR", "DM", "MC", "AMC", "AML", "AMR", "ST"]
            player_pos = (p.get("position", "") or "").lower()
            for pos in positions:
                vec.append(1.0 if pos.lower() in player_pos else 0.0)

            vectors.append(vec)

        self.vectors = np.array(vectors, dtype=np.float32)
        # L2 归一化
        norms = np.linalg.norm(self.vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1
        self.vectors = self.vectors / norms

    def search(
        self,
        query: Union[dict, str],
        top_k: int = 10,
        position_filter: Optional[str] = None,
        min_pace: Optional[int] = None,
    ) -> list[dict]:
        """
        语义搜索相似球员

        query: 球员属性 dict 或球员名称（从已索引列表中查找）
        """
        if self.vectors is None:
            return []

        # 获取查询向量
        if isinstance(query, str):
            # 按名称查找
            query_vec = None
            for i, p in enumerate(self.players):
                if query.lower() in (p.get("name", "") or "").lower():
                    query_vec = self.vectors[i]
                    break
            if query_vec is None:
                return []
        else:
            # 从属性构建向量
            vec = []
            for attr, weight in PLAYER_ATTR_VECTOR:
                val = query.get(attr, 0) or 0
                vec.append(val * weight / 20.0)
            player_pos = (query.get("position", "") or "").lower()
            for pos in ["GK", "DC", "DL", "DR", "DM", "MC", "AMC", "AML", "AMR", "ST"]:
                vec.append(1.0 if pos.lower() in player_pos else 0.0)
            query_vec = np.array(vec, dtype=np.float32)
            norm = np.linalg.norm(query_vec)
            if norm > 0:
                query_vec = query_vec / norm

        if query_vec is None:
            return []

        # 余弦相似度
        similarities = np.dot(self.vectors, query_vec)

        # 过滤
        results = []
        for i, sim in enumerate(similarities):
            p = self.players[i]

            # 过滤条件
            if position_filter and position_filter.lower() not in (p.get("position", "") or "").lower():
                continue
            if min_pace and (p.get("pace", 0) or 0) < min_pace:
                continue

            results.append({
                "player": p.get("name"),
                "position": p.get("position"),
                "age": p.get("age"),
                "ca": p.get("current_ability") or 0,
                "pa": p.get("potential_ability") or 0,
                "pace": p.get("pace") or 0,
                "acceleration": p.get("acceleration") or 0,
                "finishing": p.get("finishing") or 0,
                "passing": p.get("passing") or 0,
                "tackling": p.get("tackling") or 0,
                "similarity": round(float(sim) * 100, 1),
            })

        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_k]

    def search_by_description(self, description: str, top_k: int = 10) -> list[dict]:
        """根据文字描述搜索球员

        例: "速度快、盘带好的右边锋"
        """
        # 从描述中提取属性要求
        pseudo_attrs = self._parse_description(description)
        return self.search(pseudo_attrs, top_k=top_k)

    def _parse_description(self, desc: str) -> dict:
        """简单解析文字描述提取属性要求"""
        desc_lower = desc.lower()
        attrs = {}

        keywords_map = {
            "速度快": {"pace": 17, "acceleration": 17},
            "快": {"pace": 16, "acceleration": 15},
            "速度": {"pace": 16, "acceleration": 15},
            "盘带": {"dribbling": 16, "technique": 15},
            "过人": {"dribbling": 16},
            "传球": {"passing": 16, "vision": 14},
            "组织": {"passing": 15, "vision": 16, "decisions": 15},
            "防守": {"tackling": 15, "marking": 15, "positioning": 15},
            "抢断": {"tackling": 16},
            "头球": {"heading": 16, "jumping_reach": 15},
            "身体": {"strength": 15, "balance": 15},
            "强壮": {"strength": 16},
            "耐力": {"stamina": 16, "natural_fitness": 15},
            "射门": {"finishing": 16, "composure": 15},
            "终结": {"finishing": 16},
            "创造力": {"vision": 16, "flair": 16},
            "领导": {"leadership": 16},
            "勤奋": {"work_rate": 16},
            "跑动": {"stamina": 15, "work_rate": 15},
            "控球": {"first_touch": 15, "technique": 15},
            "门将": {"reflexes": 15, "handling": 15},
            "年轻": {},  # 会在过滤中处理
            "老将": {},  # 经验丰富
            "右边锋": {"position_filter": "AMR"},
            "左边锋": {"position_filter": "AML"},
            "边锋": {"pace": 16, "dribbling": 15, "crossing": 14},
            "前锋": {"finishing": 15, "off_the_ball": 15},
            "中后卫": {"position_filter": "DC"},
            "后腰": {"position_filter": "DM"},
            "中场": {"passing": 14, "work_rate": 14},
        }

        for keyword, attr_map in keywords_map.items():
            if keyword.lower() in desc_lower:
                attrs.update(attr_map)

        # 默认值
        for attr, _ in PLAYER_ATTR_VECTOR[:10]:
            if attr not in attrs and not attr.startswith("position"):
                attrs.setdefault(attr, 12)

        return attrs
