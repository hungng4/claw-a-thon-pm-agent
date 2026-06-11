"""Test offline cho chuyển đổi properties Notion (không cần network)."""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
from integrations.notion.notion_client import _read_prop, _to_notion_props  # noqa: E402


def test_title_conversion():
    out = _to_notion_props({"Title": "Combat hitbox"})
    assert out["Title"]["title"][0]["text"]["content"] == "Combat hitbox"


def test_select_and_date():
    out = _to_notion_props({"Status": ("select", "Blocked"), "Due": ("date", "2026-06-12")})
    assert out["Status"]["select"]["name"] == "Blocked"
    assert out["Due"]["date"]["start"] == "2026-06-12"


def test_read_select():
    assert _read_prop({"type": "select", "select": {"name": "Done"}}) == "Done"


def test_read_title():
    prop = {"type": "title", "title": [{"plain_text": "Hello"}]}
    assert _read_prop(prop) == "Hello"


if __name__ == "__main__":
    test_title_conversion()
    test_select_and_date()
    test_read_select()
    test_read_title()
    print("OK: tất cả test property pass")
