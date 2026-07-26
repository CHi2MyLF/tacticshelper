"""SQLite 数据库管理"""

import sqlite3
import os
from pathlib import Path
from .config import DB_PATH

DB_PATH.parent.mkdir(parents=True, exist_ok=True)

SCHEMA = """
CREATE TABLE IF NOT EXISTS squad (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    club_name TEXT,
    import_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS player (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    squad_id INTEGER NOT NULL,
    uid TEXT,
    name TEXT NOT NULL,
    age INTEGER,
    nationality TEXT,
    club TEXT,
    position TEXT,
    best_position TEXT,
    preferred_foot TEXT,
    height INTEGER,
    weight INTEGER,
    personality TEXT,
    media_description TEXT,
    current_ability INTEGER,
    potential_ability INTEGER,
    value TEXT,
    wage TEXT,
    extra_json TEXT,
    -- 技术属性
    corners INTEGER, crossing INTEGER, dribbling INTEGER, finishing INTEGER,
    first_touch INTEGER, free_kicks INTEGER, heading INTEGER, long_shots INTEGER,
    long_throws INTEGER, marking INTEGER, passing INTEGER, penalty_taking INTEGER,
    tackling INTEGER, technique INTEGER,
    -- 精神属性
    aggression INTEGER, anticipation INTEGER, bravery INTEGER, composure INTEGER,
    concentration INTEGER, decisions INTEGER, determination INTEGER, flair INTEGER,
    leadership INTEGER, off_the_ball INTEGER, positioning INTEGER, teamwork INTEGER,
    vision INTEGER, work_rate INTEGER,
    -- 身体属性
    acceleration INTEGER, agility INTEGER, balance INTEGER, jumping_reach INTEGER,
    natural_fitness INTEGER, pace INTEGER, stamina INTEGER, strength INTEGER,
    -- 门将属性
    aerial_reach INTEGER, command_of_area INTEGER, communication INTEGER,
    eccentricity INTEGER, handling INTEGER, kicking INTEGER, one_on_ones INTEGER,
    reflexes INTEGER, rushing_out INTEGER, throwing INTEGER, tendency_to_punch INTEGER,
    FOREIGN KEY (squad_id) REFERENCES squad(id)
);

CREATE TABLE IF NOT EXISTS tactic (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    squad_id INTEGER NOT NULL,
    name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    formation TEXT NOT NULL,
    mentality TEXT,
    attacking_style TEXT,
    defensive_style TEXT,
    instructions_json TEXT,
    player_roles_json TEXT,
    is_active INTEGER DEFAULT 1,
    FOREIGN KEY (squad_id) REFERENCES squad(id)
);

CREATE TABLE IF NOT EXISTS opponent (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    league TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    formation TEXT,
    playing_style TEXT,
    strength_notes TEXT,
    weakness_notes TEXT,
    danger_players_json TEXT
);

CREATE TABLE IF NOT EXISTS match_plan (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tactic_id INTEGER NOT NULL,
    opponent_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    adjustments_json TEXT,
    notes TEXT,
    FOREIGN KEY (tactic_id) REFERENCES tactic(id),
    FOREIGN KEY (opponent_id) REFERENCES opponent(id)
);

CREATE TABLE IF NOT EXISTS chat_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    squad_id INTEGER,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    tool_calls_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (squad_id) REFERENCES squad(id)
);

CREATE TABLE IF NOT EXISTS user_preferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    squad_id INTEGER,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    FOREIGN KEY (squad_id) REFERENCES squad(id)
);

CREATE INDEX IF NOT EXISTS idx_player_squad ON player(squad_id);
CREATE INDEX IF NOT EXISTS idx_player_position ON player(position);
CREATE INDEX IF NOT EXISTS idx_tactic_squad ON tactic(squad_id);
CREATE INDEX IF NOT EXISTS idx_chat_squad ON chat_history(squad_id);
"""


def get_db() -> sqlite3.Connection:
    """获取数据库连接"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    """初始化数据库"""
    conn = get_db()
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()


def dict_from_row(row: sqlite3.Row) -> dict:
    """将 sqlite3.Row 转为 dict"""
    if row is None:
        return None
    return dict(row)


def dicts_from_rows(rows: list[sqlite3.Row]) -> list[dict]:
    """将 sqlite3.Row 列表转为 dict 列表"""
    return [dict(row) for row in rows]
