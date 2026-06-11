# Mạnh — PM Agent for Game Production 🤖

> Claw-a-thon 2026 · Track: **Agentic Assistant**
> Trợ lý AI hỗ trợ Project Manager / Producer điều phối dự án game, deploy thành tài khoản chat trong nhóm **Zalo**, dữ liệu trên **Notion**.

## Mô tả ngắn (299 ký tự — copy thẳng vào Submission Form)
> Vấn đề: PM game tốn nhiều giờ tổng hợp tiến độ, blocker, milestone từ nhiều nguồn. Người dùng: Producer/PM & team sản xuất game. Giải pháp: agent AI trong nhóm Zalo, đọc/ghi Notion, tự trả lời về sprint, milestone, rủi ro và viết báo cáo. Giá trị: tiết kiệm giờ, cảnh báo trễ sớm, minh bạch tiến độ.

## Vấn đề
Trong sản xuất game, PM/Producer phải liên tục tổng hợp tiến độ từ nhiều bộ phận (Art, Design, Engineering, QA, LiveOps), bám milestone (Alpha/Beta/Soft Launch), gỡ blocker và viết báo cáo. Việc này tốn thời gian, dễ sót, và thông tin tản mát.

## Giải pháp
**Mạnh** là agent AI sống trong nhóm Zalo của team. Hỏi bằng tiếng Việt tự nhiên, agent tự truy vấn Notion và trả lời tức thì về 4 mảng:

1. **Sprint & Task tracking** — tổng quan sprint, % hoàn thành, task quá hạn, standup digest.
2. **Milestone & Roadmap** — bám mốc lớn, cảnh báo nguy cơ trễ kèm phân tích.
3. **Risk & Blocker** — phát hiện blocker, dependency chéo, đề xuất hành động & owner.
4. **Report & Communication** — weekly report, release note, cập nhật stakeholder.

Agent **tự khai báo là AI** với người dùng (tuân thủ rulebook mục 11.1) và **không bịa số liệu** — mọi con số lấy từ Notion.

## Kiến trúc
```
Nhóm Zalo ──webhook──► zalo_adapter.py ──► PMAgent (agent.py)
                                              │
                          system_prompt + 4 skill playbooks
                                              │
                                   Model MaaS (Gemma/Qwen)
                                              │
                                   tool-calling ──► Notion (Tasks/Sprints/Milestones/Risks)
```

## Cấu trúc repo
```
agent/
  system_prompt.md          # persona + luật hành xử + khai báo AI
  config.yaml               # model, skills, tools, lịch báo cáo
  skills/                   # 4 playbook: sprint / milestone / risk / reporting
integrations/notion/
  schema.md                 # data model 4 database Notion
  notion_client.py          # helper query/create/update/comment
src/
  agent.py                  # vòng lặp hội thoại + tool-calling
  zalo_adapter.py           # webhook Zalo OA
docs/
  sample_data.md            # dữ liệu synthetic + kịch bản demo video
tests/
  test_notion_props.py      # test offline chuyển đổi property
```

## Quickstart (local)
```bash
pip install -r requirements.txt
cp .env.example .env          # điền NOTION_TOKEN, MAAS_API_KEY, db ids, zalo token...

# Tạo 4 database trên Notion theo integrations/notion/schema.md, nhập docs/sample_data.md

python tests/test_notion_props.py     # kiểm tra nhanh (không cần network)
python src/agent.py                   # REPL chat thử với agent
python src/zalo_adapter.py            # chạy webhook server (port 8080)
```

## Deploy trên AgentBase
1. Push repo (đã xong).
2. Tạo OpenClaw instance, nạp `agent/config.yaml` + `system_prompt.md` + skills.
3. Cấu hình MaaS model (Gemma/Qwen) và Notion connector qua biến môi trường.
4. Kết nối webhook Zalo OA tới `/webhook/zalo`, thêm agent vào nhóm.

## Tuân thủ luật Claw-a-thon
- ✅ Agent tự khai báo là AI ngay khi vào nhóm / khi được chào (mục 11.1).
- ✅ Chỉ dùng dữ liệu mẫu/synthetic, không PII hay dữ liệu khách hàng thật (mục 9, 11).
- ✅ Ưu tiên model MaaS (Gemma/Qwen) theo tinh thần cuộc thi (FAQ).

## Nguồn tham khảo
- Notion API: https://developers.notion.com
- Claw-a-thon 2026 Rulebook: https://greennode.ai/claw-a-thon-rulebook

---
*Sản phẩm dự thi Claw-a-thon 2026. Bản quyền theo điều khoản cuộc thi (mục 9.2).*
