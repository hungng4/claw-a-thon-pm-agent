# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Dự án

**Mạnh** — agent AI hỗ trợ Project Manager / Producer cho tổ sản xuất game tại VNG, dự thi
**Claw-a-thon 2026** (track Agentic Assistant). Deploy thành tài khoản chat trong nhóm **Zalo**,
dữ liệu trên **Notion**. 4 năng lực: sprint/task tracking, milestone & roadmap, risk & blocker,
report & communication. Người dùng chính: Nguyễn Gia Hưng (Nate) — hungng4@vng.com.vn.

## Commands

```bash
./run_tests.sh                # toàn bộ test offline (py_compile + 3 suite, KHÔNG cần creds/network)
python3 tests/test_notion_props.py    # chạy 1 suite đơn lẻ (cũng dùng cho 2 suite còn lại)
python src/agent.py           # REPL chat thử (cần MAAS_API_KEY + NOTION_TOKEN + db ids)
python src/zalo_adapter.py    # chạy webhook Flask (port 8080, cần creds đầy đủ)
pip install -r requirements.txt
```

Tests là plain `python3 <file>` scripts với assert (không phải pytest) — chạy file trực tiếp.
`run_tests.sh` dùng `set -e` nên dừng ngay khi 1 suite fail.

## Kiến trúc

Luồng runtime: **Zalo webhook → `PMAgent.reply()` → tool-calling loop → Notion REST**.

- **`src/agent.py`** — `PMAgent` là trái tim hệ thống. `reply()` chạy vòng lặp tool-calling
  tối đa 6 vòng: gọi model (OpenAI-compatible chat completions) với `TOOLS`, nếu model trả
  `tool_calls` thì `_run_tool()` thực thi rồi feed kết quả lại, lặp đến khi có câu trả lời text.
  4 tool: `notion_query` (có filter_preset: active_sprint/overdue_tasks/blocked_tasks), `notion_create`,
  `notion_update`, `clock_now`. Cả `client` (LLM) và `notion` đều **inject được qua constructor**
  để test offline — đây là điểm mấu chốt cho phép test end-to-end không cần creds thật.

- **System prompt được lắp ráp lúc runtime** — `build_system_prompt()` nối `agent/system_prompt.md`
  (persona + luật hành xử + khai báo AI) với 4 skill playbook trong `agent/skills/` theo thứ tự liệt
  kê trong `agent/config.yaml`. Skill là **văn bản markdown nhồi vào prompt**, không phải code.

- **`agent/config.yaml`** — nguồn sự thật cho model, danh sách skill, tools, channel, schedules.
  `model.base_url_env`/`api_key_env` trỏ tới tên biến env (mặc định `MAAS_BASE_URL`/`MAAS_API_KEY`).

- **`integrations/notion/notion_client.py`** — bọc Notion REST API. Quan trọng nhất là 2 hàm
  chuyển đổi: `_read_prop()` (page Notion → dict phẳng cho LLM đọc) và `_to_notion_props()`
  (dict đơn giản `{field: value}` → định dạng properties Notion). Quy ước value: `('select', x)`,
  `('status', x)`, `('date', 'YYYY-MM-DD')`, `('number', n)`, `('text', s)`, `('relation', [ids])`;
  string thường → rich_text; key `title`/`name` → title. 4 database: tasks/sprints/milestones/risks,
  mỗi cái map sang 1 biến env `NOTION_DB_*`. Filter dựng sẵn ở cuối file.

- **`main.py`** ⭐ — entrypoint production trên AgentBase (`GreenNodeAgentBaseApp`). Bọc
  `PMAgent.reply()` trong `@app.entrypoint`, quản lý lịch sử theo `context.session_id` (Memory hoặc
  in-memory fallback). Đây là file chạy trong container, KHÔNG phải `zalo_adapter.py`.

- **`bridge/telegram_bridge.py`** ⭐ — kênh chính: long-polling Telegram → gọi `/invocations` → `sendMessage`.
  Chạy trên máy dev. `bridge/openzca_bridge.py` = phương án phụ (Zalo cá nhân). Xem `bridge/README*.md`.

- **`src/zalo_adapter.py`** — Flask webhook Zalo OA cũ, **đã bị thay bằng `main.py` + bridges**, giữ làm
  tham chiếu (không dùng production). Test cũ vẫn chạy. `GREETING`/`is_greeting_trigger` import từ `agent.py`.

Schema 4 database Notion ở `integrations/notion/schema.md`; dữ liệu mẫu + kịch bản demo ở `docs/sample_data.md`.

## Ràng buộc Claw-a-thon (bắt buộc, ảnh hưởng tới code)

- Agent **PHẢI tự khai báo là AI** (rulebook 11.1) — `GREETING` + `is_greeting_trigger` ở `src/agent.py`
  (dùng chung cho `main.py` + bridges), và trong `system_prompt.md`. Đừng xoá phần này.
- Chỉ dùng dữ liệu mẫu/synthetic/ẩn danh — **KHÔNG PII / dữ liệu khách hàng thật**.
- Ưu tiên model MaaS (Gemma/Qwen) của GreenNode AI Platform.
- Rulebook: https://greennode.ai/claw-a-thon-rulebook

## Deploy (ĐÃ CHỐT: Custom Agent — đang LIVE)

Quyết định trước đây đã chốt **Custom Agent** (`/agent-runtimes`) và **đã deploy**. Entrypoint là
`main.py` (`GreenNodeAgentBaseApp`: `@app.entrypoint` POST /invocations, `@app.ping` GET /health,
port 8080), Docker `python:3.13-slim`, LLM map sang `LLM_BASE_URL/LLM_API_KEY/LLM_MODEL`. Kênh chat
chính là **Telegram** (`bridge/telegram_bridge.py`, bot `@manh_pmbot`); openzca/Zalo là phương án phụ.
Notion đã nối (4 DB mock). Memory hội thoại dùng in-memory fallback (runtime chặn egress tới Memory API).

➡️ **Toàn bộ chi tiết handoff ở [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md)** — tài nguyên đã deploy
(runtime id, endpoint, image), biến môi trường, cách nối Notion, redeploy, known issues, kịch bản demo.

Skill deploy ở `.claude/skills/agentbase*` (project-local), dùng `/agentbase-*` như `/agentbase-wizard`.
Repo nguồn `greennode-agentbase-skills/` đã gitignore. **Deploy cần Docker + IAM creds (`.greennode.json`) + mạng VNG.**

## Git

`.git` clone từ máy Mac; sandbox Cowork không sửa được (permission) — commit/push làm từ máy Mac.
`greennode-agentbase-skills/` là repo riêng (có `.git` lồng), không phải submodule của project.
