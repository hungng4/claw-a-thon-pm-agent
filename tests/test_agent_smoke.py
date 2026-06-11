"""Smoke test end-to-end OFFLINE — không cần MaaS/Notion thật.

Inject 1 fake LLM client (mô phỏng tool-calling) + 1 fake Notion để chạy trọn
vòng reply() của PMAgent: model gọi tool -> agent thực thi -> model trả lời cuối.
Mục đích: chứng minh logic orchestration chạy được local.
"""
import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from agent import PMAgent  # noqa: E402


# ---------- Fake Notion ----------
class FakeNotion:
    def query(self, database, filter=None, sorts=None):
        if database == "sprints":
            return [{"id": "s1", "Name": "Sprint 12", "Status": "Active",
                     "Start": "2026-06-10", "End": "2026-06-23",
                     "Goal": "Hoàn thiện combat system v1"}]
        if database == "tasks":
            return [
                {"id": "t1", "Title": "Combat hitbox system", "Status": "Done", "Assignee": ["Bình"]},
                {"id": "t2", "Title": "Hitbox tuning", "Status": "In Progress", "Assignee": ["An"], "Due": "2026-06-08"},
                {"id": "t3", "Title": "VFX combo", "Status": "Blocked", "Assignee": ["Bình"]},
            ]
        return []

    def create(self, *a, **k):
        return {"id": "new-page"}

    def update(self, *a, **k):
        return {"id": "updated"}


# ---------- Fake LLM client mô phỏng tool-calling ----------
class _Fn:
    def __init__(self, name, args):
        self.name = name
        self.arguments = json.dumps(args)


class _ToolCall:
    def __init__(self, name, args):
        self.id = "call_1"
        self.type = "function"
        self.function = _Fn(name, args)


class _Msg:
    def __init__(self, content=None, tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls

    def model_dump(self):
        return {"role": "assistant", "content": self.content,
                "tool_calls": [{"id": t.id, "type": "function",
                                "function": {"name": t.function.name,
                                             "arguments": t.function.arguments}}
                               for t in (self.tool_calls or [])]}


class _Choice:
    def __init__(self, msg):
        self.message = msg


class _Resp:
    def __init__(self, msg):
        self.choices = [_Choice(msg)]


class FakeCompletions:
    def __init__(self):
        self.calls = 0

    def create(self, model, messages, tools=None, temperature=None):
        self.calls += 1
        if self.calls == 1:
            # Lượt 1: model quyết định gọi tool truy vấn sprint
            return _Resp(_Msg(tool_calls=[_ToolCall("notion_query",
                                                    {"database": "sprints",
                                                     "filter_preset": "active_sprint"})]))
        # Lượt 2: đã có dữ liệu tool -> trả lời cuối
        assert any(m.get("role") == "tool" for m in messages), "Tool result chưa được đưa lại cho model"
        return _Resp(_Msg(content="📊 Sprint 12 (10/06→23/06) đang Active, goal: combat system v1."))


class FakeClient:
    def __init__(self):
        self.chat = type("c", (), {"completions": FakeCompletions()})()


def test_reply_loop_end_to_end():
    agent = PMAgent(client=FakeClient(), notion=FakeNotion())
    out = agent.reply("Sprint hiện tại thế nào rồi?")
    assert "Sprint 12" in out
    assert agent.client.chat.completions.calls == 2  # 1 lần gọi tool + 1 lần trả lời
    print("PASS reply loop:", out)


def test_tool_dispatch_direct():
    agent = PMAgent(client=FakeClient(), notion=FakeNotion())
    res = agent._run_tool("notion_query", {"database": "tasks"})
    rows = json.loads(res)
    assert len(rows) == 3 and rows[2]["Status"] == "Blocked"
    print("PASS tool dispatch: 3 tasks, có 1 Blocked")


def test_clock_tool():
    agent = PMAgent(client=FakeClient(), notion=FakeNotion())
    res = json.loads(agent._run_tool("clock_now", {}))
    assert "today" in res
    print("PASS clock:", res["today"])


if __name__ == "__main__":
    test_reply_loop_end_to_end()
    test_tool_dispatch_direct()
    test_clock_tool()
    print("\n✅ Tất cả smoke test PASS — agent chạy trọn vòng local (mock model + Notion).")
