"""PM Agent core — vòng lặp hội thoại + tool-calling.

Nạp system prompt + skill playbooks, gọi model (MaaS Gemma/Qwen qua API tương thích
OpenAI), và thực thi tool Notion khi model yêu cầu.

Đây là skeleton chạy được để demo end-to-end cho Claw-a-thon. Trên AgentBase, phần
model/tool có thể được nền tảng quản lý; file này minh hoạ logic và dùng cho local test.
"""
from __future__ import annotations

import json
import os
from datetime import date, datetime
from pathlib import Path

import yaml

import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))
from integrations.notion.notion_client import (  # noqa: E402
    NotionClient,
    active_sprint_filter,
    blocked_tasks_filter,
    overdue_tasks_filter,
)

ROOT = Path(__file__).resolve().parents[1]

# Lời chào / tự khai báo là AI (rulebook Claw-a-thon 11.1). Nguồn sự thật duy nhất,
# dùng chung cho cả AgentBase entrypoint (main.py) lẫn các bridge (Telegram/openzca) — đừng để trôi lệch.
GREETING = (
    "Chào cả nhà 👋 Mình là Mạnh 🤖 — trợ lý AI hỗ trợ PM cho tổ sản xuất game, "
    "không phải người thật nha. Cứ hỏi mình về sprint, task, milestone, blocker hay báo cáo nhé!"
)

_GREETING_TRIGGERS = ("/start", "hi", "chào mạnh")


def is_greeting_trigger(text: str) -> bool:
    """True nếu tin nhắn là lệnh chào -> agent nên tự khai báo là AI."""
    return (text or "").strip().lower() in _GREETING_TRIGGERS


# ---------- nạp cấu hình & prompt ----------
def load_config() -> dict:
    with open(ROOT / "agent" / "config.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_system_prompt(cfg: dict) -> str:
    parts = [(ROOT / cfg["system_prompt_file"]).read_text(encoding="utf-8")]
    for skill in cfg.get("skills", []):
        parts.append("\n\n---\n\n" + (ROOT / skill).read_text(encoding="utf-8"))
    return "".join(parts)


# ---------- định nghĩa tool cho model ----------
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "notion_query",
            "description": "Truy vấn 1 database Notion (tasks/sprints/milestones/risks). "
            "filter_preset có thể là: active_sprint, overdue_tasks, blocked_tasks, none.",
            "parameters": {
                "type": "object",
                "properties": {
                    "database": {"type": "string", "enum": ["tasks", "sprints", "milestones", "risks"]},
                    "filter_preset": {"type": "string", "default": "none"},
                },
                "required": ["database"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "notion_create",
            "description": "Tạo bản ghi mới trong database Notion. properties là dict đơn giản.",
            "parameters": {
                "type": "object",
                "properties": {
                    "database": {"type": "string", "enum": ["tasks", "sprints", "milestones", "risks"]},
                    "properties": {"type": "object"},
                },
                "required": ["database", "properties"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "notion_update",
            "description": "Cập nhật 1 page Notion theo page_id.",
            "parameters": {
                "type": "object",
                "properties": {
                    "page_id": {"type": "string"},
                    "properties": {"type": "object"},
                },
                "required": ["page_id", "properties"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "clock_now",
            "description": "Lấy ngày giờ hiện tại (ISO).",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]

_FILTERS = {
    "active_sprint": active_sprint_filter,
    "overdue_tasks": overdue_tasks_filter,
    "blocked_tasks": blocked_tasks_filter,
}


class PMAgent:
    def __init__(self, client=None, notion=None):
        """client / notion có thể được inject để test offline.
        Mặc định khởi tạo OpenAI client (lazy import) + NotionClient thật."""
        self.cfg = load_config()
        self.system_prompt = build_system_prompt(self.cfg)
        self.notion = notion or NotionClient()
        m = self.cfg["model"]
        if client is not None:
            self.client = client
        else:
            from openai import OpenAI  # lazy import: chỉ cần khi chạy thật
            # Ưu tiên chuẩn env của AgentBase (LLM_*) — xem /agentbase-llm; fallback về
            # tên env khai trong config.yaml (MAAS_*) rồi tới default, để không phá local/test.
            base_url = os.environ.get("LLM_BASE_URL") or os.environ.get(
                m["base_url_env"], "https://maas.greennode.ai/v1"
            )
            api_key = os.environ.get("LLM_API_KEY") or os.environ.get(m["api_key_env"], "sk-noop")
            self.client = OpenAI(base_url=base_url, api_key=api_key)
        self.model_name = os.environ.get("LLM_MODEL") or m["name"]
        self.temperature = m.get("temperature", 0.3)

    # ---- thực thi tool ----
    def _run_tool(self, name: str, args: dict) -> str:
        try:
            if name == "notion_query":
                preset = args.get("filter_preset", "none")
                flt = _FILTERS[preset]() if preset in _FILTERS else None
                rows = self.notion.query(args["database"], filter=flt)
                return json.dumps(rows, ensure_ascii=False)
            if name == "notion_create":
                res = self.notion.create(args["database"], args["properties"])
                return json.dumps({"ok": True, "id": res.get("id")}, ensure_ascii=False)
            if name == "notion_update":
                res = self.notion.update(args["page_id"], args["properties"])
                return json.dumps({"ok": True, "id": res.get("id")}, ensure_ascii=False)
            if name == "clock_now":
                return json.dumps({"now": datetime.now().isoformat(), "today": date.today().isoformat()})
            return json.dumps({"error": f"unknown tool {name}"})
        except Exception as e:  # noqa: BLE001
            return json.dumps({"error": str(e)}, ensure_ascii=False)

    # ---- vòng lặp hội thoại ----
    def reply(self, user_message: str, history: list[dict] | None = None) -> str:
        messages = [{"role": "system", "content": self.system_prompt}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": user_message})

        for _ in range(6):  # tối đa 6 vòng tool-call
            resp = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                tools=TOOLS,
                temperature=self.temperature,
            )
            msg = resp.choices[0].message
            if not msg.tool_calls:
                return msg.content or ""
            messages.append(msg.model_dump())
            for tc in msg.tool_calls:
                args = json.loads(tc.function.arguments or "{}")
                result = self._run_tool(tc.function.name, args)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result,
                })
        return "Mình xử lý hơi lâu, bạn thử hỏi lại cụ thể hơn nha 🙏"


if __name__ == "__main__":
    # REPL test nhanh local
    agent = PMAgent()
    print("Mạnh 🤖 (gõ 'quit' để thoát)")
    hist: list[dict] = []
    while True:
        q = input("> ").strip()
        if q.lower() in ("quit", "exit"):
            break
        a = agent.reply(q, hist)
        print(a)
        hist += [{"role": "user", "content": q}, {"role": "assistant", "content": a}]
