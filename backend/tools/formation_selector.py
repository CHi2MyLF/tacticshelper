"""阵型推荐器 — 基于阵容和偏好推荐最佳阵型"""

import json
from pathlib import Path
from typing import Optional
from .player_scorer import PlayerScorer

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class FormationSelector:
    """阵型选择器"""

    def __init__(self):
        self.scorer = PlayerScorer()
        with open(DATA_DIR / "formations.json", "r", encoding="utf-8") as f:
            self.formations = json.load(f)["formations"]
        with open(DATA_DIR / "styles.json", "r", encoding="utf-8") as f:
            self.styles = json.load(f)["styles"]

    def recommend(
        self,
        players: list[dict],
        preferred_style: str = "gegenpress",
        preferred_formation: Optional[str] = None,
    ) -> dict:
        """
        推荐阵型

        参数:
            preferred_style: 战术风格 (gegenpress/tiki_taka/direct_counter/...)
            preferred_formation: 用户偏好的阵型 (4231/433/442/...)

        返回:
            {
                "recommended": "433",
                "reasoning": "...",
                "rankings": [...],
                "style_compatibility": {...},
            }
        """
        style_data = self.styles.get(preferred_style, self.styles["gegenpress"])

        # 如果用户有明确偏好阵型，优先评估该阵型
        candidates = list(self.formations.keys())
        if preferred_formation and preferred_formation in self.formations:
            candidates = [preferred_formation] + [f for f in candidates if f != preferred_formation]

        rankings = []
        for form_key in candidates[:5]:  # 评估 top-5 阵型
            form = self.formations[form_key]
            score_detail = self._evaluate_formation(players, form_key, form, style_data)
            # 风格匹配度加分
            style_bonus = 1.2 if preferred_style in form.get("best_for", []) else 0.8
            score_detail["total"] = round(score_detail["player_fit"] * style_bonus, 1)
            score_detail["formation_key"] = form_key
            score_detail["formation_name"] = form.get("label_zh", form["name"])
            rankings.append(score_detail)

        rankings.sort(key=lambda x: x["total"], reverse=True)

        best = rankings[0]
        reasoning = self._build_reasoning(best, players, preferred_style)

        return {
            "recommended": best["formation_key"],
            "recommended_name": best["formation_name"],
            "reasoning": reasoning,
            "rankings": rankings,
            "style": {
                "key": preferred_style,
                "label": style_data.get("label_zh", preferred_style),
                "mentality": style_data.get("mentality", "balanced"),
            },
        }

    def _evaluate_formation(self, players: list[dict], form_key: str, form: dict, style_data: dict) -> dict:
        """评估单个阵型的适配度"""
        position_scores = self.scorer.score_squad_for_formation(players, form_key)

        total_score = 0
        slot_count = 0
        weak_slots = []

        for slot_name, slot_data in position_scores.items():
            if slot_data.get("candidates", 0) == 0:
                weak_slots.append({"slot": slot_name, "issue": "无人可用"})
                continue

            top_roles = slot_data.get("top_roles", [])
            best_role_score = top_roles[0]["score"] if top_roles else 0
            total_score += best_role_score
            slot_count += 1

            if best_role_score < 60:
                weak_slots.append({"slot": slot_name, "issue": f"最佳角色评分仅 {best_role_score}"})

        avg_score = round(total_score / slot_count, 1) if slot_count > 0 else 0

        return {
            "player_fit": avg_score,
            "slot_count": slot_count,
            "weak_slots": weak_slots,
            "fit_label": "优秀" if avg_score >= 80 else ("良好" if avg_score >= 70 else ("一般" if avg_score >= 60 else "不足")),
        }

    def _build_reasoning(self, best: dict, players: list[dict], style: str) -> list[str]:
        """构建推荐理由"""
        reasons = []

        form_name = best.get("formation_name", best.get("formation_key", ""))
        reasons.append(f"阵型 {form_name} 球员适配度最高，综合评分 {best.get('total', 0)}")

        if best.get("weak_slots"):
            slots = ", ".join([w["slot"] for w in best["weak_slots"]])
            reasons.append(f"注意：{slots} 位置深度不足，需关注")

        if best.get("player_fit", 0) >= 75:
            reasons.append("你的阵容对这个阵型有良好的属性支撑")
        elif best.get("player_fit", 0) >= 65:
            reasons.append("这个阵型在你的阵容中基本可行，但个别位置需要补强")

        return reasons
