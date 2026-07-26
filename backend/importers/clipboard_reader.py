"""剪贴板读取器 — 从 FMRTE 复制的内容中解析球员数据

用法：用户在 FMRTE 中 Ctrl+A 全选球员，Ctrl+C 复制，
     然后在应用中点击「从剪贴板导入」。
"""

import re
import io
import csv
from typing import Optional


def parse_fmrte_clipboard(text: str) -> list[dict]:
    """解析 FMRTE 剪贴板内容

    FMRTE 的列表复制出来通常是制表符分隔的表格文本，
    第一行是列头，后面是数据行。
    """
    if not text or len(text) < 50:
        return []

    # 检测分隔符
    first_line = text.strip().split("\n")[0]
    if "\t" in first_line:
        delimiter = "\t"
    elif ";" in first_line:
        delimiter = ";"
    else:
        delimiter = ","

    # 用 CSV reader 解析
    reader = csv.reader(io.StringIO(text), delimiter=delimiter)
    rows = list(reader)

    if len(rows) < 2:
        return []

    # 映射列名（同 FMRTE CSV parser 的映射逻辑）
    from .fmrte_parser import FMRTEParser

    headers = rows[0]
    col_map = FMRTEParser.map_columns(headers)

    if len(col_map) < 3:
        # 列映射不够，尝试更激进的匹配
        col_map = _aggressive_map(headers)

    players = []
    for row in rows[1:]:
        player = FMRTEParser._parse_row(row, col_map)
        if player and player.name:
            players.append(player.to_dict())

    return players


def _aggressive_map(headers: list[str]) -> dict[int, str]:
    """激进的列名匹配 — 尝试模糊匹配"""
    from .fmrte_parser import COLUMN_MAP

    mapping = {}
    for i, h in enumerate(headers):
        clean = h.strip().lower().replace(" ", "_").replace("-", "_")

        # 精确匹配
        if clean in COLUMN_MAP:
            mapping[i] = COLUMN_MAP[clean]
            continue

        # 子串匹配
        for key, val in COLUMN_MAP.items():
            if len(key) > 3 and (key in clean or clean in key):
                mapping[i] = val
                break

    return mapping


def is_fmrte_data(text: str) -> bool:
    """检测剪贴板内容是否是 FMRTE 数据"""
    if not text or len(text) < 100:
        return False

    first_line = text.strip().split("\n")[0].lower()

    # FMRTE 的列头通常包含这些关键词
    fmrte_indicators = [
        "name", "age", "position", "club", "nation",
        "姓名", "年龄", "位置", "俱乐部", "国籍",
        "pace", "acceleration", "finishing", "passing",
        "速度", "爆发", "射门", "传球",
    ]

    matches = sum(1 for ind in fmrte_indicators if ind in first_line)
    return matches >= 2
