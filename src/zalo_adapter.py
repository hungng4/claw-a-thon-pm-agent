"""Zalo adapter — nhận webhook tin nhắn nhóm Zalo, gọi PMAgent, gửi trả lời.

Dùng Zalo Official Account (OA) Message API. Đây là skeleton minh hoạ luồng;
endpoint thực tế & cách xác thực chữ ký theo tài liệu Zalo OA hiện hành.

Luật Claw-a-thon mục 11.1: agent phải tự khai báo là AI -> xử lý ở GREETING bên dưới.
"""
from __future__ import annotations

import hashlib
import hmac
import os

import requests
from flask import Flask, jsonify, request

from agent import PMAgent

app = Flask(__name__)
pm = PMAgent()

# Lịch sử hội thoại theo từng nhóm (demo: in-memory; production nên dùng store ngoài)
_history: dict[str, list[dict]] = {}

GREETING = (
    "Chào cả nhà 👋 Mình là Mạnh 🤖 — trợ lý AI hỗ trợ PM cho tổ sản xuất game, "
    "không phải người thật nha. Cứ hỏi mình về sprint, task, milestone, blocker hay báo cáo nhé!"
)

ZALO_SEND_URL = "https://openapi.zalo.me/v3.0/oa/message/cs"


def _verify_signature(body: bytes, signature: str | None) -> bool:
    secret = os.environ.get("ZALO_APP_SECRET")
    if not secret or not signature:
        return True  # bỏ qua khi chưa cấu hình (chỉ dùng cho local/demo)
    mac = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(mac, signature)


def send_message(to_id: str, text: str) -> None:
    token = os.environ.get("ZALO_OA_TOKEN")
    if not token:
        print(f"[DRY-RUN gửi tới {to_id}]: {text}")
        return
    payload = {"recipient": {"user_id": to_id}, "message": {"text": text}}
    requests.post(ZALO_SEND_URL, headers={"access_token": token}, json=payload, timeout=15)


@app.get("/health")
def health():
    return jsonify({"status": "ok", "agent": "Manh PM Agent"})


@app.post("/webhook/zalo")
def webhook():
    if not _verify_signature(request.get_data(), request.headers.get("X-ZEvent-Signature")):
        return jsonify({"error": "invalid signature"}), 403

    event = request.get_json(silent=True) or {}
    sender = (event.get("sender") or {}).get("id", "unknown")
    text = (event.get("message") or {}).get("text", "").strip()
    event_name = event.get("event_name", "")

    # Lời chào / khai báo AI khi được thêm vào nhóm hoặc gặp lệnh chào
    if event_name in ("follow", "user_join_group") or text.lower() in ("/start", "hi", "chào mạnh"):
        send_message(sender, GREETING)
        return jsonify({"ok": True})

    if not text:
        return jsonify({"ok": True})

    hist = _history.setdefault(sender, [])
    answer = pm.reply(text, hist)
    hist += [{"role": "user", "content": text}, {"role": "assistant", "content": answer}]
    _history[sender] = hist[-20:]  # giữ 10 lượt gần nhất

    send_message(sender, answer)
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
