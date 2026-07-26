"""角色分配器 — 为阵型的每个位置分配最佳球员+角色+职责"""

import json
from pathlib import Path
from typing import Optional
from .player_scorer import PlayerScorer

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class RoleAssigner:
    """角色分配器"""

    def __init__(self):
        self.scorer = PlayerScorer()
        with open(DATA_DIR / "formations.json", "r", encoding="utf-8") as f:
            self.formations = json.load(f)["formations"]
        with open(DATA_DIR / "roles.json", "r", encoding="utf-8") as f:
            self.roles = json.load(f)["roles"]

    def assign(
        self,
        players: list[dict],
        formation_key: str,
        style: str = "gegenpress",
        locked_players: Optional[dict[str, str]] = None,
    ) -> dict:
        """
        为阵型分配球员和角色

        参数:
            players: 球员列表
            formation_key: 阵型标识
            style: 战术风格
            locked_players: 锁定球员 {position_slot: player_name}

        返回:
            {
                "formation": "433",
                "starting_xi": [{slot, player, role, duty, score, reasoning}, ...],
                "bench": [...],
                "rotation_options": {...},
                "balance_check": {...},
            }
        """
        locked_players = locked_players or {}
        formation = self.formations.get(formation_key)
        if not formation:
            return {"error": f"未知阵型: {formation_key}"}

        # 第一阶段：为每个位置找最佳角色+球员组合
        assignments = []
        used_players = set()

        for pos_slot in formation["positions"]:
            slot_name = pos_slot["slot"]
            eligible_positions = pos_slot["eligible"]

            # 检查是否有锁定球员
            if slot_name in locked_players:
                locked_name = locked_players[slot_name]
                locked_player = next((p for p in players if p.get("name") == locked_name), None)
                if locked_player:
                    # 为该球员找最佳角色
                    pos_group = self._to_position_group(eligible_positions[0])
                    role_scores = self.scorer.score_all_roles(locked_player)
                    best = role_scores[0] if role_scores else None
                    if best:
                        assignments.append({
                            "slot": slot_name,
                            "player": locked_player["name"],
                            "role": best["role_label"],
                            "role_key": best["role_key"],
                            "score": best["score"],
                            "locked": True,
                            "reasoning": f"用户指定首发 {locked_player['name']}，最佳角色 {best['role_label']} (评分 {best['score']})",
                        })
                        used_players.add(locked_player["name"])
                        continue

            # 筛选可踢该位置的球员
            candidates = [
                p for p in players
                if p.get("name") not in used_players
                and any(elig.lower() in (p.get("position", "") or "").lower() for elig in eligible_positions)
            ]

            if not candidates:
                assignments.append({
                    "slot": slot_name,
                    "player": None,
                    "role": None,
                    "score": 0,
                    "warning": f"没有可用球员踢 {slot_name}",
                })
                continue

            # 为每个候选人找最佳角色
            pos_group = self._to_position_group(eligible_positions[0])
            best_combo = None

            for candidate in candidates[:10]:
                role_scores = self.scorer.score_all_roles(candidate)
                if role_scores:
                    # 过滤出适合该位置的角色
                    relevant_roles = [
                        r for r in role_scores
                        if r.get("position_group") == pos_group
                    ]
                    if relevant_roles:
                        top_role = relevant_roles[0]
                        if not best_combo or top_role["score"] > best_combo["score"]:
                            best_combo = {
                                "player": candidate,
                                "role": top_role,
                            }

            if best_combo:
                p = best_combo["player"]
                r = best_combo["role"]
                assignments.append({
                    "slot": slot_name,
                    "player": p["name"],
                    "player_uid": p.get("uid", ""),
                    "role": r["role_label"],
                    "role_key": r["role_key"],
                    "score": r["score"],
                    "locked": False,
                    "reasoning": self._slot_reasoning(slot_name, r, p, style),
                    "alternative": self._find_alternative(candidates, p["name"], pos_group, eligible_positions),
                })
                used_players.add(p["name"])
            else:
                assignments.append({
                    "slot": slot_name,
                    "player": None,
                    "role": None,
                    "score": 0,
                    "warning": f"无法为 {slot_name} 匹配合适角色",
                })

        # 替补席：未使用的球员中评分最高的 7 人
        unused = [p for p in players if p.get("name") not in used_players]
        bench = []
        for p in sorted(unused, key=lambda x: x.get("current_ability", 0) or 0, reverse=True)[:7]:
            role_scores = self.scorer.score_all_roles(p)
            bench.append({
                "player": p["name"],
                "position": p.get("position", ""),
                "best_role": role_scores[0]["role_label"] if role_scores else "",
                "ca": p.get("current_ability", 0) or 0,
            })

        # 轮换选项
        rotation = self._build_rotation(assignments, players, formation)

        # 平衡检查
        balance = self._check_balance(assignments)

        return {
            "formation": formation_key,
            "formation_name": formation.get("label_zh", formation["name"]),
            "style": style,
            "starting_xi": assignments,
            "bench": bench,
            "rotation_options": rotation,
            "balance_check": balance,
        }

    def _to_position_group(self, eligible: str) -> str:
        mapping = {
            "GK": "GK", "DC": "DC", "DR": "DR_DL", "DL": "DR_DL",
            "WBR": "DR_DL", "WBL": "DR_DL",
            "DM": "DM", "MC": "MC",
            "AMC": "AMC", "AMR": "AMR_AML", "AML": "AMR_AML",
            "MR": "AMR_AML", "ML": "AMR_AML",
            "ST": "ST",
        }
        return mapping.get(eligible, "MC")

    def _slot_reasoning(self, slot: str, role: dict, player: dict, style: str) -> str:
        """为一个分配决策生成简短理由"""
        top_attrs = list(role.get("breakdown", {}).keys())[:3]
        reasons_parts = []

        if top_attrs:
            attr_labels = {
                "acceleration": "爆发力", "pace": "速度", "finishing": "射门",
                "passing": "传球", "dribbling": "盘带", "tackling": "抢断",
                "positioning": "站位", "anticipation": "预判", "vision": "视野",
                "crossing": "传中", "stamina": "耐力", "work_rate": "工作投入",
                "jumping_reach": "弹跳", "heading": "头球", "strength": "强壮",
                "first_touch": "停球", "technique": "技术", "composure": "镇定",
                "off_the_ball": "跑位", "decisions": "决断", "reflexes": "反应",
                "one_on_ones": "一对一", "rushing_out": "出击",
                "agility": "灵活", "balance": "平衡",
            }
            for attr in top_attrs[:3]:
                label = attr_labels.get(attr, attr)
                val = player.get(attr, 0) or 0
                if val >= 15:
                    reasons_parts.append(f"{label}={val}")

        if reasons_parts:
            return f"{player.get('name')} 的 {'/'.join(reasons_parts)} 适合 {role['role_label']}"
        return f"{player.get('name')} 在 {role['role_label']} 上评分 {role['score']}"

    def _find_alternative(self, candidates: list[dict], current_name: str,
                          pos_group: str, eligible: list[str]) -> list[dict]:
        """为某个位置找替代球员"""
        alternatives = []
        for p in candidates[:5]:
            if p.get("name") == current_name:
                continue
            role_scores = self.scorer.score_all_roles(p)
            relevant = [r for r in role_scores if r.get("position_group") == pos_group]
            if relevant:
                alternatives.append({
                    "player": p["name"],
                    "role": relevant[0]["role_label"],
                    "score": relevant[0]["score"],
                })
        return sorted(alternatives, key=lambda x: x["score"], reverse=True)[:3]

    def _build_rotation(self, assignments: list[dict], players: list[dict], formation: dict) -> dict:
        """构建轮换方案"""
        rotation = {}
        for slot in assignments:
            if slot.get("warning"):
                continue
            alt = slot.get("alternative", [])
            if alt:
                rotation[slot["slot"]] = {
                    "starter": slot["player"],
                    "rotation_option": alt[0]["player"] if alt else None,
                    "score_drop": round(slot["score"] - alt[0]["score"], 1) if alt else 0,
                }
        return rotation

    def _check_balance(self, assignments: list[dict]) -> dict:
        """检查阵型平衡性"""
        issues = []

        # 检查防守职责数量
        defend_count = sum(1 for a in assignments if a.get("role_key", "").endswith("_D"))
        attack_count = sum(1 for a in assignments if a.get("role_key", "").endswith("_A"))

        if defend_count < 3:
            issues.append({"type": "too_few_defend", "message": f"防守职责仅 {defend_count} 人，防线可能不够稳固"})
        if attack_count > 5:
            issues.append({"type": "too_many_attack", "message": f"进攻职责 {attack_count} 人，防守可能脱节"})

        # 检查中场控制
        mid_roles = [a for a in assignments if a["slot"] in ["DM", "MCR", "MCL", "MC"]]
        support_count = sum(1 for a in mid_roles if a.get("role_key", "").endswith("_S"))
        if support_count < 1 and mid_roles:
            issues.append({"type": "midfield_balance", "message": "中场缺少策应角色，衔接可能不畅"})

        return {
            "defend_duties": defend_count,
            "support_duties": sum(1 for a in assignments if a.get("role_key", "").endswith("_S")),
            "attack_duties": attack_count,
            "is_balanced": len(issues) == 0,
            "issues": issues,
        }
