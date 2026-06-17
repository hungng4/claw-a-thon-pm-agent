# Mạnh — PM Agent for Game Production 🤖

> Claw-a-thon 2026 · Track: **Agentic Assistant** · Team: **Autobot**
> Trợ lý AI hỗ trợ Project Manager / Producer điều phối dự án game — hoạt động như **bot Telegram** trong nhóm team, dữ liệu trên **Notion**, chạy trên **GreenNode AgentBase**.

**Trải nghiệm:** Telegram bot 👉 https://t.me/manh_pmbot
**Endpoint (VNG domain):** https://endpoint-36cacee7-c038-4d8a-9e8f-1202f51d4624.agentbase-runtime.aiplatform.vngcloud.vn

---

## Vấn đề
PM/Producer game tốn hàng giờ mỗi tuần mở Notion, lọc bảng, tổng hợp tiến độ, gỡ blocker và viết báo cáo. Thông tin tản mát, dễ sót, dễ trễ.

## Giải pháp
**Mạnh** là agent AI sống trong nhóm Telegram của team. Hỏi bằng tiếng Việt tự nhiên → Mạnh truy vấn Notion và trả lời tức thì, kèm phân tích + đề xuất. 4 năng lực:

1. **Sprint & Task tracking** — tổng quan sprint, task quá hạn, ai đang làm gì.
2. **Milestone & Roadmap** — bám mốc Alpha/Beta/Launch, cảnh báo nguy cơ trễ.
3. **Risk & Blocker** — phát hiện blocker, đề xuất hành động giảm thiểu.
4. **Report & Communication** — tự tổng hợp standup/weekly report, **xuất file** (.md/.csv/.docx Word) gửi thẳng vào Telegram.

Thêm: **nhớ ngữ cảnh xuyên phiên** (lịch sử hội thoại + team + phong cách từng người) qua **AgentBase Memory**; **ghi thẳng vào Notion** (tạo/cập nhật task). Agent **tự khai báo là AI** (rulebook 11.1) và chỉ dùng **dữ liệu synthetic**.

## Kiến trúc
```
[Nhóm/Chat Telegram]
        │  long-polling
        ▼
bridge/telegram_bridge.py   (chạy trên máy/VM — nối Telegram ↔ agent)
        │  POST /invocations (+ header user/session)
        ▼
main.py  →  GreenNodeAgentBaseApp  (Custom Agent trên AgentBase, port 8080)
        │
   PMAgent (src/agent.py): system prompt + 4 skill, tool-calling loop
        ├─► LLM: Qwen (GreenNode MaaS, OpenAI-compatible)
        ├─► Notion REST (Tasks / Sprints / Milestones / Risks)
        └─► AgentBase Memory (events + long-term records: team, phong cách)
```

## Model & tuân thủ luật
- **LLM:** `qwen/qwen3-5-27b` qua **GreenNode AI Platform (MaaS)** — model nội bộ cuộc thi, không dùng model ngoài.
- ✅ Agent tự khai báo là AI khi vào nhóm / khi được chào (mục 11.1).
- ✅ Chỉ dùng dữ liệu **synthetic/ẩn danh**, không PII / dữ liệu khách hàng thật.
- Rulebook: https://greennode.ai/claw-a-thon-rulebook

## Chạy & test (local, không cần creds)
```bash
./run_tests.sh        # compile + 5 bộ test offline (Notion props, agent loop, webhook, 2 bridge)
```
Cần chạy thật (điền `.env` theo `.env.example`):
```bash
pip install -r requirements.txt
python3 src/agent.py                  # REPL chat với agent (cần LLM + Notion creds)
python3 bridge/telegram_bridge.py     # bridge Telegram (cần TELEGRAM_BOT_TOKEN + AGENT_ENDPOINT_URL)
```

## Deploy (Custom Agent trên AgentBase)
Build Docker → push Container Registry → tạo/cập nhật runtime. Chi tiết đầy đủ (tài nguyên đã deploy, biến môi trường, redeploy, known issues) ở **[`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md)**.

## Cấu trúc repo
```
main.py                       # entrypoint AgentBase (Custom Agent)
Dockerfile / .dockerignore
src/agent.py                  # PMAgent: tool-calling loop, GREETING, export_file/remember
integrations/
  notion/notion_client.py     # wrap Notion REST + filters; schema.md = data model
  docx_export.py              # markdown → file .docx (Word)
agent/
  system_prompt.md, skills/   # persona + 4 playbook (nhồi vào prompt)
  config.yaml                 # model, skills, kênh
bridge/
  telegram_bridge.py          # kênh chính (Telegram, long-polling) + README_telegram.md
  openzca_bridge.py           # phương án phụ (Zalo cá nhân)
tests/                        # 5 bộ test offline (run_tests.sh)
docs/
  sample_data.md              # dữ liệu synthetic + kịch bản demo
  DEPLOYMENT.md               # handoff: deploy/vận hành
  SUBMISSION.md, video_script.md
```

---
*Sản phẩm dự thi Claw-a-thon 2026 — Team Autobot. Dữ liệu trong demo là synthetic.*
