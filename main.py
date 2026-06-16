"""AgentBase Custom Agent entrypoint cho Mạnh — PM Agent.

Bọc PMAgent.reply() trong GreenNodeAgentBaseApp:
  - POST /invocations  -> handler(payload, context)
  - GET  /health       -> health_check()

Lịch sử hội thoại:
  - Khi có MEMORY_ID  -> lưu/đọc qua AgentBase Memory (bền vững qua restart/scale).
  - Khi chưa có       -> fallback in-memory theo session_id (đủ cho local/demo).

Trên AgentBase Runtime, IAM creds + agent identity được nền tảng tự inject
(GREENNODE_CLIENT_ID/SECRET/AGENT_IDENTITY) nên SDK Memory chạy không cần cấu hình thêm.
"""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from greennode_agentbase import GreenNodeAgentBaseApp, PingStatus, RequestContext

# Cho phép `from src.agent import ...` khi chạy `python main.py` từ thư mục gốc.
sys.path.append(str(Path(__file__).resolve().parent))
from src.agent import GREETING, PMAgent, is_greeting_trigger  # noqa: E402

load_dotenv()

app = GreenNodeAgentBaseApp()

MEMORY_ID = os.environ.get("MEMORY_ID")
_agent: PMAgent | None = None
# Fallback khi chưa cấu hình Memory: lịch sử in-memory theo session (giữ 10 lượt gần nhất).
_local_history: dict[str, list[dict]] = {}


def get_agent() -> PMAgent:
    """Khởi tạo PMAgent lazy (chỉ dựng khi có request đầu, cần creds LLM/Notion)."""
    global _agent
    if _agent is None:
        _agent = PMAgent()
    return _agent


# ---------- Lịch sử hội thoại (Memory hoặc in-memory) ----------
def _memory_client():
    from greennode_agentbase.memory import MemoryClient

    return MemoryClient()


def _load_history(user_id: str, session_id: str) -> list[dict]:
    if not MEMORY_ID:
        return _local_history.get(session_id, [])
    try:
        client = _memory_client()
        result = asyncio.run(
            client.list_events_async(id=MEMORY_ID, actorId=user_id, sessionId=session_id, page=1, size=20)
        )
        # API trả mới -> cũ; đảo lại thành thứ tự thời gian cho model đọc.
        events = list(reversed(list(result.list_data or [])))
        out = []
        for e in events:
            p = getattr(e, "payload", None)
            if p and p.role and p.message:
                out.append({"role": p.role, "content": p.message})
        return out
    except Exception as e:  # noqa: BLE001 — Memory best-effort: lỗi thì degrade, KHÔNG làm sập bot.
        print(f"[memory] đọc lịch sử lỗi, dùng fallback in-memory: {e}")
        return _local_history.get(session_id, [])


def _save_turn(user_id: str, session_id: str, user_msg: str, assistant_msg: str) -> None:
    def _save_local() -> None:
        hist = _local_history.setdefault(session_id, [])
        hist += [{"role": "user", "content": user_msg}, {"role": "assistant", "content": assistant_msg}]
        _local_history[session_id] = hist[-20:]

    if not MEMORY_ID:
        _save_local()
        return

    try:
        from greennode_agentbase.memory.models import EventCreateRequest, EventPayload

        client = _memory_client()

        def _ev(role: str, msg: str):
            return EventCreateRequest(payload=EventPayload(type="conversational", role=role, message=msg))

        async def _persist() -> None:
            await client.create_event_async(
                id=MEMORY_ID, actorId=user_id, sessionId=session_id, request=_ev("user", user_msg)
            )
            await client.create_event_async(
                id=MEMORY_ID, actorId=user_id, sessionId=session_id, request=_ev("assistant", assistant_msg)
            )

        asyncio.run(_persist())
    except Exception as e:  # noqa: BLE001 — Memory best-effort: lỗi thì lưu tạm in-memory.
        print(f"[memory] lưu lịch sử lỗi, dùng fallback in-memory: {e}")
        _save_local()


# ---------- Entrypoint ----------
@app.entrypoint
def handler(payload: dict, context: RequestContext) -> dict:
    """Xử lý 1 lượt chat.

    payload:
      - message (str): nội dung tin nhắn người dùng.
      - event (str, optional): "greeting" để buộc agent tự khai báo là AI.
    context: cung cấp user_id (-> actorId) và session_id (-> thread hội thoại).
    """
    message = (payload.get("message") or "").strip()
    user_id = context.user_id
    session_id = context.session_id

    # Khi dùng Memory, header định danh là bắt buộc — không fallback default để tránh trộn dữ liệu.
    if MEMORY_ID and (not user_id or not session_id):
        return {
            "status": "error",
            "error": "Thiếu header X-GreenNode-AgentBase-User-Id / X-GreenNode-AgentBase-Session-Id "
            "(bắt buộc khi bật Memory).",
        }
    user_id = user_id or "anonymous"
    session_id = session_id or "default"

    # Tự khai báo là AI (rulebook 11.1): khi được chào hoặc nhận event greeting.
    if payload.get("event") == "greeting" or is_greeting_trigger(message):
        return {"status": "success", "message": GREETING, "session_id": session_id}

    if not message:
        return {"status": "error", "error": "payload.message rỗng."}

    history = _load_history(user_id, session_id)
    agent = get_agent()
    answer = agent.reply(message, history)
    _save_turn(user_id, session_id, message, answer)
    resp = {"status": "success", "message": answer, "session_id": session_id}
    files = getattr(agent, "last_files", []) or []
    if files:
        resp["files"] = files  # [{filename, content}] — bridge gửi qua sendDocument
    return resp


@app.ping
def health_check() -> PingStatus:
    return PingStatus.HEALTHY


if __name__ == "__main__":
    app.run(port=8080, host="0.0.0.0")
