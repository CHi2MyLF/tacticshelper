"""FM24 HTML 导出解析器

解析 FM24 通过 Ctrl+P → Web Page 导出的 HTML 文件。
格式为标准的 <table> 含 <thead><tbody> 结构。
"""

import re
from html.parser import HTMLParser
from typing import Optional


class FM24HTMLTableParser(HTMLParser):
    """解析 FM24 HTML 导出中的表格数据"""

    def __init__(self):
        super().__init__()
        self.in_table = False
        self.in_thead = False
        self.in_tbody = False
        self.in_row = False
        self.in_cell = False
        self.headers = []
        self.rows = []
        self.current_row = []
        self.current_cell = ""
        self.table_count = 0

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self.table_count += 1
            self.in_table = True
        elif tag == "thead" and self.in_table:
            self.in_thead = True
        elif tag == "tbody" and self.in_table:
            self.in_tbody = True
        elif tag == "tr" and (self.in_thead or self.in_tbody):
            self.in_row = True
            self.current_row = []
        elif tag in ("td", "th") and self.in_row:
            self.in_cell = True
            self.current_cell = ""

    def handle_endtag(self, tag):
        if tag == "table":
            self.in_table = False
        elif tag == "thead":
            self.in_thead = False
        elif tag == "tbody":
            self.in_tbody = False
        elif tag == "tr" and self.in_row:
            self.in_row = False
            if self.in_thead:
                self.headers = self.current_row
            elif self.in_tbody:
                # 跳过空行和分隔行
                if any(c.strip() for c in self.current_row):
                    self.rows.append(self.current_row)
        elif tag in ("td", "th") and self.in_cell:
            self.in_cell = False
            self.current_row.append(self.current_cell.strip())

    def handle_data(self, data):
        if self.in_cell:
            self.current_cell += data


def _strip_html_tags(text: str) -> str:
    """去除 HTML 标签"""
    return re.sub(r"<[^>]+>", "", text)


def parse_fm24_html(content: str) -> list[dict]:
    """解析 FM24 HTML 导出内容

    返回球员数据 dict 列表（与 FMRTE CSV 解析器输出兼容）
    """
    parser = FM24HTMLTableParser()
    parser.feed(content)

    if not parser.headers or not parser.rows:
        # 尝试更宽松的解析：直接找所有 table
        tables = re.findall(r"<table[^>]*>(.*?)</table>", content, re.DOTALL | re.IGNORECASE)
        for table_html in tables:
            # 提取表头
            headers = []
            th_match = re.findall(r"<th[^>]*>(.*?)</th>", table_html, re.DOTALL | re.IGNORECASE)
            if th_match:
                headers = [_strip_html_tags(h) for h in th_match]

            # 提取数据行
            rows = []
            tr_matches = re.findall(r"<tr[^>]*>(.*?)</tr>", table_html, re.DOTALL | re.IGNORECASE)
            for tr in tr_matches:
                cells = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.DOTALL | re.IGNORECASE)
                if cells:
                    rows.append([_strip_html_tags(c) for c in cells])

            if headers and rows:
                parser.headers = headers
                parser.rows = rows
                break

    if not parser.headers or not parser.rows:
        return []

    # 映射列名（复用 FMRTE parser 的映射逻辑）
    from .fmrte_parser import FMRTEParser, NUMERIC_FIELDS

    col_map = FMRTEParser.map_columns(parser.headers)

    # 如果标准映射不够，做激进匹配
    if len(col_map) < 3:
        col_map = _aggressive_fm_map(parser.headers)

    if len(col_map) < 3:
        return []

    players = []
    for row in parser.rows:
        player = FMRTEParser._parse_row(row, col_map)
        if player and player.name:
            # 跳过表头重复行
            if player.name.lower() in ("name", "姓名", "名字"):
                continue
            players.append(player.to_dict())

    return players


def _aggressive_fm_map(headers: list[str]) -> dict[int, str]:
    """FM24 HTML 列名的激进匹配"""
    from .fmrte_parser import COLUMN_MAP

    mapping = {}
    for i, h in enumerate(headers):
        clean = h.strip().lower()

        # 精确/子串匹配
        for key, val in COLUMN_MAP.items():
            if len(key) > 2:
                # 检查 key 是否在 clean 中，或 clean 是否在 key 中
                if key in clean or clean in key:
                    mapping[i] = val
                    break

        # FM24 特有的列名
        fm_specific = {
            "inf": "position", "information": "position",
            "best position": "best_position", "best pos.": "best_position",
            "pref foot": "preferred_foot", "preferred foot": "preferred_foot",
            "nat": "nationality", "nation": "nationality",
            "personality": "personality", "media handling": "media_description",
            "transfer value": "value", "value": "value",
            "wage": "wage", "weekly wage": "wage", "salary": "wage",
            "height": "height", "weight": "weight",
            "pac": "pace", "acc": "acceleration", "sta": "stamina",
            "str": "strength", "agi": "agility", "bal": "balance",
            "jum": "jumping_reach", "nat fit": "natural_fitness",
            "cor": "corners", "cro": "crossing", "dri": "dribbling",
            "fin": "finishing", "fir": "first_touch", "fre": "free_kicks",
            "hea": "heading", "lon": "long_shots", "l th": "long_throws",
            "mar": "marking", "pas": "passing", "pen": "penalty_taking",
            "tck": "tackling", "tec": "technique",
            "agg": "aggression", "ant": "anticipation", "bra": "bravery",
            "cmp": "composure", "cnt": "concentration", "dec": "decisions",
            "det": "determination", "fla": "flair", "ldr": "leadership",
            "otb": "off_the_ball", "pos": "positioning", "tea": "teamwork",
            "vis": "vision", "wor": "work_rate",
            "ref": "reflexes", "han": "handling", "1v1": "one_on_ones",
            "aer": "aerial_reach", "com": "command_of_area",
            "kic": "kicking", "thr": "throwing",
        }

        if i not in mapping:
            for fm_key, val in fm_specific.items():
                if fm_key in clean:
                    mapping[i] = val
                    break

    return mapping
