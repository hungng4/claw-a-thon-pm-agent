# Handoff & Deployment — Mạnh PM Agent

> Tài liệu để dev khác **catch up nhanh**: hệ thống đã đổi gì, đang deploy ra sao, chạy/redeploy thế nào, kịch bản demo. Cập nhật lần cuối: 2026-06-15.

---

## 1. TL;DR — đang ở đâu

- Agent **"Mạnh"** đã deploy **LIVE** trên GreenNode AgentBase dưới dạng **Custom Agent** (Docker image + `/agent-runtimes`).
- Kênh chat chính: **Telegram** (bot `@manh_pmbot`) qua bridge long-polling chạy trên máy dev.
- Dữ liệu: **Notion** (4 database mock, synthetic) — đã nối, agent đọc/ghi thật.
- LLM: **GreenNode MaaS `qwen/qwen3-5-27b`**.
- Memory hội thoại: **in-memory fallback** (xem [Known issues](#7-known-issues--quyết-định)).

Hỏi thử (endpoint hoặc Telegram): *"Mạnh, sprint hiện tại sao rồi?"*, *"task nào blocked?"*.

---

## 2. Thay đổi kiến trúc (Flask demo → AgentBase Custom Agent)

Ban đầu repo là skeleton Flask (`src/zalo_adapter.py`) gọi `PMAgent`. Đã refactor sang contract AgentBase:

```
[Telegram] ⇄ bridge/telegram_bridge.py (máy dev) ⇄ main.py (AgentBase runtime) ⇄ PMAgent ⇄ Notion REST
                                                         │
                                                  GreenNodeAgentBaseApp
                                                  POST /invocations + GET /health (port 8080)
```

| File | Vai trò | Thay đổi |
|------|---------|----------|
| `main.py` ⭐ mới | Entrypoint AgentBase: `@app.entrypoint` (POST /invocations) bọc `PMAgent.reply()`, `@app.ping` (GET /health). Quản lý lịch sử theo `context.session_id`. | Mới |
| `Dockerfile` ⭐ mới | `python:3.13-slim`, port 8080, `CMD python main.py` | Mới |
| `.dockerignore` ⭐ mới | Loại secrets/.claude/tests — **giữ `agent/*.md`** (cần lúc runtime) | Mới |
| `src/agent.py` | `PMAgent` (tool-calling loop). Map LLM env `LLM_BASE_URL/LLM_API_KEY/LLM_MODEL` (fallback `MAAS_*`). `GREETING` + `is_greeting_trigger` đặt ở đây (dùng chung). | Sửa |
| `integrations/notion/notion_client.py` | Wrap Notion REST. **Resilient**: không bắt buộc `NOTION_TOKEN` lúc init, chỉ báo lỗi khi thực sự gọi API. | Sửa |
| `src/zalo_adapter.py` | Bản Zalo OA cũ — **KHÔNG dùng cho production** (giữ làm tham chiếu). | Sửa nhẹ |
| `bridge/telegram_bridge.py` ⭐ mới | Bridge Telegram long-polling → `/invocations` → `sendMessage`. | Mới |
| `bridge/openzca_bridge.py` ⭐ mới | Bridge Zalo cá nhân (openzca) — **phương án phụ**. | Mới |
| `requirements.txt` | + `greennode-agentbase` | Sửa |
| `agent/config.yaml` | `model.name = qwen/qwen3-5-27b` | Sửa |

**Tài nguyên resilient (quan trọng):** Notion thiếu token và Memory timeout đều **không làm sập** agent — degrade nhẹ nhàng (Notion báo "chưa nối", Memory về in-memory). Xem `main.py._load_history/_save_turn` + `notion_client._require_token`.

---

## 3. Tài nguyên đã deploy (AgentBase)

> Đây là **định danh** (không phải secret). Secret nằm trong `.env` (gitignored).

| Mục | Giá trị |
|-----|---------|
| Runtime ID | `runtime-f925ad1f-e028-47ed-9962-e046c2b9b99b` |
| Endpoint (PUBLIC) | `https://endpoint-36cacee7-c038-4d8a-9e8f-1202f51d4624.agentbase-runtime.aiplatform.vngcloud.vn` |
| Image hiện tại | `vcr.vngcloud.vn/111480-abp112161/manh-pm-agent:v20260615111450` |
| CR repo | `111480-abp112161` (registry `vcr.vngcloud.vn`) |
| Flavor / Network | `runtime-s2-general-2x4` / PUBLIC, min=max=1 replica |
| Model | `qwen/qwen3-5-27b` (MaaS), API key tên `claw26-team307` |
| Memory store | `memory-9ddaae2c-ad0f-46ab-adf4-39fc76cf0b69` (ACTIVE; xem known issues) |
| Telegram bot | `@manh_pmbot` |

Console: https://aiplatform.console.vngcloud.vn/agent-runtime?tab=runtime

---

## 4. Biến môi trường (tên — KHÔNG ghi value secret ở đây)

Local: `.env` (gitignored). Runtime: `.env.runtime` (subset, sinh từ `.env`). Template: `.env.example`.

| Biến | Dùng ở | Ghi chú |
|------|--------|---------|
| `LLM_API_KEY` `LLM_BASE_URL` `LLM_MODEL` | agent (runtime) | LLM MaaS; lấy key qua `/agentbase-llm` |
| `MEMORY_ID` | agent (runtime) | Memory store id |
| `NOTION_TOKEN` | agent (runtime) | Internal integration secret (xem §6) |
| `NOTION_DB_TASKS/SPRINTS/MILESTONES/RISKS` | agent (runtime) | 4 database id |
| `TELEGRAM_BOT_TOKEN` `BOT_USERNAME` | **bridge** (máy dev) | KHÔNG đưa vào runtime |
| `AGENT_ENDPOINT_URL` | **bridge** (máy dev) | URL endpoint ở §3 |
| IAM creds | `.greennode.json` (gitignored) | `client_id`/`client_secret` cho deploy/management |

> ⚠️ Trên AgentBase Runtime, `GREENNODE_CLIENT_ID/SECRET/AGENT_IDENTITY/ENDPOINT_URL` **tự inject** — không set thủ công.
> `.env.runtime` = `grep -E '^(LLM_API_KEY|LLM_BASE_URL|LLM_MODEL|MEMORY_ID|NOTION_TOKEN|NOTION_DB_*)=' .env` (cố tình loại biến của bridge).

---

## 5. Kênh chat

### Telegram (chính) — `bridge/telegram_bridge.py`
Long-polling, **không cần URL công khai cho bridge**. Chi tiết: `bridge/README_telegram.md`.
```bash
# .env đã có TELEGRAM_BOT_TOKEN, BOT_USERNAME, AGENT_ENDPOINT_URL
python3 bridge/telegram_bridge.py     # chạy trên máy dev; tắt máy là bot ngừng
```
Hành xử: **nhóm** chỉ trả lời khi prefix (`Mạnh`/`/manh`), @mention, /command, hoặc reply-vào-bot; **DM** trả lời mọi tin.

### openzca / Zalo cá nhân (phụ) — `bridge/openzca_bridge.py`
Phương án dự phòng (Zalo OA không dùng được). Rủi ro ToS Zalo. Chi tiết: `bridge/README.md`.

---

## 6. Notion (4 database mock)

Schema: `integrations/notion/schema.md`. Mock data: `docs/sample_data.md`. Page cha: **"Mạnh PM — Demo Data"** (trong **private workspace** của owner; chứa Tasks/Sprints/Milestones/Risks).

**Quan trọng — luật tương thích với code agent:**
- `Status` phải là **Select** (filters dùng `select.equals`), KHÔNG phải kiểu "Status".
- `Due/Start/End/Target` = **Date**; `Assignee/Owner` = **Text** (để gắn tên tự do, khỏi cần user Notion thật).
- Tên property phải khớp schema (Tasks dùng `Title`; Sprints/Milestones dùng `Name`).

**Nối Notion cho 1 môi trường mới:**
1. Tạo 4 database đúng schema + nhồi mock data (xem §6 + `sample_data.md`).
2. Tạo **Internal Integration** (notion.so/my-integrations) **cùng workspace** với page → copy token.
3. Page → **••• → Connections → add integration** (cấp quyền cả 4 DB con).
4. Lấy 4 db id bằng token:
   ```bash
   # POST https://api.notion.com/v1/search  (Notion-Version 2022-06-28, filter object=database)
   # map title -> id cho NOTION_DB_*
   ```
5. Set `NOTION_TOKEN` + 4 `NOTION_DB_*` vào `.env` → redeploy (§8). Nối Notion **chỉ đổi env, không rebuild image**.

> Lưu ý: **move page giữa workspace làm đổi hết database id** → phải dò lại id (bước 4).

---

## 7. Known issues / Quyết định

- **Memory egress (đang dùng in-memory fallback):** runtime container **không kết nối được** `agentbase.api.vngcloud.vn` (Memory API) — `ConnectTimeout` 30s, dù LLM host (`maas-llm-...`) thì OK. Đã xác minh: cùng image+creds chạy 1.2s từ máy dev, timeout trong runtime → **giới hạn egress của runtime**, không phải lỗi code. Quyết định: giữ **in-memory** (nhớ trong phiên, 1 replica; mất khi restart) cho demo. Muốn Memory bền vững: xin VNG mở egress runtime→agentbase.api, hoặc dùng VPC (nhưng endpoint sẽ thành private → đổi cách nối bridge).
- **Endpoint PUBLIC không có auth gate:** ai có URL + gọi đúng format đều invoke được. Demo data toàn synthetic nên rủi ro thấp; muốn siết thì đặt Resource Gateway (`/agentbase-gateway`).
- **Bridge chạy trên máy dev:** tắt máy/terminal là bot ngừng. Production thật nên đưa bridge lên 1 server/VM luôn-bật.

---

## 8. Vận hành (commands)

```bash
# Test offline (5 suite, không cần creds/mạng)
./run_tests.sh

# Redeploy khi ĐỔI CODE: build + push + update runtime
TAG="v$(date +%Y%m%d%H%M%S)"
IMAGE="vcr.vngcloud.vn/111480-abp112161/manh-pm-agent:${TAG}"
bash .claude/skills/agentbase/scripts/cr.sh credentials docker-login
docker build --platform linux/amd64 -t "$IMAGE" .
docker push "$IMAGE"
bash .claude/skills/agentbase/scripts/runtime.sh update runtime-f925ad1f-e028-47ed-9962-e046c2b9b99b \
  --image "$IMAGE" --flavor runtime-s2-general-2x4 --env-file .env.runtime --from-cr --network-mode PUBLIC

# Redeploy khi CHỈ ĐỔI ENV (vd thêm Notion): dùng lại image cũ, chỉ --env-file
# (regen .env.runtime từ .env trước)

# Log / debug runtime
bash .claude/skills/agentbase/scripts/runtime.sh logs runtime-f925ad1f-e028-47ed-9962-e046c2b9b99b --limit 80
bash .claude/skills/agentbase/scripts/runtime.sh get runtime-f925ad1f-e028-47ed-9962-e046c2b9b99b

# Health check
curl -s "$AGENT_ENDPOINT_URL/health"
```
Deploy cần: Docker chạy + IAM creds (`.greennode.json`) + mạng VNG. Skill deploy ở `.claude/skills/agentbase*`.

---

## 9. Kịch bản demo (đã có sẵn mock data)

Today giả định trong data: Sprint 12 Active (10–23/06), 2 task overdue, 1 task Blocked.

1. *"Mạnh, sprint hiện tại sao rồi?"* → tổng quan Sprint 12 + cảnh báo task quá hạn.
2. *"Có blocker nào không?"* → **VFX combo** (Bình, chờ asset particle) + đề xuất.
3. *"Alpha có kịp không?"* → milestone Alpha 72% + rủi ro trễ + đề xuất cắt scope.
4. *"Tạo task 'Fix camera shake' cho Cường due 18/06"* → agent ghi vào Notion.
5. *"Viết weekly report giúp mình"* → tổng hợp report.

(Agent tự khai báo là AI — rulebook 11.1 — ở lời chào / `is_greeting_trigger`.)

---

## 10. Bản đồ repo (file chính)

```
main.py                         # entrypoint AgentBase (Custom Agent)
Dockerfile / .dockerignore
src/agent.py                    # PMAgent: tool-calling loop, GREETING
integrations/notion/
  notion_client.py              # wrap Notion REST + filters
  schema.md                     # schema 4 database
agent/
  config.yaml                   # model, skills, tools
  system_prompt.md, skills/*.md # persona + 4 playbook (nhồi vào prompt lúc runtime)
bridge/
  telegram_bridge.py + README_telegram.md   # kênh chính
  openzca_bridge.py + README.md              # kênh phụ
tests/                          # 5 suite offline (chạy qua run_tests.sh)
docs/sample_data.md             # mock data + kịch bản demo
docs/DEPLOYMENT.md              # ← bạn đang đọc
.env.example                    # template biến môi trường
```
