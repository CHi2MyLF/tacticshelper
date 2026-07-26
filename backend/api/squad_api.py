"""阵容数据 API"""

from fastapi import APIRouter, HTTPException
from ..database import get_db

router = APIRouter(prefix="/api/squad", tags=["squad"])


@router.get("/{squad_id}/players")
async def get_players(squad_id: int, position: str = None, search: str = None):
    """获取阵容球员列表"""
    db = get_db()
    query = "SELECT * FROM player WHERE squad_id = ?"
    params = [squad_id]

    if position:
        query += " AND position LIKE ?"
        params.append(f"%{position}%")
    if search:
        query += " AND (name LIKE ? OR position LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])

    query += " ORDER BY current_ability DESC"
    rows = db.execute(query, params).fetchall()
    db.close()
    return [dict(r) for r in rows]


@router.get("/{squad_id}/player/{player_id}")
async def get_player(squad_id: int, player_id: int):
    """获取单个球员详细信息"""
    db = get_db()
    row = db.execute(
        "SELECT * FROM player WHERE id = ? AND squad_id = ?",
        (player_id, squad_id),
    ).fetchone()
    db.close()
    if not row:
        raise HTTPException(404, "球员不存在")
    return dict(row)


@router.get("/{squad_id}/stats")
async def get_squad_stats(squad_id: int):
    """获取阵容统计数据"""
    db = get_db()
    players = db.execute(
        "SELECT * FROM player WHERE squad_id = ?", (squad_id,)
    ).fetchall()
    db.close()

    if not players:
        raise HTTPException(404, "阵容不存在")

    players_list = [dict(r) for r in players]
    outfield = [p for p in players_list if "gk" not in (p.get("position", "") or "").lower()]

    def avg(attr):
        vals = [p.get(attr, 0) or 0 for p in outfield]
        return round(sum(vals) / len(vals), 1) if vals else 0

    return {
        "total_players": len(players_list),
        "outfield_players": len(outfield),
        "goalkeepers": len(players_list) - len(outfield),
        "average_age": round(sum(p.get("age", 0) or 0 for p in players_list) / len(players_list), 1),
        "average_ca": round(sum(p.get("current_ability", 0) or 0 for p in players_list) / len(players_list), 0),
        "average_pa": round(sum(p.get("potential_ability", 0) or 0 for p in players_list) / len(players_list), 0),
        "averages": {
            "pace": avg("pace"),
            "acceleration": avg("acceleration"),
            "stamina": avg("stamina"),
            "passing": avg("passing"),
            "tackling": avg("tackling"),
            "finishing": avg("finishing"),
            "dribbling": avg("dribbling"),
            "technique": avg("technique"),
            "work_rate": avg("work_rate"),
        },
    }
