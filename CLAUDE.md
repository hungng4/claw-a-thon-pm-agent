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

- **`src/zalo_adapter.py`** — Flask webhook. `/webhook/zalo` (POST) verify chữ ký HMAC, route
  event, gọi `get_agent().reply()`, gửi trả lời qua Zalo OA API. `/health` (GET) cho health check.
  Agent khởi tạo **lazy** (chỉ dựng khi có request đầu); test inject fake qua `app.config["AGENT"]`.
  Lịch sử hội thoại in-memory theo `sender`, giữ 10 lượt gần nhất.

Schema 4 database Notion ở `integrations/notion/schema.md`; dữ liệu mẫu + kịch bản demo ở `docs/sample_data.md`.

## Ràng buộc Claw-a-thon (bắt buộc, ảnh hưởng tới code)

- Agent **PHẢI tự khai báo là AI** (rulebook 11.1) — xử lý ở `GREETING` trong `zalo_adapter.py`
  và trong `system_prompt.md`. Đừng xoá phần này.
- Chỉ dùng dữ liệu mẫu/synthetic/ẩn danh — **KHÔNG PII / dữ liệu khách hàng thật**.
- Ưu tiên model MaaS (Gemma/Qwen) của GreenNode AI Platform.
- Rulebook: https://greennode.ai/claw-a-thon-rulebook

## ⚠️ Quyết định deploy đang mở (gate mọi refactor)

Code hiện tại là Flask thuần — **chưa đúng contract AgentBase**. Hai hướng, **hỏi Nate chốt trước khi refactor**:

1. **Custom Agent** (`/agent-runtimes`): refactor `main.py` dùng `GreenNodeAgentBaseApp`
   (`@app.entrypoint` cho `POST /invocations`, `@app.ping` cho `GET /health`, port 8080), thêm
   `Dockerfile` (`FROM python:3.13-slim`), `requirements.txt` (`greennode-agentbase`). Giữ trọn logic
   PM + Notion, Zalo nối qua bridge riêng. Khi chốt hướng này: map LLM sang OpenAI-compatible
   (`LLM_BASE_URL=https://maas-llm-aiplatform-hcm.api.vngcloud.vn/v1`, `LLM_API_KEY`, `LLM_MODEL`
   lấy qua skill `/agentbase-llm`) — lưu ý `config.yaml` hiện để base_url đoán, cần sửa.
2. **OpenClaw Zalo** (`/openclaws`): template no-code, native Zalo, logic PM dồn vào system prompt,
   Notion nối qua Resource Gateway (MCP). Handler Python không dùng.

Skill deploy đã copy vào `.claude/skills/` (project-local — tự nhận khi mở session trong repo này),
dùng các slash command `/agentbase-*` như `/agentbase-wizard`. Repo nguồn `greennode-agentbase-skills/`
đã gitignore (chỉ là bản clone tham chiếu). **Deploy cần Docker + IAM creds + mạng VNG — không chạy
được trong Cowork sandbox.**

## Git

`.git` clone từ máy Mac; sandbox Cowork không sửa được (permission) — commit/push làm từ máy Mac.
`greennode-agentbase-skills/` là repo riêng (có `.git` lồng), không phải submodule của project.
