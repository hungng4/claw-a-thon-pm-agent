"""Bridge nối Telegram ↔ agent "Mạnh" trên AgentBase (long-polling, không cần URL công khai).

Luồng:
    [Chat/Nhóm Telegram] → Telegram Bot API (getUpdates, long-poll)
        → bridge gọi AGENT_ENDPOINT_URL/invocations (kèm header user/session cho Memory)
        → lấy câu trả lời → sendMessage trả về Telegram.

Chạy trên máy bạn (hoặc bất kỳ đâu có internet ra). Xem README ở cuối repo / bridge/README_telegram.md.

Quy ước hành xử (giống bản Zalo, chốt với Nate):
    - Nhóm: CHỈ trả lời khi tin bắt đầu bằng prefix (BOT_PREFIXES), @mention bot,
      là /command, hoặc là reply vào tin của bot.
    - Chat 1-1 (private): trả lời mọi tin.

Cấu hình qua biến môi trường:
    TELEGRAM_BOT_TOKEN  (bắt buộc)  token từ @BotFather
    AGENT_ENDPOINT_URL  (bắt buộc)  URL endpoint agent trên AgentBase
    BOT_USERNAME        (tuỳ chọn)  username bot (không gồm @), để nhận diện @mention trong nhóm
    BOT_PREFIXES        (mặc "mạnh,/manh,manh")  prefix kích hoạt trong nhóm
    AGENT_TIMEOUT       (mặc 60)    timeout (giây) gọi agent
    POLL_TIMEOUT        (mặc 30)    long-poll timeout (giây) cho getUpdates
"""
from __future__ import annotations

import os
import time

import requests
from dotenv import load_dotenv

load_dotenv()  # tự nạp biến từ .env ở thư mục gốc (chạy bridge từ gốc repo)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
AGENT_ENDPOINT_URL = os.environ.get("AGENT_ENDPOINT_URL", "").rstrip("/")
BOT_USERNAME = os.environ.get("BOT_USERNAME", "").lstrip("@").strip().lower()
BOT_PREFIXES = [p.strip().lower() for p in os.environ.get("BOT_PREFIXES", "mạnh,/manh,manh").split(",") if p.strip()]
AGENT_TIMEOUT = int(os.environ.get("AGENT_TIMEOUT", "60"))
POLL_TIMEOUT = int(os.environ.get("POLL_TIMEOUT", "30"))

API = "https://api.telegram.org/bot{token}/{method}"


# ---------- hàm thuần (test offline được) ----------
def extract_message(update: dict) -> dict | None:
    """Rút thông tin tin nhắn text từ 1 Telegram update. Trả None nếu không phải tin text cần xử lý."""
    msg = update.get("message") or update.get("edited_message")
    if not msg:
        return None
    text = (msg.get("text") or msg.get("caption") or "").strip()
    if not text:
        return None
    chat = msg.get("chat") or {}
    frm = msg.get("from") or {}
    chat_type = chat.get("type", "")
    reply_to = msg.get("reply_to_message") or {}
    reply_from = (reply_to.get("from") or {})
    return {
        "text": text,
        "chat_id": str(chat.get("id", "")),
        "chat_type": chat_type,
        "is_group": chat_type in ("group", "supergroup"),
        "user_id": str(frm.get("id", "")),
        "message_id": msg.get("message_id"),
        "entities": msg.get("entities") or [],
        "reply_to_bot": bool(reply_from.get("is_bot")),
    }


def _mentions_bot(text: str, entities: list[dict]) -> bool:
    """True nếu tin có @mention trùng BOT_USERNAME (cần BOT_USERNAME được set)."""
    if not BOT_USERNAME:
        return False
    low = text.lower()
    for e in entities:
        if e.get("type") == "mention":
            off, length = e.get("offset", 0), e.get("length", 0)
            handle = low[off:off + length].lstrip("@")
            if handle == BOT_USERNAME:
                return True
    return False


def _is_command(entities: list[dict]) -> bool:
    return any(e.get("type") == "bot_command" and e.get("offset", 1) == 0 for e in entities)


def should_respond(msg: dict) -> tuple[bool, str]:
    """Quyết định có trả lời không + nội dung đã bỏ prefix.

    Private: luôn trả lời. Nhóm: chỉ khi prefix / @mention / /command / reply-vào-bot.
    """
    text = msg["text"]
    if not msg["is_group"]:
        return True, text

    low = text.lower()
    for p in BOT_PREFIXES:
        if low.startswith(p):
            return True, (text[len(p):].lstrip(" :,-").strip() or text)
    if _mentions_bot(text, msg["entities"]):
        # bỏ phần "@username" khỏi câu cho gọn
        return True, text.replace(f"@{BOT_USERNAME}", "", 1).strip() if BOT_USERNAME else text
    if _is_command(msg["entities"]) or msg["reply_to_bot"]:
        return True, text
    return False, text


