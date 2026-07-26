"""球员-角色评分系统 (DWRS — Dynamic Weighted Role Score)

结合 FM-Arena 经验系数 + 角色关键属性权重，
为每个球员在每个角色上打出 0-100 的综合评分。
"""

import json
from pathlib import Path
from typing import Optional

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class PlayerScorer:
    """球员角色评分器"""

    def __init__(self):
        with open(DATA_DIR / "coefficients.json", "r", encoding="utf-8") as f:
            self.coef_data = json.load(f)
        with open(DATA_DIR / "roles.json", "r", encoding="utf-8") as f:
            self.roles_data = json.load(f)

        self.meta_tiers = self.coef_data["meta_weights"]["tiers"]
        self.position_coefs = self.coef_data["position_coefficients"]
        self.roles = self.roles_data["roles"]

    # ─── 属性分组权重 (meta weights) ───

    def get_meta_weight(self, attr: str) -> float:
        """获取属性的元权重（来自 FM-Arena 测试）"""
        for tier_name, tier_data in self.meta_tiers.items():
            if attr in tier_data["attrs"]:
                return tier_data["weight"]
        return 0.2  # 未知属性最低权重

    # ─── 位置系数 ───

    def get_position_coefficient(self, attr: str, position: str) -> float:
        """获取某位置下某属性的经验系数"""
        pos_data = self.position_coefs.get(position, {})
        return pos_data.get(attr, 0.001)

    # ─── 角色关键属性 ───

    def get_role_attrs(self, position_group: str, role_key: str) -> Optional[dict]:
        """获取角色的关键属性和偏好属性"""
        group = self.roles.get(position_group, {})
        return group.get(role_key)

    # ─── 核心评分函数 ───

    def score(self, player: dict, role_key: str, position_group: str) -> dict:
        """
        计算球员在特定角色上的 DWRS 评分。

        参数:
            player: 球员属性 dict（name, pace, finishing, ...）
            role_key: 角色标识（如 "IF_A", "BBM_S"）
            position_group: 位置组（如 "AMR_AML", "MC"）

        返回:
            {
                "player_name": "Messi",
                "role": "Inside Forward (Attack)",
                "role_key": "IF_A",
                "score": 87.5,
                "breakdown": {...}  # 各属性贡献明细
            }
        """
        role_data = self.get_role_attrs(position_group, role_key)
        if not role_data:
            return {
                "player_name": player.get("name", "Unknown"),
                "role_key": role_key,
                "score": 0,
                "error": f"未知角色: {position_group}/{role_key}",
            }

        key_attrs = role_data.get("key_attrs", [])
        preferred_attrs = role_data.get("preferred_attrs", [])
        avoid_attrs = role_data.get("avoid", [])

        # 确定位置（用于查位置系数）
        pos = self._resolve_position(position_group, player)

        total_weighted = 0.0
        max_possible = 0.0
        breakdown = {}

        all_relevant_attrs = list(set(key_attrs + preferred_attrs))

        for attr in all_relevant_attrs:
            value = player.get(attr, 0)
            if value is None:
                value = 0

            # 三层权重计算
            meta_w = self.get_meta_weight(attr)           # 元权重 (0.2-8.0)
            pos_c = self.get_position_coefficient(attr, pos)  # 位置系数
            role_m = 1.5 if attr in key_attrs else 1.2    # 角色乘数
            if attr in avoid_attrs:
                role_m = 0.3  # 不适合的属性降低权重

            combined = meta_w * pos_c * role_m * 20  # 缩放（20=属性满值）

            total_weighted += value * combined
            max_possible += 20 * combined

            breakdown[attr] = {
                "value": value,
                "meta_weight": round(meta_w, 1),
                "position_coef": round(pos_c, 5),
                "role_multiplier": round(role_m, 1),
                "contribution": round(value * combined, 2),
            }

        score = round((total_weighted / max_possible * 100), 1) if max_possible > 0 else 0.0

        return {
            "player_name": player.get("name", "Unknown"),
            "role_key": role_key,
            "role_label": role_data.get("label_zh", role_key),
            "position_group": position_group,
            "score": score,
            "breakdown": dict(sorted(breakdown.items(), key=lambda x: x[1]["contribution"], reverse=True)),
        }

    def score_all_roles(self, player: dict) -> list[dict]:
        """为球员在所有可能角色上打分，返回排序后的结果"""
        results = []
        position = player.get("position", "")

        # 根据球员位置筛选相关角色组
        relevant_groups = self._get_relevant_groups(position)

        for group in relevant_groups:
            group_roles = self.roles.get(group, {})
            for role_key in group_roles:
                result = self.score(player, role_key, group)
                results.append(result)

        results.sort(key=lambda x: x["score"], reverse=True)
        return results

    def score_squad_for_formation(self, players: list[dict], formation_key: str) -> dict:
        """为全队在一个阵型的所有位置上评分"""
        with open(DATA_DIR / "formations.json", "r", encoding="utf-8") as f:
            formations = json.load(f)["formations"]

        formation = formations.get(formation_key)
        if not formation:
            return {"error": f"未知阵型: {formation_key}"}

        position_scores = {}
        for pos_slot in formation["positions"]:
            slot_name = pos_slot["slot"]
            eligible = pos_slot["eligible"]
            position_group = self._to_position_group(eligible[0])

            # 筛选能打这个位置的球员
            candidates = [
                p for p in players
                if any(elig.lower() in (p.get("position", "") or "").lower() for elig in eligible)
            ]

            # 为这批球员在所有相关角色上评分
            role_scores = {}
            group_roles = self.roles.get(position_group, {})
            for role_key in group_roles:
                player_scores = []
                for p in candidates[:5]:  # top-5 候选人
                    s = self.score(p, role_key, position_group)
                    player_scores.append(s)
                player_scores.sort(key=lambda x: x["score"], reverse=True)
                role_scores[role_key] = player_scores[:3]  # 每个角色 top-3

            position_scores[slot_name] = {
                "candidates": len(candidates),
                "top_roles": self._summarize_top_roles(role_scores),
                "detailed": role_scores,
            }

        return position_scores

    # ─── 辅助方法 ───

    def _resolve_position(self, position_group: str, player: dict) -> str:
        """根据位置组和球员位置确定用于查系数的位置标签"""
        group_to_pos = {
            "GK": "GK", "DC": "DC",
            "DR_DL": "DR", "DM": "DM", "MC": "MC",
            "AMC": "AMC", "AMR_AML": "AMR", "ST": "ST",
        }
        return group_to_pos.get(position_group, "MC")

    def _get_relevant_groups(self, position: str) -> list[str]:
        """根据球员位置字符串返回相关的位置组"""
        pos_lower = (position or "").lower()
        groups = []
        if "gk" in pos_lower:
            groups.append("GK")
        if any(p in pos_lower for p in ["dc", "sw", "d ", "d("]):
            groups.append("DC")
        if any(p in pos_lower for p in ["dr", "dl", "wbr", "wbl"]):
            groups.append("DR_DL")
        if any(p in pos_lower for p in ["dm", "dmc"]):
            groups.append("DM")
        if any(p in pos_lower for p in ["mc", "m ", "m("]):
            groups.append("MC")
        if "amc" in pos_lower:
            groups.append("AMC")
        if any(p in pos_lower for p in ["amr", "aml", "am ", "am("]):
            groups.append("AMR_AML")
        if any(p in pos_lower for p in ["st", "sc", "fc"]):
            groups.append("ST")

        if not groups:
            # fallback: try all outfield groups
            groups = ["DC", "DR_DL", "DM", "MC", "AMC", "AMR_AML", "ST"]

        return groups

    def _to_position_group(self, eligible: str) -> str:
        """将阵型中的位置标签映射到角色组"""
        mapping = {
            "GK": "GK", "DC": "DC", "DR": "DR_DL", "DL": "DR_DL",
            "WBR": "DR_DL", "WBL": "DR_DL",
            "DM": "DM", "MC": "MC",
            "AMC": "AMC", "AMR": "AMR_AML", "AML": "AMR_AML",
            "MR": "AMR_AML", "ML": "AMR_AML",
            "ST": "ST",
        }
        return mapping.get(eligible, "MC")

    def _summarize_top_roles(self, role_scores: dict) -> list[dict]:
        """汇总每个位置的最佳角色"""
        summary = []
        for role_key, player_scores in role_scores.items():
            if player_scores:
                top = player_scores[0]
                summary.append({
                    "role_key": role_key,
                    "best_player": top["player_name"],
                    "score": top["score"],
                })
        summary.sort(key=lambda x: x["score"], reverse=True)
        return summary[:3]


# 便捷函数
def score_player_for_role(player: dict, role_key: str, position_group: str = "MC") -> dict:
    """为单个球员在单个角色上评分"""
    scorer = PlayerScorer()
    return scorer.score(player, role_key, position_group)
