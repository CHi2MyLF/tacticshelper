"""FMRTE CSV 解析器 — 支持中英文列名自适应"""

import csv
import io
from typing import Optional
from dataclasses import dataclass, field

# 属性列名映射：英文名 + 中文名 → 统一字段名
COLUMN_MAP = {
    # 基本信息
    "name": "name", "姓名": "name", "名字": "name",
    "uid": "uid", "unique_id": "uid", "id": "uid",
    "age": "age", "年龄": "age",
    "nationality": "nationality", "国籍": "nationality", "nation": "nationality",
    "club": "club", "俱乐部": "club", "球队": "club",
    "position": "position", "位置": "position",
    "best_position": "best_position", "最佳位置": "best_position",
    "preferred_foot": "preferred_foot", "惯用脚": "preferred_foot",
    "height": "height", "身高": "height",
    "weight": "weight", "体重": "weight",
    "personality": "personality", "性格": "personality", "个性": "personality",
    "media_description": "media_description", "媒体描述": "media_description",

    # 技术属性
    "corners": "corners", "角球": "corners",
    "crossing": "crossing", "传中": "crossing",
    "dribbling": "dribbling", "盘带": "dribbling",
    "finishing": "finishing", "射门": "finishing",
    "first_touch": "first_touch", "停球": "first_touch", "接球": "first_touch",
    "free_kicks": "free_kicks", "free_kick_taking": "free_kicks", "任意球": "free_kicks",
    "heading": "heading", "头球": "heading",
    "long_shots": "long_shots", "远射": "long_shots",
    "long_throws": "long_throws", "界外球": "long_throws",
    "marking": "marking", "盯人": "marking",
    "passing": "passing", "传球": "passing",
    "penalty_taking": "penalty_taking", "penalties": "penalty_taking", "点球": "penalty_taking",
    "tackling": "tackling", "抢断": "tackling", "铲球": "tackling",
    "technique": "technique", "技术": "technique",

    # 精神属性
    "aggression": "aggression", "侵略性": "aggression",
    "anticipation": "anticipation", "预判": "anticipation",
    "bravery": "bravery", "勇敢": "bravery",
    "composure": "composure", "镇定": "composure",
    "concentration": "concentration", "集中": "concentration",
    "decisions": "decisions", "决断": "decisions",
    "determination": "determination", "决心": "determination",
    "flair": "flair", "才华": "flair",
    "leadership": "leadership", "领导力": "leadership",
    "off_the_ball": "off_the_ball", "无球跑动": "off_the_ball", "跑位": "off_the_ball",
    "positioning": "positioning", "防守站位": "positioning", "站位": "positioning",
    "teamwork": "teamwork", "团队合作": "teamwork",
    "vision": "vision", "视野": "vision",
    "work_rate": "work_rate", "工作投入": "work_rate",

    # 身体属性
    "acceleration": "acceleration", "爆发力": "acceleration",
    "agility": "agility", "灵活": "agility",
    "balance": "balance", "平衡": "balance",
    "jumping_reach": "jumping_reach", "jumping": "jumping_reach", "弹跳": "jumping_reach",
    "natural_fitness": "natural_fitness", "体质": "natural_fitness",
    "pace": "pace", "速度": "pace",
    "stamina": "stamina", "耐力": "stamina",
    "strength": "strength", "强壮": "strength",

    # 门将属性
    "aerial_reach": "aerial_reach", "aerial_ability": "aerial_reach", "制空范围": "aerial_reach",
    "command_of_area": "command_of_area", "指挥防守": "command_of_area",
    "communication": "communication", "沟通": "communication",
    "eccentricity": "eccentricity", "神经指数": "eccentricity",
    "handling": "handling", "手控球": "handling",
    "kicking": "kicking", "大脚开球": "kicking",
    "one_on_ones": "one_on_ones", "一对一": "one_on_ones",
    "reflexes": "reflexes", "反应": "reflexes",
    "rushing_out": "rushing_out", "出击": "rushing_out",
    "throwing": "throwing", "手抛球": "throwing",
    "tendency_to_punch": "tendency_to_punch", "击球倾向": "tendency_to_punch",

    # Current Ability / Potential Ability
    "current_ability": "current_ability", "ca": "current_ability", "当前能力": "current_ability",
    "potential_ability": "potential_ability", "pa": "potential_ability", "潜力": "potential_ability",

    # 身价 / 工资
    "value": "value", "身价": "value",
    "wage": "wage", "工资": "wage", "周薪": "wage",
}

