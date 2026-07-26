"""Tool Registry — 注册 Claude Function Calling 工具定义"""

from typing import Any, Callable
from dataclasses import dataclass, field

# 所有可用工具的 JSON Schema 定义
TOOL_DEFINITIONS = [
    {
        "name": "diagnose_squad",
        "description": "获取完整的阵容诊断报告，包括：球队优劣势分析、隐藏问题（如缺少防守中场、定位球主罚者等）、各位置覆盖情况、阵容年龄平衡、最佳角色建议",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "score_player_for_role",
        "description": "评估指定球员在某个角色上的 DWRS 评分（0-100）。可以用来比较不同球员在同一角色上的表现，或同一球员在不同角色上的适配度",
        "input_schema": {
            "type": "object",
            "properties": {
                "player_name": {
                    "type": "string",
                    "description": "球员姓名（支持部分匹配）",
                },
                "role_key": {
                    "type": "string",
                    "description": "角色标识，如 IF_A, BBM_S, AF_A, DLP_S, WB_A 等",
                },
            },
            "required": ["player_name"],
        },
    },
    {
        "name": "recommend_formation",
        "description": "基于当前阵容和战术风格偏好，推荐最适合的阵型。考虑球员适配度、风格兼容性、阵型平衡性",
        "input_schema": {
            "type": "object",
            "properties": {
                "style": {
                    "type": "string",
                    "enum": ["gegenpress", "tiki_taka", "direct_counter", "wing_play", "possession_flexible", "vertical_tiki_taka", "fluid_counter", "park_the_bus"],
                    "description": "战术风格",
                },
                "preferred_formation": {
                    "type": "string",
                    "description": "用户偏好的阵型（可选），如 4231, 433, 442 等",
                },
            },
            "required": ["style"],
        },
    },
    {
        "name": "assign_roles",
        "description": "为指定阵型分配首发球员和角色/职责。包括首发阵容、替补席、轮换选项、阵容平衡检查",
        "input_schema": {
            "type": "object",
            "properties": {
                "formation": {
                    "type": "string",
                    "description": "阵型标识，如 4231, 433, 442, 352 等",
                },
                "style": {
                    "type": "string",
                    "enum": ["gegenpress", "tiki_taka", "direct_counter", "wing_play", "possession_flexible", "vertical_tiki_taka", "fluid_counter", "park_the_bus"],
                    "description": "战术风格",
                },
            },
            "required": ["formation", "style"],
        },
    },
    {
        "name": "generate_instructions",
        "description": "根据战术风格和阵型，生成完整的球队指令（持球/转换/无球阶段）和个人指令",
        "input_schema": {
            "type": "object",
            "properties": {
                "style": {
                    "type": "string",
                    "enum": ["gegenpress", "tiki_taka", "direct_counter", "wing_play", "possession_flexible", "vertical_tiki_taka", "fluid_counter", "park_the_bus"],
                    "description": "战术风格",
                },
                "formation": {
                    "type": "string",
                    "description": "阵型标识",
                },
            },
            "required": ["style", "formation"],
        },
    },
    {
        "name": "check_squad_depth",
        "description": "检查阵容深度，评估各位置的轮换储备。报告关键位置的深度不足问题，给出转会建议",
        "input_schema": {
            "type": "object",
            "properties": {
                "formation": {
                    "type": "string",
                    "description": "参考阵型（用来判断需要多少各位置球员），默认 433",
                },
            },
            "required": [],
        },
    },
    {
        "name": "analyze_opponent",
        "description": "分析对手特征并生成针对性战术调整方案。包括对手威胁分析、弱点识别、针对性盯人建议",
        "input_schema": {
            "type": "object",
            "properties": {
                "opponent_name": {
                    "type": "string",
                    "description": "对手名称",
                },
                "formation": {
                    "type": "string",
                    "description": "对手常用阵型，如 433, 4231, 442 等",
                },
                "style": {
                    "type": "string",
                    "description": "对手打法风格描述，如 '高压逼抢', '控球', '防守反击'",
                },
                "strengths": {
                    "type": "string",
                    "description": "对手优势（可选）",
                },
                "weaknesses": {
                    "type": "string",
                    "description": "对手弱点（可选）",
                },
                "danger_players": {
                    "type": "array",
                    "items": {"type": "object", "properties": {"name": {"type": "string"}, "position": {"type": "string"}, "is_star": {"type": "boolean"}}},
                    "description": "对手危险球员列表",
                },
            },
            "required": ["opponent_name"],
        },
    },
    {
        "name": "get_all_players",
        "description": "获取当前阵容中所有球员的完整数据列表，包括所有属性值",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "save_tactic",
        "description": "保存当前战术方案到数据库",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "战术名称"},
                "formation": {"type": "string", "description": "阵型"},
                "mentality": {"type": "string", "description": "心态"},
                "style": {"type": "string", "description": "战术风格"},
                "instructions_json": {"type": "string", "description": "指令 JSON"},
                "player_roles_json": {"type": "string", "description": "球员角色 JSON"},
            },
            "required": ["name", "formation", "mentality"],
        },
    },
    {
        "name": "search_knowledge",
        "description": "搜索 FM2024 知识库，获取战术指南、属性分析、训练建议、转会策略等专业知识。当用户询问通用 FM 知识时使用",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "搜索查询，如 '如何训练年轻前锋'、'最佳角球战术'"},
                "category": {
                    "type": "string",
                    "enum": ["meta", "tactics", "position_guide", "roles", "training", "transfers", "set_pieces", "match_day"],
                    "description": "知识分类过滤（可选）",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "find_similar_players",
        "description": "语义搜索相似球员。根据球员名称查找属性相似的球员，或根据文字描述搜索（如'速度快盘带好的右边锋'）",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "球员名称 或 描述文字（如'像哈维的中场'、'速度快盘带好的右边锋'）"},
                "position_filter": {"type": "string", "description": "位置过滤，如 AMR, DC, ST"},
                "top_k": {"type": "integer", "description": "返回结果数量，默认 5"},
            },
            "required": ["query"],
        },
    },
]


@dataclass
class ToolRegistry:
    """工具注册中心 — 管理工具定义和实际执行函数"""

    _handlers: dict[str, Callable] = field(default_factory=dict)

    def register(self, name: str, handler: Callable) -> None:
        self._handlers[name] = handler

    def get_definitions(self) -> list[dict]:
        return TOOL_DEFINITIONS

    def execute(self, name: str, args: dict) -> Any:
        handler = self._handlers.get(name)
        if not handler:
            return {"error": f"未知工具: {name}"}
        try:
            return handler(**args)
        except Exception as e:
            return {"error": f"工具执行失败: {str(e)}"}
