"""阵容诊断 — 分析全队优劣势、深度、平衡性"""

from typing import Optional
from .player_scorer import PlayerScorer

# 出场球员属性
OUTFIELD_ATTRS = [
    "acceleration", "agility", "balance", "jumping_reach", "natural_fitness",
    "pace", "stamina", "strength",
    "corners", "crossing", "dribbling", "finishing", "first_touch",
    "free_kicks", "heading", "long_shots", "long_throws", "marking",
    "passing", "penalty_taking", "tackling", "technique",
    "aggression", "anticipation", "bravery", "composure", "concentration",
    "decisions", "determination", "flair", "leadership", "off_the_ball",
    "positioning", "teamwork", "vision", "work_rate",
]

GK_ATTRS = [
    "aerial_reach", "command_of_area", "communication", "eccentricity",
    "handling", "kicking", "one_on_ones", "reflexes", "rushing_out",
    "throwing", "tendency_to_punch",
]


class SquadDiagnosis:
    """阵容诊断器"""

    def __init__(self):
        self.scorer = PlayerScorer()

    def diagnose(self, players: list[dict]) -> dict:
        """生成完整的阵容诊断报告"""
        if not players:
            return {"error": "没有球员数据"}

        outfield = [p for p in players if not self._is_gk(p)]
        gks = [p for p in players if self._is_gk(p)]

        return {
            "squad_size": len(players),
            "outfield_count": len(outfield),
            "gk_count": len(gks),
            "squad_strengths": self._analyze_strengths(outfield),
            "squad_weaknesses": self._analyze_weaknesses(outfield),
            "hidden_issues": self._find_hidden_issues(players),
            "gk_analysis": self._analyze_gk(gks),
            "position_coverage": self._analyze_position_coverage(players),
            "squad_balance": self._analyze_balance(players),
            "best_roles": self._find_best_roles(players),
            "average_age": round(sum(p.get("age", 0) for p in players) / len(players), 1) if players else 0,
        }

    def _is_gk(self, player: dict) -> bool:
        pos = (player.get("position", "") or "").lower()
        return "gk" in pos

    def _is_defender(self, player: dict) -> bool:
        pos = (player.get("position", "") or "").lower()
        return any(p in pos for p in ["dc", "dr", "dl", "wbr", "wbl", "sw", "d ", "d("])

    def _is_midfielder(self, player: dict) -> bool:
        pos = (player.get("position", "") or "").lower()
        return any(p in pos for p in ["mc", "dm", "mr", "ml", "amc", "amr", "aml", "m ", "m("])

    def _is_attacker(self, player: dict) -> bool:
        pos = (player.get("position", "") or "").lower()
        return any(p in pos for p in ["st", "sc", "fc", "amc", "amr", "aml", "am ", "am("])

    def _avg_attr(self, players: list[dict], attr: str) -> float:
        vals = [p.get(attr, 0) or 0 for p in players]
        return round(sum(vals) / len(vals), 1) if vals else 0

    def _analyze_strengths(self, outfield: list[dict]) -> list[dict]:
        """分析阵容优势"""
        strengths = []

        # 速度优势
        avg_pace = self._avg_attr(outfield, "pace")
        avg_acc = self._avg_attr(outfield, "acceleration")
        if avg_pace >= 15:
            strengths.append({
                "category": "speed",
                "title_zh": "顶级速度",
                "detail": f"全队平均 Pace {avg_pace}，Acceleration {avg_acc}",
                "implication": "非常适合快速反击和高位压迫打法",
                "level": "major",
            })
        elif avg_pace >= 13:
            strengths.append({
                "category": "speed",
                "title_zh": "良好的速度",
                "detail": f"全队平均 Pace {avg_pace}",
                "implication": "可以执行中高位防守和转换进攻",
                "level": "minor",
            })

        # 传球能力
        avg_passing = self._avg_attr(outfield, "passing")
        avg_vision = self._avg_attr(outfield, "vision")
        avg_technique = self._avg_attr(outfield, "technique")
        if avg_passing >= 14 and avg_vision >= 13:
            strengths.append({
                "category": "technical",
                "title_zh": "出色的传控能力",
                "detail": f"平均 Passing {avg_passing}, Vision {avg_vision}, Technique {avg_technique}",
                "implication": "适合控球主导的战术体系",
                "level": "major",
            })

        # 创造力
        avg_flair = self._avg_attr(outfield, "flair")
        avg_decisions = self._avg_attr(outfield, "decisions")
        if avg_flair >= 13 and avg_decisions >= 13:
            strengths.append({
                "category": "creativity",
                "title_zh": "富有创造力",
                "detail": f"平均 Flair {avg_flair}, Decisions {avg_decisions}",
                "implication": "适合给予球员更多自由度，打灵活进攻",
                "level": "minor",
            })

        # 防守稳固
        avg_tackling = self._avg_attr(outfield, "tackling")
        avg_positioning = self._avg_attr(outfield, "positioning")
        if avg_tackling >= 14 and avg_positioning >= 14:
            strengths.append({
                "category": "defense",
                "title_zh": "防守稳固",
                "detail": f"平均 Tackling {avg_tackling}, Positioning {avg_positioning}",
                "implication": "防守端值得信赖，可以执行多种防守策略",
                "level": "major",
            })

        # 身高优势
        avg_jumping = self._avg_attr(outfield, "jumping_reach")
        if avg_jumping >= 14:
            strengths.append({
                "category": "physical",
                "title_zh": "空中优势明显",
                "detail": f"平均 Jumping Reach {avg_jumping}",
                "implication": "定位球和传中战术的利器",
                "level": "minor",
            })

        # 工作投入
        avg_workrate = self._avg_attr(outfield, "work_rate")
        avg_stamina = self._avg_attr(outfield, "stamina")
        if avg_workrate >= 14 and avg_stamina >= 14:
            strengths.append({
                "category": "work_rate",
                "title_zh": "勤奋的团队",
                "detail": f"平均 Work Rate {avg_workrate}, Stamina {avg_stamina}",
                "implication": "适合高压逼抢和高强度打法",
                "level": "major",
            })

        return strengths

    def _analyze_weaknesses(self, outfield: list[dict]) -> list[dict]:
        """分析阵容短板"""
        weaknesses = []

        avg_pace = self._avg_attr(outfield, "pace")
        avg_acc = self._avg_attr(outfield, "acceleration")
        if avg_pace <= 12:
            weaknesses.append({
                "category": "speed",
                "title_zh": "速度偏慢",
                "detail": f"全队平均 Pace 仅 {avg_pace}",
                "risk": "高位防线容易被速度型前锋打身后",
                "suggestion": "防线不宜压太高，可考虑使用协防后卫或 Anchor 后腰保护",
                "level": "major" if avg_pace <= 11 else "minor",
            })

        # 防守问题
        defender_pace = self._avg_attr([p for p in outfield if self._is_defender(p)], "pace")
        if defender_pace <= 12:
            weaknesses.append({
                "category": "defender_speed",
                "title_zh": "后卫线速度不足",
                "detail": f"后卫平均 Pace 仅 {defender_pace}",
                "risk": "面对快速前锋非常脆弱",
                "suggestion": "减少高位压迫，中低位防守更安全；引入速度型中卫",
                "level": "major",
            })

        avg_heading = self._avg_attr(outfield, "heading")
        avg_jumping = self._avg_attr(outfield, "jumping_reach")
        if avg_heading <= 11 and avg_jumping <= 11:
            weaknesses.append({
                "category": "aerial",
                "title_zh": "防空能力薄弱",
                "detail": f"平均 Heading {avg_heading}, Jumping Reach {avg_jumping}",
                "risk": "容易被传中和定位球打穿",
                "suggestion": "尽量让对手走中路，减少边路传中机会",
                "level": "minor",
            })

        avg_strength = self._avg_attr(outfield, "strength")
        if avg_strength <= 11:
            weaknesses.append({
                "category": "physical",
                "title_zh": "身体对抗偏弱",
                "detail": f"平均 Strength 仅 {avg_strength}",
                "risk": "在身体对抗激烈的比赛中可能吃亏",
                "suggestion": "多打地面传球，减少身体对抗",
                "level": "minor",
            })

        return weaknesses

    def _find_hidden_issues(self, players: list[dict]) -> list[dict]:
        """发现隐藏问题（不那么明显但可能致命的）"""
        issues = []

        # 检查防守型后腰
        dm_players = [p for p in players if self._is_midfielder(p) and not self._is_attacker(p)]
        dm_tackling = [p for p in dm_players if (p.get("tackling", 0) or 0) >= 13]
        if dm_players and len(dm_tackling) == 0:
            issues.append({
                "category": "dm_protection",
                "title_zh": "缺少防守型中场",
                "detail": "中场球员中没有人 Tackling ≥ 13",
                "risk": "防线前方缺乏保护屏障",
                "suggestion": "考虑引进一名防守型中场 (DM/BWM)，或在战术中用双后腰弥补",
                "severity": "high",
            })

        # 检查左脚球员
        left_footed = [p for p in players if "left" in (p.get("preferred_foot", "") or "").lower()
                       or "左脚" in (p.get("preferred_foot", "") or "")]
        if len(left_footed) < 2:
            issues.append({
                "category": "foot_balance",
                "title_zh": "左脚球员不足",
                "detail": f"全队仅 {len(left_footed)} 名左脚球员",
                "risk": "左路进攻套路受限，尤其是左后卫和左边锋位置",
                "suggestion": "左侧使用 Inverted Winger 或 Inside Forward（右脚内切）弥补",
                "severity": "medium",
            })

        # 检查定位球主罚者
        freekick_takers = [p for p in players if (p.get("free_kicks", 0) or 0) >= 13]
        corner_takers = [p for p in players if (p.get("corners", 0) or 0) >= 13]
        penalty_takers = [p for p in players if (p.get("penalty_taking", 0) or 0) >= 13]
        if not freekick_takers:
            issues.append({
                "category": "set_pieces",
                "title_zh": "缺少定位球主罚者",
                "detail": "无人 Free Kicks ≥ 13",
                "risk": "定位球转化率低",
                "suggestion": "训练中加强定位球练习，或签约定位球专家",
                "severity": "low",
            })

        # 检查队长材料
        leaders = [p for p in players if (p.get("leadership", 0) or 0) >= 15]
        if not leaders:
            issues.append({
                "category": "leadership",
                "title_zh": "缺乏领袖气质",
                "detail": "无人 Leadership ≥ 15",
                "risk": "逆境中球队可能缺乏斗志",
                "suggestion": "选择 Determination 和 Teamwork 最高的球员担任队长",
                "severity": "low",
            })

        # 检查受伤倾向（natural_fitness 低）
        injury_risks = [p for p in players if (p.get("natural_fitness", 0) or 0) <= 10]
        if len(injury_risks) >= 3:
            issues.append({
                "category": "injury_risk",
                "title_zh": "伤病风险",
                "detail": f"{len(injury_risks)} 名球员 Natural Fitness ≤ 10",
                "risk": "密集赛程下容易受伤或体能不足",
                "suggestion": "需要充足的轮换储备，训练强度不宜过高",
                "severity": "medium",
            })

        return issues

    def _analyze_gk(self, gks: list[dict]) -> dict:
        """门将分析"""
        if not gks:
            return {"warning": "没有门将数据", "recommendation": "必须至少有一名门将"}

        best_gk = max(gks, key=lambda p: p.get("reflexes", 0) or 0)
        return {
            "count": len(gks),
            "best_gk": best_gk.get("name"),
            "reflexes": best_gk.get("reflexes", 0),
            "one_on_ones": best_gk.get("one_on_ones", 0),
            "rushing_out": best_gk.get("rushing_out", 0),
            "kicking": best_gk.get("kicking", 0),
            "sweeper_keeper_score": self.scorer.score(best_gk, "SK_S", "GK")["score"],
            "traditional_gk_score": self.scorer.score(best_gk, "G_D", "GK")["score"],
        }

    def _analyze_position_coverage(self, players: list[dict]) -> dict:
        """分析各位置覆盖情况"""
        coverage = {
            "GK": {"count": 0, "players": []},
            "DC": {"count": 0, "players": []},
            "DL": {"count": 0, "players": []},
            "DR": {"count": 0, "players": []},
            "DM": {"count": 0, "players": []},
            "MC": {"count": 0, "players": []},
            "AML": {"count": 0, "players": []},
            "AMR": {"count": 0, "players": []},
            "AMC": {"count": 0, "players": []},
            "ST": {"count": 0, "players": []},
        }

        for p in players:
            pos = (p.get("position", "") or "").lower()
            name = p.get("name", "?")
            for key in coverage:
                if key.lower() in pos:
                    coverage[key]["count"] += 1
                    coverage[key]["players"].append(name)

        # 标记薄弱位置
        thin_positions = []
        for key, data in coverage.items():
            if key == "GK" and data["count"] < 2:
                thin_positions.append({"position": key, "reason": "门将需要至少2人"})
            elif key != "GK" and data["count"] < 2:
                thin_positions.append({"position": key, "reason": "深度不足，受伤即无人可用"})

        return {
            "coverage": coverage,
            "thin_positions": thin_positions,
            "total_coverage_score": max(0, 10 - len(thin_positions)),
        }

    def _analyze_balance(self, players: list[dict]) -> dict:
        """分析阵容年龄和属性平衡"""
        ages = [p.get("age", 0) or 0 for p in players]
        avg_age = round(sum(ages) / len(ages), 1) if ages else 0

        young = len([a for a in ages if a <= 23])
        prime = len([a for a in ages if 24 <= a <= 29])
        veteran = len([a for a in ages if a >= 30])

        balance_msg = ""
        if prime / len(ages) >= 0.5:
            balance_msg = "阵容结构理想，核心球员处于巅峰期"
        elif veteran / len(ages) >= 0.4:
            balance_msg = "阵容偏老化，需要考虑更新换代"
        elif young / len(ages) >= 0.5:
            balance_msg = "阵容年轻有活力但缺乏经验"

        return {
            "average_age": avg_age,
            "young_23_or_under": young,
            "prime_24_29": prime,
            "veteran_30_plus": veteran,
            "assessment": balance_msg,
        }

    def _find_best_roles(self, players: list[dict]) -> list[dict]:
        """找出全队最佳角色组合"""
        top_players = sorted(players, key=lambda p: p.get("current_ability", 0) or 0, reverse=True)[:5]
        result = []
        for p in top_players:
            scores = self.scorer.score_all_roles(p)
            if scores:
                result.append({
                    "player": p.get("name"),
                    "best_role": scores[0]["role_label"],
                    "score": scores[0]["score"],
                    "top3_roles": [s["role_label"] for s in scores[:3]],
                })
        return result
