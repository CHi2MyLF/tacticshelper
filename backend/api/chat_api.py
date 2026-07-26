"""对话 API — SSE 流式返回 (RAG增强)"""

import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional

from ..agent.advisor import AdvisorAgent
from ..agent.tool_registry import ToolRegistry
from ..tools.player_scorer import PlayerScorer
from ..tools.squad_diagnosis import SquadDiagnosis
from ..tools.formation_selector import FormationSelector
from ..tools.role_assigner import RoleAssigner
from ..tools.instruction_generator import InstructionGenerator
from ..tools.depth_checker import DepthChecker
from ..tools.opponent_analyzer import OpponentAnalyzer
from ..rag.embedder import Embedder
from ..rag.store import VectorStore
from ..rag.retriever import KnowledgeRetriever
from ..rag.player_index import PlayerIndex
from ..rag.knowledge_loader import KnowledgeLoader
from ..database import get_db
from ..config import load_config, save_config

router = APIRouter(prefix="/api/chat", tags=["chat"])

# 全局 RAG 实例
_embedder: Optional[Embedder] = None
_vector_store: Optional[VectorStore] = None
_knowledge_retriever: Optional[KnowledgeRetriever] = None
_player_index: Optional[PlayerIndex] = None

# 全局 Agent 实例
_agent: Optional[AdvisorAgent] = None
_squad_cache: dict = {}  # {squad_id: [players]}
_tool_instances: dict = {}


def init_rag() -> None:
    """初始化 RAG 系统"""
    global _embedder, _vector_store, _knowledge_retriever, _player_index

    try:
        _embedder = Embedder()
        _vector_store = VectorStore("fm_knowledge")
        _knowledge_retriever = KnowledgeRetriever(_embedder, _vector_store)
        _player_index = PlayerIndex()

        # 异步加载知识库（在后台完成）
        import asyncio
        async def load():
            loader = KnowledgeLoader(_embedder, _vector_store)
            count = await loader.load_all()
            print(f"[RAG] 知识库加载完成: {count} 条记录")

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(load())
            else:
                loop.run_until_complete(load())
        except Exception:
            asyncio.run(load())

    except Exception as e:
        print(f"[RAG] 初始化失败 (非致命): {e}")


def get_agent() -> AdvisorAgent:
    global _agent, _knowledge_retriever, _player_index
    if _agent is None:
        config = load_config()
        _agent = AdvisorAgent(config)

        # 注入 RAG
        if _knowledge_retriever:
            _agent.set_knowledge_retriever(_knowledge_retriever)
        if _player_index:
            _agent.set_player_index(_player_index)

        _register_tools(_agent)
    return _agent


