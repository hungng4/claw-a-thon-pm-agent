"""Test Telegram bridge OFFLINE — parse update, trigger nhóm/private, handle_update.

Không gọi Telegram/agent thật: ask_fn/send_fn inject fake.
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from bridge import telegram_bridge as t  # noqa: E402


def _update(text, chat_type="private", chat_id=1, user_id=9, entities=None, reply_bot=False):
    msg = {"message_id": 5, "text": text, "chat": {"id": chat_id, "type": chat_type},
           "from": {"id": user_id}, "entities": entities or []}
    if reply_bot:
        msg["reply_to_message"] = {"from": {"is_bot": True}}
    return {"update_id": 100, "message": msg}


def test_extract_basic():
    m = t.extract_message(_update("  xin chào  ", chat_type="supergroup", chat_id=42))
    assert m["text"] == "xin chào" and m["chat_id"] == "42" and m["is_group"] is True
    assert t.extract_message({"update_id": 1}) is None       # không có message
    assert t.extract_message(_update("")) is None            # text rỗng
    print("PASS extract")


def test_private_always():
    ok, content = t.should_respond(t.extract_message(_update("báo cáo đi", chat_type="private")))
    assert ok is True and content == "báo cáo đi"
    print("PASS private trả lời mọi tin")


def test_group_prefix_strips():
    ok, content = t.should_respond(t.extract_message(_update("Mạnh sprint sao rồi", chat_type="group")))
    assert ok is True and content == "sprint sao rồi", content
    print("PASS group prefix -> trả lời + bỏ prefix")


def test_group_no_trigger_ignored():
    ok, _ = t.should_respond(t.extract_message(_update("tám chuyện", chat_type="group")))
    assert ok is False
    print("PASS group không trigger -> bỏ qua")


def test_group_command():
    ents = [{"type": "bot_command", "offset": 0, "length": 6}]
    ok, _ = t.should_respond(t.extract_message(_update("/start", chat_type="group", entities=ents)))
    assert ok is True
    print("PASS group /command -> trả lời")


def test_group_reply_to_bot():
    ok, _ = t.should_respond(t.extract_message(_update("ok cảm ơn", chat_type="group", reply_bot=True)))
    assert ok is True
    print("PASS group reply-vào-bot -> trả lời")


def test_group_mention():
    saved = t.BOT_USERNAME
    t.BOT_USERNAME = "manhbot"
    try:
        ents = [{"type": "mention", "offset": 0, "length": 8}]
        ok, content = t.should_respond(t.extract_message(
            _update("@manhbot blocker nào gấp", chat_type="group", entities=ents)))
        assert ok is True and "blocker" in content
    finally:
        t.BOT_USERNAME = saved
    print("PASS group @mention -> trả lời")


def test_handle_update_group():
    captured = {}
    ask = lambda message, user_id, session_id: f"reply:{message}|u={user_id}|s={session_id}"
    send = lambda chat_id, text, reply_to=None: captured.update(chat=chat_id, text=text, reply=reply_to)
    done = t.handle_update(_update("Mạnh tình hình", chat_type="supergroup", chat_id=7, user_id=3),
                           ask_fn=ask, send_fn=send)
    assert done is True
    assert captured["chat"] == "7" and captured["reply"] == 5
    assert captured["text"] == "reply:tình hình|u=3|s=7", captured["text"]
    print("PASS handle_update group -> gọi agent + sendMessage")


def test_handle_update_ignored():
    captured = {}
    send = lambda *a, **k: captured.update(sent=True)
    done = t.handle_update(_update("chuyện phiếm", chat_type="group"), ask_fn=lambda *a: "x", send_fn=send)
    assert done is False and "sent" not in captured
    print("PASS handle_update group không trigger -> bỏ qua")


def test_format_for_telegram():
    # văn xuôi: escape ký tự đặc biệt MarkdownV2, KHÔNG tự thêm ```
    f = t._format_for_telegram("Sprint 12 (đang chạy).")
    assert "```" not in f and "\\(" in f and "\\." in f
    # block ``` do agent tự bọc: giữ nguyên fence, KHÔNG escape pipe bên trong
    f2 = t._format_for_telegram("Bảng:\n```\n| a | b |\n```")
    assert f2.count("```") == 2 and "| a | b |" in f2
    # chunk dài
    parts = t._chunks("line\n" * 2000, size=100)
    assert len(parts) > 1 and all(len(p) <= 100 for p in parts)
    print("PASS format Telegram (giữ fence agent, escape văn xuôi) + chunk")


def test_handle_update_with_file():
    cap = {"msgs": [], "docs": []}
    ask = lambda m, u, s: {"text": "đã gửi report", "files": [{"filename": "weekly.md", "content": "# Report"}]}
    send = lambda chat_id, text, reply_to=None: cap["msgs"].append((chat_id, text))
    doc = lambda chat_id, filename, content: cap["docs"].append((chat_id, filename, content))
    done = t.handle_update(_update("Mạnh xuất report", chat_type="private", chat_id="d1"),
                           ask_fn=ask, send_fn=send, doc_fn=doc)
    assert done is True
    assert cap["msgs"][0] == ("d1", "đã gửi report")
    assert cap["docs"][0] == ("d1", "weekly.md", "# Report")
    print("PASS handle_update gửi kèm file qua sendDocument")


def test_handle_update_binary_file():
    """File nhị phân (.docx) đi qua content_b64 -> handle_update decode về bytes trước khi gửi."""
    import base64
    raw = b"PK\x03\x04 fake-docx-bytes"
    cap = {"docs": []}
    ask = lambda m, u, s: {"text": "đã gửi", "files": [
        {"filename": "report.docx", "content_b64": base64.b64encode(raw).decode("ascii")}]}
    send = lambda chat_id, text, reply_to=None: None
    doc = lambda chat_id, filename, content: cap["docs"].append((chat_id, filename, content))
    t.handle_update(_update("Mạnh xuất docx", chat_type="private", chat_id="d2"),
                    ask_fn=ask, send_fn=send, doc_fn=doc)
    assert cap["docs"][0] == ("d2", "report.docx", raw)  # đã decode đúng bytes gốc
    assert isinstance(cap["docs"][0][2], bytes)
    print("PASS handle_update decode content_b64 -> bytes (gửi file .docx)")


if __name__ == "__main__":
    test_extract_basic()
    test_private_always()
    test_group_prefix_strips()
    test_group_no_trigger_ignored()
    test_group_command()
    test_group_reply_to_bot()
    test_group_mention()
    test_handle_update_group()
    test_handle_update_ignored()
    test_format_for_telegram()
    test_handle_update_with_file()
    test_handle_update_binary_file()
    print("\n✅ Telegram bridge PASS — parse update, trigger nhóm/private, handle_update + file.")
