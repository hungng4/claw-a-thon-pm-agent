"""Test shim openzca OFFLINE — logic phân loại nhóm/DM, trigger prefix, route /hook.

Không gọi openzca thật, không gọi agent thật: ask_agent/send_reply bị inject fake.
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from bridge import openzca_bridge as b  # noqa: E402


def test_is_group():
    assert b.is_group({"chatType": "group"}) is True
    assert b.is_group({"chatType": 1}) is True
    assert b.is_group({"chatType": "user"}) is False
    assert b.is_group({}) is False
    print("PASS is_group")


def test_extract_maps_fields():
    m = b.extract({"content": "  sprint?  ", "threadId": 123, "senderId": 9, "chatType": "group",
                   "mentionIds": [7]})
    assert m["content"] == "sprint?" and m["thread_id"] == "123"
    assert m["sender_id"] == "9" and m["is_group"] is True and m["mention_ids"] == ["7"]
    print("PASS extract")


def test_should_respond_dm_always():
    ok, content = b.should_respond("bất kỳ gì", group=False, mention_ids=[])
    assert ok is True and content == "bất kỳ gì"
    print("PASS DM trả lời mọi tin")


def test_should_respond_group_prefix_strips():
    ok, content = b.should_respond("Mạnh sprint sao rồi", group=True, mention_ids=[])
    assert ok is True and content == "sprint sao rồi", content
    ok2, _ = b.should_respond("/manh báo cáo tuần", group=True, mention_ids=[])
    assert ok2 is True
    print("PASS group prefix -> trả lời + bỏ prefix")


def test_should_respond_group_no_trigger_ignored():
    ok, _ = b.should_respond("chuyện phiếm trong nhóm", group=True, mention_ids=[])
    assert ok is False
    print("PASS group không prefix -> bỏ qua")


def test_should_respond_group_mention():
    saved = b.BOT_USER_ID
    b.BOT_USER_ID = "bot-1"
    try:
        ok, content = b.should_respond("xem giúp blocker", group=True, mention_ids=["bot-1"])
        assert ok is True and content == "xem giúp blocker"
    finally:
        b.BOT_USER_ID = saved
    print("PASS group @mention -> trả lời")


def test_hook_route_group_prefix():
    captured = {}
    b.ask_agent = lambda message, user_id, session_id: f"reply:{message}|u={user_id}|s={session_id}"
    b.send_reply = lambda thread_id, text, group: captured.update(thread=thread_id, text=text, group=group)
    c = b.app.test_client()

    r = c.post("/hook", json={"content": "Mạnh tình hình sprint", "threadId": "g1",
                              "senderId": "u9", "chatType": "group"})
    assert r.status_code == 200
    assert captured["thread"] == "g1" and captured["group"] is True
    assert captured["text"] == "reply:tình hình sprint|u=u9|s=g1", captured["text"]
    print("PASS /hook group prefix -> gọi agent + gửi reply")


def test_hook_route_group_ignored():
    captured = {}
    b.send_reply = lambda *a, **k: captured.update(sent=True)
    c = b.app.test_client()
    r = c.post("/hook", json={"content": "tám chuyện", "threadId": "g1", "chatType": "group"})
    assert r.status_code == 200 and r.get_json().get("skipped") is True
    assert "sent" not in captured
    print("PASS /hook group không trigger -> bỏ qua, không gửi")


if __name__ == "__main__":
    test_is_group()
    test_extract_maps_fields()
    test_should_respond_dm_always()
    test_should_respond_group_prefix_strips()
    test_should_respond_group_no_trigger_ignored()
    test_should_respond_group_mention()
    test_hook_route_group_prefix()
    test_hook_route_group_ignored()
    print("\n✅ openzca bridge PASS — phân loại nhóm/DM, trigger prefix/mention, route /hook.")