def _register_tools(agent: AdvisorAgent):
    """注册所有工具的执行函数"""
    registry = agent.tool_registry

    # 延迟初始化工具实例
    def get_scorer():
        if "scorer" not in _tool_instances:
            _tool_instances["scorer"] = PlayerScorer()
        return _tool_instances["scorer"]

    def get_diagnosis():
        if "diagnosis" not in _tool_instances:
            _tool_instances["diagnosis"] = SquadDiagnosis()
        return _tool_instances["diagnosis"]

    def get_formation_selector():
        if "formation_selector" not in _tool_instances:
            _tool_instances["formation_selector"] = FormationSelector()
        return _tool_instances["formation_selector"]

    def get_role_assigner():
        if "role_assigner" not in _tool_instances:
            _tool_instances["role_assigner"] = RoleAssigner()
        return _tool_instances["role_assigner"]

    def get_instruction_gen():
        if "instruction_gen" not in _tool_instances:
            _tool_instances["instruction_gen"] = InstructionGenerator()
        return _tool_instances["instruction_gen"]

    def get_depth_checker():
        if "depth_checker" not in _tool_instances:
            _tool_instances["depth_checker"] = DepthChecker()
        return _tool_instances["depth_checker"]

    def get_opponent_analyzer():
        if "opponent_analyzer" not in _tool_instances:
            _tool_instances["opponent_analyzer"] = OpponentAnalyzer()
        return _tool_instances["opponent_analyzer"]

    def get_players():
        """从缓存获取当前阵容"""
        for squad_id, players in _squad_cache.items():
            return players
        return []

    registry.register("diagnose_squad", lambda: get_diagnosis().diagnose(get_players()))

    registry.register("score_player_for_role", lambda player_name=None, role_key=None:
        get_scorer().score(
            _find_player(player_name),
            role_key or "CM_S",
            _guess_position_group(role_key or "CM_S"),
        ))

    registry.register("recommend_formation", lambda style="gegenpress", preferred_formation=None:
        get_formation_selector().recommend(get_players(), style, preferred_formation))

    registry.register("assign_roles", lambda formation="433", style="gegenpress":
        get_role_assigner().assign(get_players(), formation, style))

    registry.register("generate_instructions", lambda style="gegenpress", formation="433":
        get_instruction_gen().generate(style, formation, []))

    registry.register("check_squad_depth", lambda formation="433":
        get_depth_checker().check(get_players(), formation))

    registry.register("analyze_opponent", lambda opponent_name, formation="", style="", strengths="", weaknesses="", danger_players=None:
        get_opponent_analyzer().analyze({
            "name": opponent_name,
            "formation": formation,
            "style": style,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "danger_players": danger_players or [],
        }))

    registry.register("get_all_players", lambda: get_players())

    registry.register("save_tactic", lambda name, formation, mentality, style="", instructions_json="", player_roles_json="":
        _save_tactic(name, formation, mentality, style, instructions_json, player_roles_json))

    # ─── RAG 工具 ───
    registry.register("search_knowledge", lambda query, category=None:
        _search_knowledge_sync(query, category))

    registry.register("find_similar_players", lambda query, position_filter=None, top_k=5:
        _find_similar_sync(query, position_filter, top_k))

    # 重建球员索引
    players = get_players()
    if players and _player_index:
        _player_index.build(players)


def _find_player(name: str) -> dict:
    """根据名称查找球员"""
    for players in _squad_cache.values():
        for p in players:
            if name.lower() in (p.get("name", "") or "").lower():
                return p
        # 如果只缓存了一个阵容，模糊匹配
        for p in players:
            p_name = (p.get("name", "") or "").lower()
            if name.lower() in p_name or p_name in name.lower():
                return p
    return {}


def _guess_position_group(role_key: str) -> str:
    """根据角色 key 猜测位置组"""
    role_groups = {
        "SK": "GK", "G_": "GK",
        "BPD": "DC", "CD_": "DC", "NCB": "DC",
        "FB_": "DR_DL", "WB_": "DR_DL", "CWB": "DR_DL", "IWB": "DR_DL",
        "DM_": "DM", "DLP": "DM", "A_D": "DM", "HB_": "DM", "RGA": "DM", "VOL": "DM", "BWM": "DM",
        "CM_": "MC", "AP_": "MC", "BBM": "MC", "MEZ": "MC", "CAR": "MC",
        "AM_": "AMC", "T_A": "AMC", "EG_": "AMC", "SS_": "AMC",
        "W_A": "AMR_AML", "W_S": "AMR_AML", "IF_": "AMR_AML", "IW_": "AMR_AML", "RMD": "AMR_AML", "DW_": "AMR_AML",
        "AF_": "ST", "P_A": "ST", "DLF": "ST", "TF_": "ST", "CF_": "ST", "PF_": "ST", "F9_": "ST",
    }
    for prefix, group in role_groups.items():
        if role_key.startswith(prefix):
            return group
    return "MC"


def _save_tactic(name, formation, mentality, style, instructions_json, player_roles_json):
    """保存战术到数据库"""
    # 找到活跃的 squad_id
    squad_id = next(iter(_squad_cache.keys()), None)
    if not squad_id:
        return {"error": "没有活跃的阵容数据"}

    db = get_db()
    db.execute(
        "INSERT INTO tactic (squad_id, name, formation, mentality, instructions_json, player_roles_json) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (squad_id, name, formation, mentality, instructions_json, player_roles_json),
    )
    db.commit()
    db.close()
    return {"success": True, "message": f"战术 '{name}' 已保存"}


