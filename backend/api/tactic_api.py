"""战术管理 API"""

from fastapi import APIRouter
from ..database import get_db

router = APIRouter(prefix="/api/tactic", tags=["tactic"])


@router.get("/list/{squad_id}")
async def list_tactics(squad_id: int):
    """获取阵容的战术历史"""
    db = get_db()
    rows = db.execute(
        "SELECT * FROM tactic WHERE squad_id = ? ORDER BY created_at DESC",
        (squad_id,),
    ).fetchall()
    db.close()
    return [dict(r) for r in rows]


@router.get("/{tactic_id}")
async def get_tactic(tactic_id: int):
    """获取单个战术"""
    db = get_db()
    row = db.execute(
        "SELECT * FROM tactic WHERE id = ?", (tactic_id,)
    ).fetchone()
    db.close()
    return dict(row) if row else None
