"""Advisor Agent — 支持 Anthropic / DeepSeek / OpenAI 兼容"""

import json
from typing import AsyncGenerator, Optional

from .system_prompt import get_system_prompt
from .context_builder import ContextBuilder
from .tool_registry import ToolRegistry
from ..config import AppConfig, load_config


class AdvisorAgent:
    """FM2024 战术顾问 Agent（多 Provider）"""

    def __init__(self, config: Optional[AppConfig] = None):
        self.config = config or load_config()
        self.context_builder = ContextBuilder()
        self.tool_registry = ToolRegistry()
        self._knowledge_retriever = None
        self._player_index = None
        self._anthropic = None
        self._openai = None
        self._init_client()

    def _init_client(self):
        """初始化 API 客户端（自动检测 Provider）"""
        if not self.config.api_key:
            return
        base = self.config.api_base_url or ""

        if "deepseek" in base or "openai" in base or "api.openai.com" in base:
            try:
                from openai import AsyncOpenAI
                self._openai = AsyncOpenAI(api_key=self.config.api_key, base_url=base)
                self._anthropic = None
            except ImportError:
                pass
        else:
            try:
                import anthropic
                self._anthropic = anthropic.AsyncAnthropic(
                    api_key=self.config.api_key, base_url=base
                )
                self._openai = None
            except ImportError:
                pass

    def set_knowledge_retriever(self, retriever):
        self._knowledge_retriever = retriever

    def set_player_index(self, player_index):
        self._player_index = player_index

    def set_api_key(self, api_key: str, base_url: str = "https://api.anthropic.com"):
        self.config.api_key = api_key
        self.config.api_base_url = base_url
        self._init_client()

    def register_handler(self, name: str, handler):
        self.tool_registry.register(name, handler)

    def has_api_key(self) -> bool:
        return bool(self.config.api_key)

    def _has_client(self) -> bool:
        return self._anthropic is not None or self._openai is not None

    async def chat(
        self,
        user_message: str,
        squad_players: list[dict],
        chat_history: list[dict] = None,
        user_preferences: dict = None,
    ) -> AsyncGenerator[dict, None]:
        if not self._has_client():
            yield {"type": "error", "message": "请先设置 API Key"}
            return

        chat_history = chat_history or []

        # ─── RAG ───
        rag_context = ""
        if self._knowledge_retriever and await self._knowledge_retriever.is_ready():
            try:
                rag_context = await self._knowledge_retriever.retrieve_context(user_message, top_k=4)
            except Exception:
                pass

        squad_snapshot = self.context_builder.build_squad_snapshot(squad_players)
        style_reference = self.context_builder.build_style_reference()

        system_prompt = get_system_prompt()
        if rag_context:
            system_prompt += f"\n\n{rag_context}\n\n---\n请优先参考上述知识库资料来回答用户的问题。"

        tools = self.tool_registry.get_definitions()

        if self._openai:
            async for chunk in self._chat_openai(system_prompt, user_message, squad_snapshot, style_reference, chat_history, tools):
                yield chunk
        elif self._anthropic:
            async for chunk in self._chat_anthropic(system_prompt, user_message, squad_snapshot, style_reference, chat_history, tools):
                yield chunk
        else:
            yield {"type": "error", "message": "未配置有效的 API 客户端"}

    # ─── OpenAI-compatible (DeepSeek) ───

    async def _chat_openai(self, system_prompt: str, user_message: str, squad_snapshot: str,
                           style_ref: str, history: list[dict], tools: list[dict]) -> AsyncGenerator[dict, None]:
        # 转换 tools 格式: Claude → OpenAI
        openai_tools = []
        for t in tools:
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t.get("description", ""),
                    "parameters": t.get("input_schema", {"type": "object", "properties": {}}),
                }
            })

        messages = [{"role": "system", "content": system_prompt}]
        # 注入阵容快照
        messages.append({"role": "system", "content": squad_snapshot})
        messages.append({"role": "system", "content": style_ref})
        # 历史
        for m in history[-20:]:
            role = m.get("role", "user")
            if role in ("user", "assistant"):
                messages.append({"role": role, "content": m.get("content", "")})
        # 当前消息
        messages.append({"role": "user", "content": user_message})

        model = self.config.model
        # 自动适配模型名
        if "deepseek" in (self.config.api_base_url or ""):
            model = model if "deepseek" in model else "deepseek-chat"
        elif not self._anthropic:
            model = model or "deepseek-chat"

        try:
            while True:
                resp = await self._openai.chat.completions.create(
                    model=model,
                    messages=messages,
                    tools=openai_tools if openai_tools else None,
                    tool_choice="auto" if openai_tools else None,
                    max_tokens=4096,
                    stream=True,
                )

                full_text = ""
                tool_calls_acc: dict[int, dict] = {}
                finish_reason = None

                async for chunk in resp:
                    if chunk.choices and chunk.choices[0].delta:
                        delta = chunk.choices[0].delta
                        finish_reason = chunk.choices[0].finish_reason

                        if delta.content:
                            full_text += delta.content
                            yield {"type": "text", "content": delta.content}

                        if delta.tool_calls:
                            for tc in delta.tool_calls:
                                idx = tc.index
                                if idx not in tool_calls_acc:
                                    tool_calls_acc[idx] = {
                                        "id": tc.id or "",
                                        "name": tc.function.name if tc.function else "",
                                        "arguments": "",
                                    }
                                if tc.id:
                                    tool_calls_acc[idx]["id"] = tc.id
                                if tc.function:
                                    if tc.function.name:
                                        tool_calls_acc[idx]["name"] = tc.function.name
                                    if tc.function.arguments:
                                        tool_calls_acc[idx]["arguments"] += tc.function.arguments

                # 处理 Tool calls
                if finish_reason == "tool_calls" and tool_calls_acc:
                    tool_uses = []
                    for idx in sorted(tool_calls_acc.keys()):
                        tc = tool_calls_acc[idx]
                        try:
                            args = json.loads(tc["arguments"]) if tc["arguments"] else {}
                        except json.JSONDecodeError:
                            args = {}
                        tool_uses.append({"id": tc["id"], "name": tc["name"], "input": args})
                        yield {"type": "tool_call", "id": tc["id"], "name": tc["name"], "input": args}

                    # 执行 tools
                    assistant_msg = {"role": "assistant", "content": full_text or None}
                    if tool_uses:
                        assistant_msg["tool_calls"] = [
                            {"id": tu["id"], "type": "function",
                             "function": {"name": tu["name"], "arguments": json.dumps(tu["input"], ensure_ascii=False)}}
                            for tu in tool_uses
                        ]
                    messages.append(assistant_msg)

                    for tu in tool_uses:
                        result = self.tool_registry.execute(tu["name"], tu["input"])
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tu["id"],
                            "content": json.dumps(result, ensure_ascii=False, indent=2),
                        })
                    continue  # loop back for Claude's response

                # No tool calls, done
                if full_text.strip():
                    history.append({"role": "assistant", "content": full_text})
                yield {"type": "done"}
                return

        except Exception as e:
            yield {"type": "error", "message": f"API 错误: {str(e)}"}

    # ─── Anthropic ───

    async def _chat_anthropic(self, system_prompt: str, user_message: str, squad_snapshot: str,
                              style_ref: str, history: list[dict], tools: list[dict]) -> AsyncGenerator[dict, None]:
        import anthropic as anth

        messages = self.context_builder.build_chat_messages(
            system_prompt=system_prompt,
            squad_snapshot=squad_snapshot,
            chat_history=history,
            style_reference=style_ref,
        )
        messages.append({"role": "user", "content": user_message})

        try:
            while True:
                response = await self._anthropic.messages.create(
                    model=self.config.model or "claude-sonnet-4-20250514",
                    max_tokens=4096,
                    system=messages[0]["content"] if messages[0]["role"] == "system" else "",
                    messages=[m for m in messages if m["role"] != "system"],
                    tools=tools,
                )

                text_content = ""
                tool_uses = []

                for block in response.content:
                    if block.type == "text":
                        text_content += block.text
                        yield {"type": "text", "content": block.text}
                    elif block.type == "tool_use":
                        tool_uses.append({"id": block.id, "name": block.name, "input": block.input})
                        yield {"type": "tool_call", "id": block.id, "name": block.name, "input": block.input}

                if not tool_uses:
                    if text_content:
                        history.append({"role": "assistant", "content": text_content})
                    yield {"type": "done"}
                    return

                assistant_content = []
                if text_content:
                    assistant_content.append({"type": "text", "text": text_content})
                for tu in tool_uses:
                    assistant_content.append({"type": "tool_use", "id": tu["id"], "name": tu["name"], "input": tu["input"]})

                tool_results = []
                for tu in tool_uses:
                    result = self.tool_registry.execute(tu["name"], tu["input"])
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tu["id"],
                        "content": json.dumps(result, ensure_ascii=False, indent=2),
                    })

                messages.append({"role": "assistant", "content": assistant_content})
                messages.append({"role": "user", "content": tool_results})

        except Exception as e:
            yield {"type": "error", "message": f"API 错误: {str(e)}"}
