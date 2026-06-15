"""Notion client helper cho PM Agent.

Bọc Notion REST API (https://developers.notion.com) thành các hàm gọn mà agent dùng:
query / create / update / comment trên 4 database Tasks, Sprints, Milestones, Risks.

Yêu cầu env:
    NOTION_TOKEN              integration token (secret_xxx)
    NOTION_DB_TASKS          database_id của Tasks
    NOTION_DB_SPRINTS        database_id của Sprints
    NOTION_DB_MILESTONES     database_id của Milestones
    NOTION_DB_RISKS          database_id của Risks
"""
from __future__ import annotations

import os
from datetime import date
from typing import Any

import requests

NOTION_VERSION = "2022-06-28"
BASE = "https://api.notion.com/v1"

DB_ENV = {
    "tasks": "NOTION_DB_TASKS",
    "sprints": "NOTION_DB_SPRINTS",
    "milestones": "NOTION_DB_MILESTONES",
    "risks": "NOTION_DB_RISKS",
}


class NotionClient:
    def __init__(self, token: str | None = None):
        # Không bắt buộc token lúc khởi tạo: agent vẫn boot khi chưa nối Notion.
        # Chỉ báo lỗi (được PMAgent._run_tool bắt) khi thực sự gọi API Notion.
        self.token = token or os.environ.get("NOTION_TOKEN", "")

    @property
    def headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.token}",
            "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json",
        }

    # ---- internal ----
    def _require_token(self) -> None:
        if not self.token:
            raise RuntimeError("Chưa nối Notion (thiếu NOTION_TOKEN) — vui lòng cấu hình để dùng dữ liệu.")

    def _db_id(self, database: str) -> str:
        env_key = DB_ENV.get(database.lower())
        if not env_key:
            raise ValueError(f"Database không hợp lệ: {database}")
        db_id = os.environ.get(env_key)
        if not db_id:
            raise RuntimeError(f"Chưa cấu hình database Notion '{database}' (thiếu {env_key}).")
        return db_id

    def _post(self, path: str, payload: dict) -> dict:
        self._require_token()
        r = requests.post(f"{BASE}/{path}", headers=self.headers, json=payload, timeout=30)
        r.raise_for_status()
        return r.json()

    def _patch(self, path: str, payload: dict) -> dict:
        self._require_token()
        r = requests.patch(f"{BASE}/{path}", headers=self.headers, json=payload, timeout=30)
        r.raise_for_status()
        return r.json()

    # ---- public ----
    def query(self, database: str, filter: dict | None = None, sorts: list | None = None) -> list[dict]:
        """Truy vấn 1 database, trả về list page (đã làm phẳng properties)."""
        payload: dict[str, Any] = {}
        if filter:
            payload["filter"] = filter
        if sorts:
            payload["sorts"] = sorts
        data = self._post(f"databases/{self._db_id(database)}/query", payload)
        return [self._flatten(p) for p in data.get("results", [])]

    def create(self, database: str, properties: dict) -> dict:
        payload = {
            "parent": {"database_id": self._db_id(database)},
            "properties": _to_notion_props(properties),
        }
        return self._post("pages", payload)

    def update(self, page_id: str, properties: dict) -> dict:
        return self._patch(f"pages/{page_id}", {"properties": _to_notion_props(properties)})

    def comment(self, page_id: str, text: str) -> dict:
        payload = {
            "parent": {"page_id": page_id},
            "rich_text": [{"text": {"content": text}}],
        }
        return self._post("comments", payload)

    # ---- helpers ----
    @staticmethod
    def _flatten(page: dict) -> dict:
        """Rút gọn page Notion thành dict phẳng dễ dùng cho LLM."""
        out: dict[str, Any] = {"id": page["id"], "url": page.get("url")}
        for name, prop in page.get("properties", {}).items():
            out[name] = _read_prop(prop)
        return out


# ---------- chuyển đổi properties ----------
def _read_prop(prop: dict) -> Any:
    t = prop["type"]
    val = prop.get(t)
    if t in ("title", "rich_text"):
        return "".join(x.get("plain_text", "") for x in val) if val else ""
    if t == "select":
        return val["name"] if val else None
    if t == "number":
        return val
    if t == "date":
        return val["start"] if val else None
    if t == "people":
        return [p.get("name") for p in val] if val else []
    if t == "relation":
        return [r["id"] for r in val] if val else []
    if t == "status":
        return val["name"] if val else None
    return val


def _to_notion_props(props: dict) -> dict:
    """Chuyển dict đơn giản {field: value} → định dạng properties của Notion.

    Quy ước value:
      str dạng title  -> dùng key 'Title'/'Name' sẽ map title
      ('select', x)    -> select
      ('date', 'YYYY-MM-DD') -> date
      ('number', n)    -> number
      ('text', s)      -> rich_text
      ('relation', [ids]) -> relation
    """
    out: dict[str, Any] = {}
    for field, value in props.items():
        if isinstance(value, tuple):
            kind, v = value
            if kind == "select":
                out[field] = {"select": {"name": v}}
            elif kind == "status":
                out[field] = {"status": {"name": v}}
            elif kind == "date":
                out[field] = {"date": {"start": v}}
            elif kind == "number":
                out[field] = {"number": v}
            elif kind == "text":
                out[field] = {"rich_text": [{"text": {"content": v}}]}
            elif kind == "relation":
                out[field] = {"relation": [{"id": i} for i in v]}
        elif field.lower() in ("title", "name"):
            out[field] = {"title": [{"text": {"content": str(value)}}]}
        else:
            out[field] = {"rich_text": [{"text": {"content": str(value)}}]}
    return out


# ---------- filter dựng sẵn ----------
def active_sprint_filter() -> dict:
    return {"property": "Status", "select": {"equals": "Active"}}


def overdue_tasks_filter() -> dict:
    today = date.today().isoformat()
    return {
        "and": [
            {"property": "Due", "date": {"before": today}},
            {"property": "Status", "select": {"does_not_equal": "Done"}},
        ]
    }


def blocked_tasks_filter() -> dict:
    return {"property": "Status", "select": {"equals": "Blocked"}}