def _search_knowledge_sync(query: str, category: str = None) -> dict:
    """同步包装: 搜索 FM 知识库"""
    import asyncio
    async def _do():
        if not _knowledge_retriever:
            return {"error": "知识库未初始化"}
        results = await _knowledge_retriever.retrieve(query, top_k=5, category_filter=category)
        return {
            "query": query,
            "results_count": len(results),
            "results": [
                {
                    "title": r.get("metadata", {}).get("title", ""),
                    "category": r.get("metadata", {}).get("category", ""),
                    "score": r.get("score", 0),
                    "content": r.get("content", "")[:500],
                }
                for r in results
            ],
        }

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            return {"note": "知识库搜索已触发（异步）", "results": []}
        return loop.run_until_complete(_do())
    except Exception:
        return asyncio.run(_do())


def _find_similar_sync(query: str, position_filter: str = None, top_k: int = 5) -> dict:
    """同步包装: 语义球员搜索"""
    if not _player_index or _player_index.vectors is None:
        return {"error": "球员索引未构建，请先导入阵容数据"}

    players = get_players()
    if not players:
        return {"error": "没有球员数据"}

    # 重建索引（如果换了阵容）
    _player_index.build(players)

    # 先尝试按名称搜索
    results = _player_index.search(query, top_k=top_k, position_filter=position_filter)

    # 如果名称搜不到，按描述搜索
    if not results:
        results = _player_index.search_by_description(query, top_k=top_k)

    return {
        "query": query,
        "results_count": len(results),
        "results": results,
    }


class ChatRequest(BaseModel):
    message: str
    squad_id: Optional[int] = None
    chat_history: list[dict] = []
    preferences: Optional[dict] = None


class ConfigRequest(BaseModel):
    api_key: str
    api_base_url: str = "https://api.anthropic.com"
    model: str = "deepseek-chat"


@router.post("/stream")
async def chat_stream(request: ChatRequest):
    """流式对话"""
    agent = get_agent()
    if not agent.has_api_key():
        raise HTTPException(400, "请先设置 API Key")

    # 加载阵容数据到缓存
    players = []
    if request.squad_id:
        if request.squad_id not in _squad_cache:
            db = get_db()
            rows = db.execute(
                "SELECT * FROM player WHERE squad_id = ?", (request.squad_id,)
            ).fetchall()
            db.close()
            _squad_cache[request.squad_id] = [dict(r) for r in rows]

        players = _squad_cache.get(request.squad_id, [])
    elif _squad_cache:
        players = next(iter(_squad_cache.values()))

    async def generate():
        try:
            async for chunk in agent.chat(
                user_message=request.message,
                squad_players=players,
                chat_history=request.chat_history,
                user_preferences=request.preferences,
            ):
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/config")
async def set_config(request: ConfigRequest):
    """设置 API Key"""
    # 防止错误消息被写入配置
    if not request.api_key or len(request.api_key) < 5:
        raise HTTPException(400, "API Key 太短，请填入有效的 Key")
    if any(bad in request.api_key for bad in ["❌", "Error", "error", "string indices", "index"]):
        raise HTTPException(400, "无效的 API Key，请填入真实的 Key")

    config = load_config()
    config.api_key = request.api_key
    config.api_base_url = request.api_base_url
    config.model = request.model
    save_config(config)

    global _agent
    _agent = AdvisorAgent(config)
    _register_tools(_agent)

    return {"success": True, "message": "API Key 已保存"}


@router.get("/config/status")
async def config_status():
    """检查 API Key 是否已设置"""
    config = load_config()
    return {
        "has_api_key": bool(config.api_key),
        "api_base_url": config.api_base_url,
        "model": config.model,
    }
