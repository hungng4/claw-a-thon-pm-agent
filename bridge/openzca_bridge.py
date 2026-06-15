"""Shim nối openzca (Zalo tài khoản cá nhân) ↔ agent "Mạnh" trên AgentBase.

Luồng:
    [Nhóm Zalo] → openzca listen --webhook → POST /hook (server này)
        → gọi AGENT_ENDPOINT_URL/invocations (kèm header user/session cho Memory)
        → lấy câu trả lời → `openzca msg send <threadId> ...` gửi lại Zalo.

Chạy TRÊN MÁY BẠN (không phải AgentBase), cạnh openzca CLI. Xem README ở cuối file.

Quy ước hành xử (chốt với Nate):
    - Nhóm: CHỈ trả lời khi tin bắt đầu bằng prefix (BOT_PREFIXES) hoặc bot được @mention.
    - Chat 1-1 (DM): trả lời mọi tin.
    - openzca mặc định bỏ qua tin của chính tài khoản đăng nhập → không lo lặp.

Cấu hình qua biến môi trường:
    AGENT_ENDPOINT_URL  (bắt buộc)  URL endpoint agent, vd https://endpoint-xxx.aiplatform.vngcloud.vn
    BRIDGE_PORT         (mặc 3000)  cổng server nhận webhook
    OPENZCA_BIN         (mặc openzca)  đường dẫn CLI openzca
    BOT_PREFIXES        (mặc "mạnh,/manh,manh")  prefix kích hoạt trong nhóm (phân tách bằng dấu phẩy)
    BOT_USER_ID         (tuỳ chọn)  id Zalo của tài khoản bot, để nhận diện @mention trong nhóm
    AGENT_TIMEOUT       (mặc 60)    timeout (giây) khi gọi agent
"""
from __future__ import annotations

import os
import subprocess

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, request

load_dotenv()  # tự nạp biến từ .env ở thư mục gốc

AGENT_ENDPOINT_URL = os.environ.get("AGENT_ENDPOINT_URL", "").rstrip("/")
BRIDGE_PORT = int(os.environ.get("BRIDGE_PORT", "3000"))
OPENZCA_BIN = os.environ.get("OPENZCA_BIN", "openzca")
BOT_PREFIXES = [p.strip().lower() for p in os.environ.get("BOT_PREFIXES", "mạnh,/manh,manh").split(",") if p.strip()]
BOT_USER_ID = os.environ.get("BOT_USER_ID", "").strip()
AGENT_TIMEOUT = int(os.environ.get("AGENT_TIMEOUT", "60"))

app = Flask(__name__)


# ---------- hàm thuần (test offline được) ----------
def is_group(payload: dict) -> bool:
    """Đoán tin thuộc nhóm hay DM. openzca/zca-js: chatType Group thường là 1 hoặc 'group'."""
    ct = payload.get("chatType", payload.get("chat_type"))
    return str(ct).strip().lower() in ("group", "1", "grouptype", "groupchat")


def extract(payload: dict) -> dict:
    """Rút các trường cần từ payload openzca (best-effort, có fallback)."""
    return {
        "content": (payload.get("content") or payload.get("text") or "").strip(),
        "thread_id": str(payload.get("threadId") or payload.get("thread_id") or payload.get("conversationId") or ""),
        "sender_id": str(payload.get("senderId") or payload.get("sender_id") or payload.get("uidFrom") or ""),
        "is_group": is_group(payload),
        "mention_ids": [str(m) for m in (payload.get("mentionIds") or payload.get("mentions") or [])],
    }


def should_respond(content: str, group: bool, mention_ids: list[str]) -> tuple[bool, str]:
    """Quyết định có trả lời không + trả về nội dung đã bỏ prefix.

    DM: luôn trả lời, giữ nguyên content.
    Nhóm: chỉ khi content bắt đầu bằng prefix (bỏ prefix) HOẶC bot được @mention (giữ content).
    """
    if not content:
        return False, content
    if not group:
        return True, content

    low = content.lower()
    for p in BOT_PREFIXES:
        if low.startswith(p):
            cleaned = content[len(p):].lstrip(" :,-").strip()
            return True, (cleaned or content)
    if BOT_USER_ID and BOT_USER_ID in mention_ids:
        return True, content
    return False, content


# ---------- I/O (gọi agent + gửi Zalo) ----------
def ask_agent(message: str, user_id: str, session_id: str) -> str:
    """Gọi endpoint agent, trả về câu trả lời text."""
    if not AGENT_ENDPOINT_URL:
        raise RuntimeError("Chưa set AGENT_ENDPOINT_URL")
    resp = requests.post(
        f"{AGENT_ENDPOINT_URL}/invocations",
        headers={
            "Content-Type": "application/json",
            # Bắt buộc cho Memory: user_id -> actor, session_id -> thread hội thoại.
            "X-GreenNode-AgentBase-User-Id": user_id or "zalo-unknown",
            "X-GreenNode-AgentBase-Session-Id": session_id or "zalo-default",
        },
        json={"message": message},
        timeout=AGENT_TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("status") == "error":
        return f"⚠️ {data.get('error', 'agent lỗi')}"
    return data.get("message", "")


def send_reply(thread_id: str, text: str, group: bool) -> None:
    """Gửi tin về Zalo qua openzca CLI."""
    if not text:
        return
    argv = [OPENZCA_BIN, "msg", "send", thread_id, text]
    if group:
        argv.append("--group")
    subprocess.run(argv, check=True, timeout=30)


# ---------- HTTP ----------
@app.get("/health")
def health():
    return jsonify({"status": "ok", "bridge": "openzca<->manh", "agent": bool(AGENT_ENDPOINT_URL)})


@app.post("/hook")
def hook():
    payload = request.get_json(silent=True) or {}
    msg = extract(payload)

    respond, content = should_respond(msg["content"], msg["is_group"], msg["mention_ids"])
    if not respond or not msg["thread_id"]:
        return jsonify({"ok": True, "skipped": True})

    try:
        answer = ask_agent(content, user_id=msg["sender_id"], session_id=msg["thread_id"])
        send_reply(msg["thread_id"], answer, msg["is_group"])
    except Exception as e:  # noqa: BLE001 — log & nuốt lỗi để openzca không retry dồn
        print(f"[bridge] lỗi xử lý tin từ {msg['thread_id']}: {e}")
    # Luôn trả 200 để openzca coi như đã nhận.
    return jsonify({"ok": True})


if __name__ == "__main__":
    if not AGENT_ENDPOINT_URL:
        print("⚠️  CHƯA set AGENT_ENDPOINT_URL — server vẫn chạy nhưng /hook sẽ báo lỗi khi gọi agent.")
    print(f"[bridge] listening on :{BRIDGE_PORT}/hook  -> agent: {AGENT_ENDPOINT_URL or '(chưa set)'}")
    app.run(host="0.0.0.0", port=BRIDGE_PORT)
