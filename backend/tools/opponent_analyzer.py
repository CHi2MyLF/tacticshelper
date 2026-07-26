"""对手分析器 — 分析对手特征并生成针对性调整"""

import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class OpponentAnalyzer:
    """对手分析器"""

    def __init__(self):
        with open(DATA_DIR / "counter_rules.json", "r", encoding="utf-8") as f:
            self.rules = json.load(f)
        with open(DATA_DIR / "formations.json", "r", encoding="utf-8") as f:
            self.formations = json.load(f)["formations"]
        with open(DATA_DIR / "styles.json", "r", encoding="utf-8") as f:
            self.styles = json.load(f)["styles"]

    def analyze(
        self,
        opponent_info: dict,
        current_tactic: dict = None,
        squad_strengths: list[dict] = None,
    ) -> dict:
        """
        分析对手并生成针对性方案

        参数:
            opponent_info: {name, formation, style, strengths, weaknesses, danger_players}
            current_tactic: 当前战术方案
            squad_strengths: 我方阵容优势

        返回:
            {
                "opponent_profile": {...},
                "key_threats": [...],
                "vulnerabilities": [...],
                "tactical_adjustments": [...],
                "individual_marking": [...],
                "recommended_approach": "...",
            }
        """
        opponent = {
            "name": opponent_info.get("name", "未知对手"),
            "formation": opponent_info.get("formation", ""),
            "style": opponent_info.get("style", ""),
            "strengths": opponent_info.get("strengths", ""),
            "weaknesses": opponent_info.get("weaknesses", ""),
            "danger_players": opponent_info.get("danger_players", []),
        }

        # 分析威胁
        threats = self._analyze_threats(opponent)

        # 分析弱点
        vulnerabilities = self._analyze_vulnerabilities(opponent)

        # 生成针对性调整
        adjustments = self._generate_adjustments(opponent, threats, vulnerabilities, current_tactic)

        # 推荐盯人方案
        marking = self._recommend_marking(opponent.get("danger_players", []))

        # 生成综合建议
        approach = self._build_approach(opponent, threats, vulnerabilities, adjustments)

        return {
            "opponent_profile": opponent,
            "key_threats": threats,
            "vulnerabilities": vulnerabilities,
            "tactical_adjustments": adjustments,
            "individual_marking": marking,
            "recommended_approach": approach,
        }

    def _analyze_threats(self, opponent: dict) -> list[dict]:
        """分析对手的威胁点"""
        threats = []

        # 基于阵型的威胁分析
        formation_threats = {
            "433": [
                {"area": "边路快速反击", "detail": "433的边锋+边后卫组合能快速打穿边路"},
                {"area": "中路控制", "detail": "三中场配置在人数上控制中路"},
            ],
            "4231": [
                {"area": "AMC区域", "detail": "前腰在双后腰和后卫线之间的空间活动"},
                {"area": "边锋内切", "detail": "内锋内切后可直接射门"},
            ],
            "442": [
                {"area": "双前锋配合", "detail": "双前锋互相做球，防守难度增加"},
                {"area": "边路传中", "detail": "传统边锋+双前锋的传中威胁"},
            ],
            "352": [
                {"area": "翼卫插上", "detail": "翼卫是主要的宽度来源，前插频繁"},
                {"area": "双前锋+中场后排", "detail": "三后卫体系人数劣势时反击"},
            ],
        }

        opponent_formation = opponent.get("formation", "")
        if opponent_formation in formation_threats:
            threats.extend(formation_threats[opponent_formation])

        # 基于风格的分析
        style = opponent.get("style", "").lower()
        if "gegenpress" in style or "高压" in style or "压迫" in style:
            threats.append({"area": "高位压迫", "detail": "对手会高强度逼抢你的后场出球"})
        if "tiki" in style or "控球" in style:
            threats.append({"area": "控球消耗", "detail": "对手会长时间控球，消耗你的体力"})
        if "counter" in style or "反击" in style:
            threats.append({"area": "快速反击", "detail": "对手会利用你压上后的空档快速反击"})

        # 危险球员
        for dp in opponent.get("danger_players", []):
            threats.append({
                "area": f"危险球员: {dp.get('name', '?')}",
                "detail": f"位置 {dp.get('position', '?')}，需要注意特殊盯防",
                "player": dp,
            })

        return threats

    def _analyze_vulnerabilities(self, opponent: dict) -> list[dict]:
        """分析对手的弱点"""
        vulnerabilities = []

        weaknesses = opponent.get("weaknesses", "")
        opponent_formation = opponent.get("formation", "")

        # 阵型弱点
        formation_weaknesses = {
            "433": [
                {"area": "边后卫身后", "detail": "433边后卫助攻后身后空档大，尤其是面对反击时"},
                {"area": "单后腰覆盖不足", "detail": "单后腰无法同时覆盖左右两侧"},
            ],
            "4231": [
                {"area": "双后腰之间", "detail": "双后腰如果站位过宽，中间会有空隙"},
                {"area": "前腰回防", "detail": "有些AMC回防意识差，让中场实际只有2人"},
            ],
            "442": [
                {"area": "中场人数劣势", "detail": "双中场面对三中场阵型时人数不足"},
                {"area": "中后卫之间", "detail": "双前锋拉扯下中卫之间的空隙"},
            ],
            "352": [
                {"area": "翼卫身后", "detail": "翼卫压上后身后大片空档"},
                {"area": "三中卫边路", "detail": "边中卫面对速度型边锋时吃力"},
            ],
        }

        if opponent_formation in formation_weaknesses:
            vulnerabilities.extend(formation_weaknesses[opponent_formation])

        # 文字描述的弱点
        if weaknesses:
            vulnerabilities.append({"area": "已知弱点", "detail": weaknesses})

        return vulnerabilities

    def _generate_adjustments(
        self, opponent: dict, threats: list[dict],
        vulnerabilities: list[dict], current_tactic: dict = None,
    ) -> list[dict]:
        """生成针对性战术调整"""
        adjustments = []

        opponent_formation = opponent.get("formation", "")
        opponent_style = opponent.get("style", "").lower()

        # 针对阵型的调整
        if "433" in opponent_formation:
            adjustments.append({
                "category": "formation",
                "instruction": "使用中场人数对等的阵型（433/4231）",
                "reason": "避免在中场被对手3人压制",
                "priority": "high",
            })
        if "4231" in opponent_formation:
            adjustments.append({
                "category": "formation",
                "instruction": "设置后腰专门盯防对方AMC",
                "reason": "限制对手前腰的发挥是克制4231的关键",
                "priority": "high",
            })
        if "442" in opponent_formation:
            adjustments.append({
                "category": "formation",
                "instruction": "打三中场阵型（433/352）控制中场",
                "reason": "442中场只有2人，三中场可以轻松控制",
                "priority": "medium",
            })

        # 针对风格的调整
        if "高压" in opponent_style or "gegenpress" in opponent_style:
            adjustments.append({
                "category": "possession",
                "instruction": "减少后场短传，门将开大脚找前锋",
                "reason": "避免在后场被压迫抢断导致失球",
                "priority": "high",
            })
            adjustments.append({
                "category": "possession",
                "instruction": "打对手压上后的身后空档",
                "reason": "高位压迫必然留下后场空间",
                "priority": "high",
            })
        if "控球" in opponent_style or "tiki" in opponent_style:
            adjustments.append({
                "category": "defense",
                "instruction": "保持阵型紧凑，不要贸然上抢",
                "reason": "控球型球队会利用你失位后的空间",
                "priority": "medium",
            })
            adjustments.append({
                "category": "transition",
                "instruction": "断球后快速反击，不要给对手回防时间",
                "reason": "控球球队阵型散开时最脆弱",
                "priority": "high",
            })
        if "反击" in opponent_style or "counter" in opponent_style:
            adjustments.append({
                "category": "defense",
                "instruction": "进攻时留2-3人保护，不要全线压上",
                "reason": "防止被断球后快速反击",
                "priority": "high",
            })
            adjustments.append({
                "category": "possession",
                "instruction": "耐心控球，等待对手露出破绽",
                "reason": "反击型球队不喜欢主动逼抢",
                "priority": "medium",
            })

        # 针对性盯人
        danger_players = opponent.get("danger_players", [])
        for dp in danger_players:
            pos = dp.get("position", "")
            adjustments.append({
                "category": "marking",
                "instruction": f"对 {dp.get('name', '?')} 实施针对性盯防",
                "reason": f"限制对手核心球员 {dp.get('name')} 的发挥",
                "priority": "critical" if dp.get("is_star") else "high",
            })

        return adjustments

    def _recommend_marking(self, danger_players: list[dict]) -> list[dict]:
        """推荐盯人方案"""
        marking = []
        for dp in danger_players:
            position = dp.get("position", "")
            marking.append({
                "target_player": dp.get("name", "?"),
                "target_position": position,
                "instruction": "tight_marking" if position in ["AMC", "ST", "FC"] else "closing_down",
                "instruction_zh": "贴身盯防" if position in ["AMC", "ST", "FC"] else "紧逼压迫",
                "trigger_press": "always",
            })
        return marking

    def _build_approach(
        self, opponent: dict, threats: list[dict],
        vulnerabilities: list[dict], adjustments: list[dict],
    ) -> str:
        """生成综合战术建议"""
        approach_parts = [f"对阵 {opponent.get('name', '对手')} 的战术方针："]

        # 根据调整生成总体策略
        high_priority = [a for a in adjustments if a.get("priority") in ("high", "critical")]
        if high_priority:
            approach_parts.append("\n核心要点：")
            for adj in high_priority[:3]:
                approach_parts.append(f"• {adj['instruction']} — {adj['reason']}")

        if vulnerabilities:
            approach_parts.append(f"\n对手弱点：")
            for v in vulnerabilities[:3]:
                if not v["detail"].startswith("已知"):
                    approach_parts.append(f"• {v['detail']}")

        if threats:
            approach_parts.append(f"\n需要警惕：")
            for t in threats[:3]:
                if not t["area"].startswith("危险球员"):
                    approach_parts.append(f"• {t['detail']}")

        return "\n".join(approach_parts)