# 数值型字段（解析为 int）
NUMERIC_FIELDS = {
    "age", "height", "weight",
    "corners", "crossing", "dribbling", "finishing", "first_touch",
    "free_kicks", "heading", "long_shots", "long_throws", "marking",
    "passing", "penalty_taking", "tackling", "technique",
    "aggression", "anticipation", "bravery", "composure", "concentration",
    "decisions", "determination", "flair", "leadership", "off_the_ball",
    "positioning", "teamwork", "vision", "work_rate",
    "acceleration", "agility", "balance", "jumping_reach",
    "natural_fitness", "pace", "stamina", "strength",
    "aerial_reach", "command_of_area", "communication", "eccentricity",
    "handling", "kicking", "one_on_ones", "reflexes", "rushing_out",
    "throwing", "tendency_to_punch",
    "current_ability", "potential_ability",
}

# 所有技术属性
TECHNICAL_ATTRS = [
    "corners", "crossing", "dribbling", "finishing", "first_touch",
    "free_kicks", "heading", "long_shots", "long_throws", "marking",
    "passing", "penalty_taking", "tackling", "technique"
]

# 所有精神属性
MENTAL_ATTRS = [
    "aggression", "anticipation", "bravery", "composure", "concentration",
    "decisions", "determination", "flair", "leadership", "off_the_ball",
    "positioning", "teamwork", "vision", "work_rate"
]

# 所有身体属性
PHYSICAL_ATTRS = [
    "acceleration", "agility", "balance", "jumping_reach",
    "natural_fitness", "pace", "stamina", "strength"
]

# 所有门将属性
GK_ATTRS = [
    "aerial_reach", "command_of_area", "communication", "eccentricity",
    "handling", "kicking", "one_on_ones", "reflexes", "rushing_out",
    "throwing", "tendency_to_punch"
]


@dataclass
class PlayerData:
    """统一的球员数据模型"""
    uid: str = ""
    name: str = ""
    age: int = 0
    nationality: str = ""
    club: str = ""
    position: str = ""
    best_position: str = ""
    preferred_foot: str = ""
    height: int = 0
    weight: int = 0
    personality: str = ""
    media_description: str = ""
    current_ability: int = 0
    potential_ability: int = 0
    value: str = ""
    wage: str = ""
    # 属性
    corners: int = 0
    crossing: int = 0
    dribbling: int = 0
    finishing: int = 0
    first_touch: int = 0
    free_kicks: int = 0
    heading: int = 0
    long_shots: int = 0
    long_throws: int = 0
    marking: int = 0
    passing: int = 0
    penalty_taking: int = 0
    tackling: int = 0
    technique: int = 0
    aggression: int = 0
    anticipation: int = 0
    bravery: int = 0
    composure: int = 0
    concentration: int = 0
    decisions: int = 0
    determination: int = 0
    flair: int = 0
    leadership: int = 0
    off_the_ball: int = 0
    positioning: int = 0
    teamwork: int = 0
    vision: int = 0
    work_rate: int = 0
    acceleration: int = 0
    agility: int = 0
    balance: int = 0
    jumping_reach: int = 0
    natural_fitness: int = 0
    pace: int = 0
    stamina: int = 0
    strength: int = 0
    aerial_reach: int = 0
    command_of_area: int = 0
    communication: int = 0
    eccentricity: int = 0
    handling: int = 0
    kicking: int = 0
    one_on_ones: int = 0
    reflexes: int = 0
    rushing_out: int = 0
    throwing: int = 0
    tendency_to_punch: int = 0
    # 额外数据
    extra: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "uid": self.uid, "name": self.name, "age": self.age,
            "nationality": self.nationality, "club": self.club,
            "position": self.position, "best_position": self.best_position,
            "preferred_foot": self.preferred_foot,
            "height": self.height, "weight": self.weight,
            "personality": self.personality, "media_description": self.media_description,
            "current_ability": self.current_ability, "potential_ability": self.potential_ability,
            "value": self.value, "wage": self.wage,
            "corners": self.corners, "crossing": self.crossing, "dribbling": self.dribbling,
            "finishing": self.finishing, "first_touch": self.first_touch,
            "free_kicks": self.free_kicks, "heading": self.heading,
            "long_shots": self.long_shots, "long_throws": self.long_throws,
            "marking": self.marking, "passing": self.passing,
            "penalty_taking": self.penalty_taking, "tackling": self.tackling,
            "technique": self.technique,
            "aggression": self.aggression, "anticipation": self.anticipation,
            "bravery": self.bravery, "composure": self.composure,
            "concentration": self.concentration, "decisions": self.decisions,
            "determination": self.determination, "flair": self.flair,
            "leadership": self.leadership, "off_the_ball": self.off_the_ball,
            "positioning": self.positioning, "teamwork": self.teamwork,
            "vision": self.vision, "work_rate": self.work_rate,
            "acceleration": self.acceleration, "agility": self.agility,
            "balance": self.balance, "jumping_reach": self.jumping_reach,
            "natural_fitness": self.natural_fitness, "pace": self.pace,
            "stamina": self.stamina, "strength": self.strength,
            "aerial_reach": self.aerial_reach, "command_of_area": self.command_of_area,
            "communication": self.communication, "eccentricity": self.eccentricity,
            "handling": self.handling, "kicking": self.kicking,
            "one_on_ones": self.one_on_ones, "reflexes": self.reflexes,
            "rushing_out": self.rushing_out, "throwing": self.throwing,
            "tendency_to_punch": self.tendency_to_punch,
        }

    def get_attr(self, name: str) -> int:
        """获取指定属性值"""
        return getattr(self, name, 0)

    def is_gk(self) -> bool:
        """判断是否为门将"""
        pos = self.position.lower()
        return "gk" in pos or "门将" in pos

    def is_defender(self) -> bool:
        pos = self.position.lower()
        return any(p in pos for p in ["d ", "d(", "dc", "dr", "dl", "dcr", "dcl", "wbr", "wbl", "sw", "cwb"])

    def is_midfielder(self) -> bool:
        pos = self.position.lower()
        return any(p in pos for p in ["m ", "m(", "mc", "mr", "ml", "dm", "amc", "amr", "aml"])

    def is_attacker(self) -> bool:
        pos = self.position.lower()
        return any(p in pos for p in ["st", "amc", "amr", "aml", "am ", "am(", "fc", "sc", "前锋"])


