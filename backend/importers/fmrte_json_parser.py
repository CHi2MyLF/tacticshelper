"""FMRTE JSON 导出解析器

FMRTE 导出 JSON 格式示例结构：
{
  "Players": [
    {
      "Name": "Messi",
      "Age": 36,
      ...
      "Attributes": {
        "Technical": { "Corners": 14, "Crossing": 16, ... },
        "Mental": { "Aggression": 7, "Anticipation": 20, ... },
        "Physical": { "Acceleration": 16, "Agility": 18, ... },
        "Goalkeeping": { ... }
      }
    }
  ]
}

也支持扁平格式（老版本FMRTE）：
[
  { "Name": "...", "Corners": 14, "Crossing": 16, ... }
]
"""

import json
from typing import Optional

# JSON key → 统一字段名
JSON_KEY_MAP = {
    # 基本
    "Name": "name", "name": "name",
    "Age": "age", "age": "age",
    "Nation": "nationality", "Nationality": "nationality",
    "Club": "club", "club": "club",
    "Position": "position", "position": "position",
    "BestPosition": "best_position", "best_position": "best_position",
    "PreferredFoot": "preferred_foot", "preferred_foot": "preferred_foot",
    "Height": "height", "height": "height",
    "Weight": "weight", "weight": "weight",
    "Personality": "personality", "personality": "personality",
    "MediaDescription": "media_description",
    "CurrentAbility": "current_ability", "CA": "current_ability",
    "PotentialAbility": "potential_ability", "PA": "potential_ability",
    "Value": "value", "value": "value",
    "Wage": "wage", "wage": "wage",
    "UID": "uid", "uid": "uid",
}

# 属性名映射（去除空格、统一大小写）
ATTR_NAMES = {
    "corners": "corners", "crossing": "crossing", "dribbling": "dribbling",
    "finishing": "finishing", "firsttouch": "first_touch", "first touch": "first_touch",
    "freekicks": "free_kicks", "free kicks": "free_kicks",
    "heading": "heading", "longshots": "long_shots", "long shots": "long_shots",
    "longthrows": "long_throws", "long throws": "long_throws",
    "marking": "marking", "passing": "passing",
    "penaltytaking": "penalty_taking", "penalty taking": "penalty_taking",
    "tackling": "tackling", "technique": "technique",
    "aggression": "aggression", "anticipation": "anticipation",
    "bravery": "bravery", "composure": "composure",
    "concentration": "concentration", "decisions": "decisions",
    "determination": "determination", "flair": "flair",
    "leadership": "leadership", "offtheball": "off_the_ball", "off the ball": "off_the_ball",
    "positioning": "positioning", "teamwork": "teamwork",
    "vision": "vision", "workrate": "work_rate", "work rate": "work_rate",
    "acceleration": "acceleration", "agility": "agility",
    "balance": "balance", "jumpingreach": "jumping_reach", "jumping reach": "jumping_reach",
    "naturalfitness": "natural_fitness", "natural fitness": "natural_fitness",
    "pace": "pace", "stamina": "stamina", "strength": "strength",
    "aerialreach": "aerial_reach", "aerial reach": "aerial_reach",
    "commandofarea": "command_of_area", "command of area": "command_of_area",
    "communication": "communication", "eccentricity": "eccentricity",
    "handling": "handling", "kicking": "kicking",
    "oneonones": "one_on_ones", "one on ones": "one_on_ones",
    "reflexes": "reflexes", "rushingout": "rushing_out", "rushing out": "rushing_out",
    "throwing": "throwing", "tendencytopunch": "tendency_to_punch", "tendency to punch": "tendency_to_punch",
}


def _map_attr_name(key: str) -> Optional[str]:
    """将 FMRTE JSON 的属性名映射到统一字段名"""
    clean = key.strip().lower().replace(" ", "").replace("-", "").replace("_", "")
    if clean in ATTR_NAMES:
        return ATTR_NAMES[clean]
    # 尝试原始
    if key.lower() in ATTR_NAMES:
        return ATTR_NAMES[key.lower()]
    return None


def parse_fmrte_json(content: str) -> list[dict]:
    """解析 FMRTE JSON 导出"""
    data = json.loads(content)

    # 处理不同格式
    players_raw = []

    if isinstance(data, list):
        players_raw = data
    elif isinstance(data, dict):
        # 找包含球员列表的键
        for key in ["Players", "players", "data", "results", "items"]:
            if key in data:
                players_raw = data[key]
                break
        # 如果只有单个球员
        if not players_raw and "Name" in data:
            players_raw = [data]

    if not players_raw:
        return []

    players = []
    for raw in players_raw:
        player = _parse_player(raw)
        if player and player.get("name"):
            players.append(player)

    return players


def _parse_player(raw: dict) -> Optional[dict]:
    """解析单个球员"""
    result = {}

    # 基本字段
    for json_key, field in JSON_KEY_MAP.items():
        if json_key in raw:
            result[field] = raw[json_key]

    # 属性 — 可能在 Attributes 子对象里，也可能平铺
    attrs_sources = []

    if "Attributes" in raw:
        attrs = raw["Attributes"]
        for category in ["Technical", "Mental", "Physical", "Goalkeeping"]:
            if category in attrs:
                attrs_sources.append(attrs[category])
        # 也可能不分category
        if not attrs_sources:
            attrs_sources.append(attrs)

    # 也检查平铺的属性
    attrs_sources.append(raw)

    for source in attrs_sources:
        for key, value in source.items():
            mapped = _map_attr_name(key)
            if mapped and isinstance(value, (int, float)):
                result[mapped] = int(value)

    # 默认值
    for attr in [
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
    ]:
        result.setdefault(attr, 0)

    result.setdefault("age", 0)
    result.setdefault("current_ability", 0)
    result.setdefault("potential_ability", 0)
    result.setdefault("club", "")
    result.setdefault("position", "")

    return result
