"""Test tầng Flask/Zalo webhook OFFLINE — inject fake agent, không gửi Zalo thật."""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

import zalo_adapter  # noqa: E402


class FakeAgent:
    def reply(self, text, history=None):
        return f"echo: {text}"


def _client():
    zalo_adapter.app.config["AGENT"] = FakeAgent()
    zalo_adapter.send_message = lambda to, txt: captured.append((to, txt))  # chặn gửi thật
    return zalo_adapter.app.test_client()


captured: list = []


def test_health():
    c = _client()
    r = c.get("/health")
    assert r.status_code == 200 and r.get_json()["status"] == "ok"
    print("PASS /health")


def test_greeting_declares_ai():
    captured.clear()
    c = _client()
    r = c.post("/webhook/zalo", json={"sender": {"id": "u1"}, "message": {"text": "/start"}})
    assert r.status_code == 200
    assert any("AI" in txt for _, txt in captured), "Phải tự khai báo là AI (rulebook 11.1)"
    print("PASS greeting khai báo AI:", captured[-1][1][:40], "...")


def test_message_routed_to_agent():
    captured.clear()
    c = _client()
    r = c.post("/webhook/zalo", json={"sender": {"id": "u1"}, "message": {"text": "sprint sao rồi"}})
    assert r.status_code == 200
    assert captured and captured[-1][1] == "echo: sprint sao rồi"
    print("PASS routing tới agent:", captured[-1][1])


if __name__ == "__main__":
    test_health()
    test_greeting_declares_ai()
    test_message_routed_to_agent()
    print("\n✅ Webhook Zalo PASS — boot Flask, khai báo AI, route tin nhắn tới agent.")
