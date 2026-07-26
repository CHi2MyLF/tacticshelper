"""数据导入 API"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Optional

from ..importers.fmrte_parser import FMRTEParser
from ..importers.clipboard_reader import parse_fmrte_clipboard, is_fmrte_data
from ..importers.fm24_html_parser import parse_fm24_html
from ..database import get_db, init_db

router = APIRouter(prefix="/api/import", tags=["import"])


class ImportResult(BaseModel):
    success: bool
    squad_id: int
    player_count: int
    message: str
    sample_players: list[dict] = []


def _save_to_db(players: list, name: str) -> ImportResult:
    """将解析后的球员数据存入数据库"""
    if not players:
        raise HTTPException(400, "未解析到任何球员数据")

    # 确保 players 是统一的 dict 列表
    clean_players = []
    for p in players:
        if isinstance(p, dict):
            clean_players.append(p)
        elif hasattr(p, "to_dict"):
            clean_players.append(p.to_dict())
        elif isinstance(p, str):
            # 不应该出现字符串，跳过
            continue
        else:
            clean_players.append(dict(p) if hasattr(p, "__iter__") else {})

    if not clean_players:
        raise HTTPException(400, "数据格式错误，请检查来源")

    db = get_db()
    init_db()

    first = clean_players[0]
    club = first.get("club", "") or "未知俱乐部"

    cursor = db.execute(
        "INSERT INTO squad (name, club_name) VALUES (?, ?)",
        (name, club),
    )
    squad_id = cursor.lastrowid

    # 构建 INSERT 的列名（取所有球员属性的并集）
    all_keys = set()
    for p in clean_players:
        all_keys.update(p.keys())
    all_keys.add("squad_id")
    # 去除数据库中不存在的列
    valid_cols = {k for k in all_keys if k != "extra"}

    for p in clean_players:
        p["squad_id"] = squad_id
        cols = [k for k in valid_cols if k in p]
        placeholders = ", ".join(["?" for _ in cols])
        values = [p.get(k) for k in cols]
        sql = f"INSERT OR IGNORE INTO player ({', '.join(cols)}) VALUES ({placeholders})"
        try:
            db.execute(sql, values)
        except Exception:
            continue  # 跳过有问题的行

    db.commit()
    db.close()

    sample = clean_players[:5]
    return ImportResult(
        success=True,
        squad_id=squad_id,
        player_count=len(clean_players),
        message=f"成功导入 {len(clean_players)} 名球员",
        sample_players=sample,
    )


@router.post("/csv", response_model=ImportResult)
async def import_csv(file: UploadFile = File(...)):
    """上传并导入 FMRTE CSV 文件"""
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(400, "请上传 CSV 文件")

    content = await file.read()
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = content.decode("gbk")

    try:
        players = FMRTEParser.parse_csv(text)
    except Exception as e:
        raise HTTPException(400, f"CSV 解析失败: {str(e)}")

    if not players:
        raise HTTPException(400, "未解析到任何球员数据，请确认文件来自 FMRTE 导出")

    return _save_to_db(players, f"CSV导入_{file.filename}")


class ClipboardData(BaseModel):
    text: str


@router.post("/clipboard", response_model=ImportResult)
async def import_clipboard(data: ClipboardData):
    """从剪贴板文字导入"""
    text = data.text

    if not text.strip():
        raise HTTPException(400, "剪贴板内容为空")

    if not is_fmrte_data(text):
        raise HTTPException(
            400,
            "未检测到 FMRTE 数据格式。\n\n"
            "请确保：\n"
            "1. 在 FMRTE 中打开了球队球员列表\n"
            "2. Ctrl+A 全选球员\n"
            "3. Ctrl+C 复制\n"
            "4. 回到这里粘贴",
        )

    try:
        players = parse_fmrte_clipboard(text)
    except Exception as e:
        raise HTTPException(400, f"解析失败: {str(e)}")

    return _save_to_db(players, f"FMRTE导入_{len(players)}人")


@router.post("/fm24-html", response_model=ImportResult)
async def import_fm24_html(file: UploadFile = File(...)):
    """上传 FM24 导出的 HTML 文件（游戏内 Ctrl+P → Web Page）"""
    content = await file.read()
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        text = content.decode("gbk", errors="replace")

    try:
        players = parse_fm24_html(text)
    except Exception as e:
        raise HTTPException(400, f"HTML 解析失败: {str(e)}")

    if not players:
        raise HTTPException(
            400,
            "未在 HTML 文件中找到球员数据。\n\n"
            "请确认：\n"
            "1. 在 FM24 的 Squad 页面\n"
            "2. 自定义视图包含所有属性列\n"
            "3. Ctrl+A 全选所有球员\n"
            "4. Ctrl+P → Web Page → 保存\n"
            "5. 上传保存的 .html 文件",
        )

    return _save_to_db(players, f"FM24导出_{players[0].get('club', '')}_{len(players)}人")


class HTMLClipboardData(BaseModel):
    text: str


@router.post("/fm24-clipboard", response_model=ImportResult)
async def import_fm24_clipboard(data: HTMLClipboardData):
    """从 FM24 HTML 剪贴板导入（在浏览器中打开导出的 HTML，全选复制，粘贴到这里）"""
    text = data.text

    if not text.strip():
        raise HTTPException(400, "内容为空")

    # 尝试 FM24 HTML 解析
    players = parse_fm24_html(text)

    # 如果没解析到，尝试当 FMRTE 数据处理
    if not players:
        players = parse_fmrte_clipboard(text)

    if not players:
        raise HTTPException(
            400,
            "无法解析数据。\n\n"
            "FM24 用户：在游戏里 Squad 页 Ctrl+A → Ctrl+P → Web Page → 打开文件 → Ctrl+A → Ctrl+C → 粘贴\n"
            "FMRTE 用户：在 FMRTE 里 Ctrl+A → Ctrl+C → 粘贴",
        )

    return _save_to_db(players, f"导入_{len(players)}人")


@router.get("/squads")
async def list_squads():
    """列出所有已导入的阵容"""
    db = get_db()
    rows = db.execute(
        "SELECT s.id, s.name, s.club_name, s.import_date, "
        "(SELECT COUNT(*) FROM player WHERE squad_id = s.id) as player_count "
        "FROM squad s ORDER BY s.import_date DESC"
    ).fetchall()
    db.close()
    return [dict(r) for r in rows]


@router.get("/sample")
async def get_sample_data():
    """获取示例数据（用于快速体验，无需 FMRTE）"""
    sample_csv = _generate_sample_csv()
    players = FMRTEParser.parse_csv(sample_csv)
    if players:
        return _save_to_db(players, "示例阵容 (Barcelona)")
    raise HTTPException(500, "示例数据生成失败")


def _generate_sample_csv() -> str:
    """生成一份示例巴萨阵容 CSV"""
    header = "Name,Age,Nation,Club,Position,CA,PA,Pace,Acc,Stamina,Strength,Finishing,Dribbling,Passing,Tackling,Heading,Technique,First Touch,Vision,Decisions,Composure,Anticipation,Work Rate,Off Ball,Positioning,Crossing,Marking,Long Shots,Jumping,Agility,Balance,Reflexes,Handling,One On Ones,Aerial Reach,Command,Kicking,Preferred Foot,Personality"
    rows = [
        "Marc-André ter Stegen,31,Germany,Barcelona,GK,166,172,12,13,14,13,7,8,16,2,7,9,10,14,15,16,15,14,3,2,1,1,14,17,16,16,15,16,Right,Professional",
        "Jules Koundé,25,France,Barcelona,DC/DR,158,168,15,14,14,13,6,11,13,15,12,12,12,11,14,13,14,14,10,13,8,14,13,6,13,14,Right,Resolute",
        "Ronald Araújo,25,Uruguay,Barcelona,DC,160,168,16,15,15,17,5,6,11,17,15,9,10,8,14,14,16,16,6,15,6,13,18,12,14,Right,Born Leader",
        "Andreas Christensen,28,Denmark,Barcelona,DC,155,160,12,13,14,14,5,7,14,16,14,12,14,12,15,14,15,13,7,15,5,13,12,7,12,Right,Professional",
        "Alejandro Balde,20,Spain,Barcelona,DL/WBL/ML,152,170,18,18,16,11,5,14,12,12,6,13,12,11,13,12,14,13,13,12,11,13,4,12,14,Left,Fairly Professional",
        "João Cancelo,30,Portugal,Barcelona,DR,158,162,15,16,15,11,10,16,17,13,8,17,16,15,14,13,14,11,14,11,14,11,7,14,14,Right,Spirited",
        "Frenkie de Jong,27,Netherlands,Barcelona,MC/DM,162,170,14,14,16,12,8,14,18,12,7,16,17,16,15,14,15,12,12,6,10,14,14,8,15,14,Right,Model Citizen",
        "Pedri,21,Spain,Barcelona,MC/AMC,164,178,13,14,15,8,10,16,18,9,5,18,18,18,17,15,16,16,13,10,5,12,8,6,16,15,Right,Model Citizen",
        "Gavi,19,Spain,Barcelona,MC/AMC,156,176,14,15,17,10,9,14,15,14,6,15,14,14,15,14,17,15,12,10,7,13,10,7,15,14,Right,Driven",
        "İlkay Gündoğan,33,Germany,Barcelona,MC/AMC,158,158,11,12,13,10,13,12,17,10,9,16,16,17,15,14,14,11,10,7,12,15,7,6,13,Right,Leader",
        "Lamine Yamal,17,Spain,Barcelona,AMR/ST,146,182,16,17,13,8,12,17,14,6,8,15,14,13,13,12,14,11,14,4,15,4,13,4,17,16,Left,Ambitious",
        "Raphinha,27,Brazil,Barcelona,AMR/AML,158,162,17,16,15,11,13,16,15,10,9,15,14,14,14,13,14,13,13,6,14,7,16,10,14,15,Left,Resolute",
        "Ferran Torres,24,Spain,Barcelona,AML/ST/AMR,152,158,15,16,14,9,14,14,13,7,10,14,13,13,13,14,13,14,13,6,14,7,11,8,15,14,Right,Fairly Professional",
        "Robert Lewandowski,35,Poland,Barcelona,ST,168,168,12,11,14,14,18,12,12,4,16,14,14,12,14,15,16,16,15,14,4,4,7,17,14,14,Right,Perfectionist",
        "Vitor Roque,19,Brazil,Barcelona,ST,140,166,15,16,13,11,14,13,10,5,12,12,11,10,12,12,14,11,14,3,3,5,10,14,14,Right,Fairly Ambitious",
    ]
    return "\n".join([header] + rows)