class FMRTEParser:
    """FMRTE CSV 解析器"""

    @staticmethod
    def detect_delimiter(first_line: str) -> str:
        """检测分隔符"""
        if first_line.count(";") > first_line.count(","):
            return ";"
        if first_line.count("\t") > first_line.count(","):
            return "\t"
        return ","

    @staticmethod
    def map_columns(headers: list[str]) -> dict[int, str]:
        """将 CSV 列头映射到统一字段名"""
        mapping = {}
        for i, header in enumerate(headers):
            clean = header.strip().lower().replace(" ", "_").replace("-", "_")
            if clean in COLUMN_MAP:
                mapping[i] = COLUMN_MAP[clean]
        return mapping

    @classmethod
    def parse_csv(cls, content: str) -> list[PlayerData]:
        """解析 CSV 内容，返回球员数据列表"""
        lines = content.strip().split("\n")
        if len(lines) < 2:
            raise ValueError("CSV 内容为空或只有表头")

        delimiter = cls.detect_delimiter(lines[0])
        reader = csv.reader(io.StringIO(content), delimiter=delimiter)

        headers = next(reader)
        col_map = cls.map_columns(headers)

        if len(col_map) < 5:
            raise ValueError(
                f"未能识别足够的属性列。检测到 {len(col_map)} 个已知列。"
                f"\n表头: {headers[:10]}..."
                f"\n请确认 CSV 文件来自 FMRTE 导出。"
            )

        players = []
        for row in reader:
            player = cls._parse_row(row, col_map)
            if player and player.name:
                players.append(player)

        return players

    @classmethod
    def _parse_row(cls, row: list[str], col_map: dict[int, str]) -> Optional[PlayerData]:
        """解析单行数据"""
        player = PlayerData()
        data = {}

        for i, value in enumerate(row):
            if i not in col_map:
                continue
            field = col_map[i]
            value = value.strip().strip('"').strip("'")

            if field in NUMERIC_FIELDS:
                try:
                    data[field] = int(value) if value else 0
                except ValueError:
                    data[field] = 0
            else:
                data[field] = value

        # 设置属性
        for field, value in data.items():
            if hasattr(player, field):
                setattr(player, field, value)

        return player

    @classmethod
    def parse_file(cls, filepath: str) -> list[PlayerData]:
        """解析 CSV 文件"""
        with open(filepath, "r", encoding="utf-8-sig") as f:
            content = f.read()
        return cls.parse_csv(content)


def import_csv(content: str) -> list[dict]:
    """便捷函数：导入 CSV 并返回 dict 列表"""
    players = FMRTEParser.parse_csv(content)
    return [p.to_dict() for p in players]