# ---------- I/O ----------
def ask_agent(message: str, user_id: str, session_id: str) -> dict:
    """Gọi agent, trả {'text': str, 'files': [{filename, content}]}."""
    if not AGENT_ENDPOINT_URL:
        raise RuntimeError("Chưa set AGENT_ENDPOINT_URL")
    resp = requests.post(
        f"{AGENT_ENDPOINT_URL}/invocations",
        headers={
            "Content-Type": "application/json",
            "X-GreenNode-AgentBase-User-Id": user_id or "tg-unknown",
            "X-GreenNode-AgentBase-Session-Id": session_id or "tg-default",
        },
        json={"message": message},
        timeout=AGENT_TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("status") == "error":
        return {"text": f"⚠️ {data.get('error', 'agent lỗi')}", "files": []}
    return {"text": data.get("message", ""), "files": data.get("files") or []}


TG_LIMIT = 3900  # < 4096 của Telegram, chừa chỗ cho cặp ``` + ký tự escape


def _escape_code(text: str) -> str:
    """Trong code block (``` ```), MarkdownV2 chỉ cần escape '\\' và '`'."""
    return text.replace("\\", "\\\\").replace("`", "\\`")


_MDV2_SPECIAL = set("_*[]()~`>#+-=|{}.!\\")


def _escape_mdv2(text: str) -> str:
    """Escape ký tự đặc biệt MarkdownV2 ở phần văn xuôi (ngoài code block)."""
    return "".join("\\" + c if c in _MDV2_SPECIAL else c for c in text)


def _format_for_telegram(text: str) -> str:
    """Giữ nguyên block ``` ``` do AGENT tự bọc (bảng/dữ liệu cấu trúc), escape an toàn phần văn xuôi.

    Agent tự quyết phần nào cần render (bọc ```); phần còn lại là văn xuôi bình thường.
    """
    segs = text.split("```")
    if len(segs) % 2 == 0:  # số ``` lẻ (fence chưa cân) -> escape toàn bộ cho an toàn
        return _escape_mdv2(text)
    parts = []
    for i, seg in enumerate(segs):
        if i % 2 == 1:  # bên trong cặp ```
            parts.append("```\n" + _escape_code(seg.strip("\n")) + "\n```")
        else:
            parts.append(_escape_mdv2(seg))
    return "".join(parts)


def _chunks(text: str, size: int = TG_LIMIT) -> list[str]:
    """Chia text thành các phần <= size, ưu tiên cắt theo dòng."""
    if len(text) <= size:
        return [text]
    out, cur = [], ""
    for line in text.split("\n"):
        while len(line) > size:  # dòng quá dài -> cắt cứng
            if cur:
                out.append(cur); cur = ""
            out.append(line[:size]); line = line[size:]
        if cur and len(cur) + len(line) + 1 > size:
            out.append(cur); cur = line
        else:
            cur = line if not cur else cur + "\n" + line
    if cur:
        out.append(cur)
    return out


def send_message(chat_id: str, text: str, reply_to: int | None = None) -> None:
    """Gửi tin: giữ block ``` agent tự bọc, escape văn xuôi; tự chia nếu quá dài; fallback text thường."""
    if not text:
        return
    url = API.format(token=TELEGRAM_BOT_TOKEN, method="sendMessage")
    for i, part in enumerate(_chunks(text)):
        payload = {"chat_id": chat_id, "text": _format_for_telegram(part), "parse_mode": "MarkdownV2"}
        if reply_to is not None and i == 0:
            payload["reply_to_message_id"] = reply_to
        r = requests.post(url, json=payload, timeout=30)
        if not getattr(r, "ok", True):  # MarkdownV2 lỗi -> fallback gửi text thường (raw)
            requests.post(url, json={"chat_id": chat_id, "text": part}, timeout=30)


def send_document(chat_id: str, filename: str, content) -> None:
    """Gửi 1 file (text) về Telegram qua sendDocument (multipart upload)."""
    data_bytes = content.encode("utf-8") if isinstance(content, str) else (content or b"")
    requests.post(
        API.format(token=TELEGRAM_BOT_TOKEN, method="sendDocument"),
        data={"chat_id": chat_id},
        files={"document": (filename or "file.txt", data_bytes)},
        timeout=60,
    )


def handle_update(update: dict, ask_fn=ask_agent, send_fn=send_message, doc_fn=send_document) -> bool:
    """Xử lý 1 update. Trả True nếu đã trả lời, False nếu bỏ qua. (ask_fn/send_fn/doc_fn inject để test.)"""
    msg = extract_message(update)
    if not msg or not msg["chat_id"]:
        return False
    respond, content = should_respond(msg)
    if not respond:
        return False
    try:
        res = ask_fn(content, msg["user_id"], msg["chat_id"])
        text = res if isinstance(res, str) else (res.get("text") or "")
        files = [] if isinstance(res, str) else (res.get("files") or [])
        reply_to = msg["message_id"] if msg["is_group"] else None
        if text:
            send_fn(msg["chat_id"], text, reply_to)
        for f in files:
            doc_fn(msg["chat_id"], f.get("filename", "file.txt"), f.get("content", ""))
    except Exception as e:  # noqa: BLE001
        print(f"[tg-bridge] lỗi xử lý chat {msg['chat_id']}: {e}")
    return True


# ---------- vòng long-polling ----------
def poll_loop() -> None:
    offset = None
    print(f"[tg-bridge] long-polling… -> agent: {AGENT_ENDPOINT_URL}")
    while True:
        try:
            params = {"timeout": POLL_TIMEOUT}
            if offset is not None:
                params["offset"] = offset
            r = requests.get(
                API.format(token=TELEGRAM_BOT_TOKEN, method="getUpdates"),
                params=params, timeout=POLL_TIMEOUT + 15,
            )
            r.raise_for_status()
            for upd in r.json().get("result", []):
                offset = upd["update_id"] + 1
                handle_update(upd)
        except requests.RequestException as e:
            print(f"[tg-bridge] lỗi mạng, thử lại sau 3s: {e}")
            time.sleep(3)


if __name__ == "__main__":
    missing = [k for k, v in {"TELEGRAM_BOT_TOKEN": TELEGRAM_BOT_TOKEN, "AGENT_ENDPOINT_URL": AGENT_ENDPOINT_URL}.items() if not v]
    if missing:
        raise SystemExit(f"⚠️ Thiếu biến môi trường: {', '.join(missing)}")
    poll_loop()
