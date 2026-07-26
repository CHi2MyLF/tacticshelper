"""动态上下文构建器 — 为每轮对话构建精简但信息充分的上下文"""

import json
from typing import Optional
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class ContextBuilder:
    """对话上下文构建器"""

    def __init__(self):
        with open(DATA_DIR / "attributes.json", "r", encoding="utf-8") as f:
            self.attributes = json.load(f)
        with open(DATA_DIR / "styles.json", "r", encoding="utf-8") as f:
            self.styles_data = json.load(f)

    def build_squad_snapshot(self, players: list[dict], max_players: int = 30) -> str:
        """构建阵容快照文本（注入到系统消息中）"""
        if not players:
            return "尚未导入球员数据。请先导入 FMRTE 导出的 CSV 文件。"

        # Top 球员简要卡
        sorted_players = sorted(players, key=lambda p: p.get("current_ability", 0) or 0, reverse=True)[:max_players]

        lines = [f"## 当前阵容（共 {len(players)} 人，显示 Top {len(sorted_players)}）\n"]
        lines.append("| # | 球员 | 年龄 | 位置 | CA | PA | Pace | Acc | Fin | Pas | Tac | Wor | Sta |")
        lines.append("|---|------|------|------|----|----|------|-----|-----|-----|-----|-----|-----|")

        for i, p in enumerate(sorted_players, 1):
            name = p.get("name", "?")
            age = p.get("age", "?")
            pos = p.get("position", "?")
            ca = p.get("current_ability", "?")
            pa = p.get("potential_ability", "?")
            pace = p.get("pace", "?")
            acc = p.get("acceleration", "?")
            fin = p.get("finishing", "?")
            pas = p.get("passing", "?")
            tac = p.get("tackling", "?")
            wor = p.get("work_rate", "?")
            sta = p.get("stamina", "?")

            lines.append(f"| {i} | {name} | {age} | {pos} | {ca} | {pa} | {pace} | {acc} | {fin} | {pas} | {tac} | {wor} | {sta} |")

        return "\n".join(lines)

    def build_style_reference(self) -> str:
        """构建战术风格参考信息"""
        lines = ["## 可选战术风格\n"]
        styles = self.styles_data.get("styles", self.styles_data)
        for key, style in styles.items():
            if not isinstance(style, dict):
                continue
            lines.append(f"- **{key}** ({style.get('label_zh', key)}): {style.get('description_zh', '')}")
        return "\n".join(lines)

    def build_user_context(self, preferences: dict = None) -> str:
        """构建用户偏好上下文"""
        if not preferences:
            return ""
        lines = ["## 用户已设置的偏好"]
        for key, value in preferences.items():
            lines.append(f"- {key}: {value}")
        return "\n".join(lines)

    def build_chat_messages(
        self,
        system_prompt: str,
        squad_snapshot: str,
        chat_history: list[dict],
        style_reference: str,
        user_preferences: dict = None,
    ) -> list[dict]:
        """构建完整的 Claude API 消息列表"""
        system_text = system_prompt

        # 添加阵容数据
        system_text += f"\n\n{squad_snapshot}"

        # 添加风格参考
        system_text += f"\n\n{style_reference}"

        # 添加用户偏好
        if user_preferences:
            prefs_text = self.build_user_context(user_preferences)
            if prefs_text:
                system_text += f"\n\n{prefs_text}"

        messages = [{"role": "system", "content": system_text}]

        # 添加历史对话（最近 20 轮）
        for msg in chat_history[-20:]:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "tool":
                # 工具结果
                messages.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": msg.get("tool_use_id", ""),
                        "content": content,
                    }],
                })
            elif role == "assistant" and msg.get("tool_calls"):
                # 带有 tool_calls 的 assistant 消息
                tool_calls = json.loads(msg["tool_calls"])
                content_parts = []
                if content:
                    content_parts.append({"type": "text", "text": content})
                for tc in tool_calls:
                    content_parts.append({
                        "type": "tool_use",
                        "id": tc["id"],
                        "name": tc["name"],
                        "input": tc["input"],
                    })
                messages.append({"role": "assistant", "content": content_parts})
            else:
                messages.append({"role": role, "content": content})

        return messages
