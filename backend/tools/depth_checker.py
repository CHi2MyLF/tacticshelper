"""阵容深度分析 — 评估各位置的轮换深度和伤病风险"""

from .player_scorer import PlayerScorer


class DepthChecker:
    """阵容深度检查器"""

    def __init__(self):
        self.scorer = PlayerScorer()

    def check(self, players: list[dict], formation_key: str = "433") -> dict:
        """
        检查阵容深度

        返回:
            {
                "position_depth": {position: {starter, backup, depth_score}},
                "critical_positions": [...],
                "recommendations": [...],
                "overall_depth_score": 85,
            }
        """
        # 定义关键位置组
        position_groups = {
            "GK": {"min_players": 2, "critical": True, "label_zh": "门将"},
            "DC": {"min_players": 3, "critical": True, "label_zh": "中后卫"},
            "DL": {"min_players": 2, "critical": False, "label_zh": "左后卫"},
            "DR": {"min_players": 2, "critical": False, "label_zh": "右后卫"},
            "DM": {"min_players": 1, "critical": False, "label_zh": "防守型中场"},
            "MC": {"min_players": 3, "critical": True, "label_zh": "中场"},
            "AML": {"min_players": 2, "critical": False, "label_zh": "左边锋"},
            "AMR": {"min_players": 2, "critical": False, "label_zh": "右边锋"},
            "AMC": {"min_players": 1, "critical": False, "label_zh": "前腰"},
            "ST": {"min_players": 2, "critical": True, "label_zh": "前锋"},
        }

        depth_report = {}
        critical_positions = []
        recommendations = []

        for pos_key, pos_info in position_groups.items():
            # 找到能踢该位置的所有球员
            eligible = self._find_eligible(players, pos_key)

            # 按能力排序
            sorted_players = sorted(eligible, key=lambda p: p.get("current_ability", 0) or 0, reverse=True)

            starter = sorted_players[0] if len(sorted_players) > 0 else None
            backup = sorted_players[1] if len(sorted_players) > 1 else None

            depth_report[pos_key] = {
                "label_zh": pos_info["label_zh"],
                "eligible_count": len(eligible),
                "min_required": pos_info["min_players"],
                "starter": starter.get("name") if starter else None,
                "starter_ca": starter.get("current_ability", 0) or 0 if starter else 0,
                "backup": backup.get("name") if backup else None,
                "backup_ca": backup.get("current_ability", 0) or 0 if backup else 0,
                "quality_drop": None,
            }

            if starter and backup:
                starter_ca = starter.get("current_ability", 0) or 0
                backup_ca = backup.get("current_ability", 0) or 0
                drop = starter_ca - backup_ca
                depth_report[pos_key]["quality_drop"] = drop
                if drop > 20:
                    depth_report[pos_key]["warning"] = f"主力与替补差距大 (CA 差 {drop})"
                    if pos_info["critical"]:
                        recommendations.append(f"【{pos_info['label_zh']}】主力({starter.get('name')})与替补({backup.get('name')})能力差距大，建议引进轮换球员")

            if len(eligible) < pos_info["min_players"]:
                shortage = pos_info["min_players"] - len(eligible)
                issue = {
                    "position": pos_key,
                    "label": pos_info["label_zh"],
                    "shortage": shortage,
                    "current": len(eligible),
                }
                critical_positions.append(issue)
                recommendations.append(f"【{pos_info['label_zh']}】仅有 {len(eligible)} 人，需要 {pos_info['min_players']} 人，缺口 {shortage} 人")

        # 综合深度评分
        total_slots = sum(1 for p in position_groups.values())
        adequate_slots = sum(
            1 for k, p in position_groups.items()
            if depth_report[k]["eligible_count"] >= p["min_players"]
        )
        depth_score = round((adequate_slots / total_slots) * 100)

        return {
            "position_depth": depth_report,
            "critical_positions": critical_positions,
            "recommendations": recommendations,
            "overall_depth_score": depth_score,
            "assessment": (
                "阵容深度充足" if depth_score >= 90
                else "阵容深度良好" if depth_score >= 75
                else "阵容深度一般" if depth_score >= 60
                else "阵容深度不足，需要补强"
            ),
        }

    def _find_eligible(self, players: list[dict], position: str) -> list[dict]:
        """找到能打某个位置的所有球员"""
        eligible = []
        pos_lower = position.lower()

        for p in players:
            player_pos = (p.get("position", "") or "").lower()

            # 直接匹配
            if pos_lower in player_pos:
                eligible.append(p)
                continue

            # 交叉匹配
            if pos_lower == "dc" and any(pp in player_pos for pp in ["dc", "sw", "d ", "d(", "dr", "dl"]):
                eligible.append(p)
            elif pos_lower in ("dl", "dr") and any(pp in player_pos for pp in [pos_lower, "wbr", "wbl", "d ", "d("]):
                eligible.append(p)
            elif pos_lower == "dm" and any(pp in player_pos for pp in ["dm", "mc"]):
                eligible.append(p)
            elif pos_lower == "mc" and any(pp in player_pos for pp in ["mc", "dm", "amc"]):
                eligible.append(p)
            elif pos_lower in ("aml", "amr") and any(pp in player_pos for pp in [pos_lower, "am ", "am(", "ml", "mr", "st"]):
                eligible.append(p)
            elif pos_lower == "st" and any(pp in player_pos for pp in ["st", "sc", "fc", "amc", "amr", "aml"]):
                eligible.append(p)

        return eligible
