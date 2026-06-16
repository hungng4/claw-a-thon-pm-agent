# Claw-a-thon — Submission kit (team Autobot)

> Gom sẵn mọi field để copy vào form. Deadline **12:00 trưa 17/06**. Chỗ nào cần điền: ⬜.

## Thông tin nộp
- **Tên team:** Autobot
- **Track:** Agentic Assistant
- **Tên Agent / use case:** Mạnh — Trợ lý AI cho Project Manager / Producer tổ sản xuất game
- **GitHub repo (public):** https://github.com/hungng4/claw-a-thon-pm-agent ✅
- **VNG Domain Endpoint:** `https://endpoint-36cacee7-c038-4d8a-9e8f-1202f51d4624.agentbase-runtime.aiplatform.vngcloud.vn`
  (endpoint kỹ thuật `/invocations` + `/health` — trải nghiệm thực tế qua Telegram, xem dưới)
- **Telegram bot (trải nghiệm):** `@manh_pmbot` → https://t.me/manh_pmbot ⬜ *(cần bridge luôn-bật trong lúc voting — xem mục Hosting)*
- **Video demo (2–3’):** ⬜ *(YouTube Unlisted / OneDrive — quay theo kịch bản dưới)*
- **Thumbnail:** ⬜ *(xem concept dưới)*

---

## Mô tả use case (< 300 từ)

**Mạnh — Trợ lý AI cho Project Manager / Producer tổ sản xuất game**

Trong sản xuất game, PM/Producer tốn rất nhiều thời gian mở Notion, lọc bảng, tổng hợp tiến độ và đốc thúc thủ công. **Mạnh** là một agent AI hoạt động như thành viên chat trong nhóm **Telegram** của team: PM chỉ cần nhắn tin tự nhiên, Mạnh truy vấn dữ liệu dự án trên **Notion** và trả lời tức thì, kèm phân tích và đề xuất.

Mạnh có 4 năng lực:
- **Sprint & task tracking** — tình hình sprint, task quá hạn, ai đang làm gì.
- **Milestone & roadmap** — tiến độ Alpha/Beta/Launch, cảnh báo nguy cơ trễ.
- **Risk & blocker** — phát hiện blocker, đề xuất hành động giảm thiểu.
- **Report & communication** — tự tổng hợp daily standup / weekly report.

Ví dụ: *“Có blocker nào không?”* → Mạnh liệt kê task bị chặn kèm lý do và đề xuất xử lý; *“Tạo task ‘Fix camera shake’ cho Cường due 18/06”* → ghi thẳng vào Notion.

Kiến trúc: **Custom Agent trên GreenNode AgentBase** (LLM **Qwen** qua MaaS), **Notion** làm nguồn dữ liệu, **Telegram** làm kênh giao tiếp. Agent tự khai báo là AI theo rulebook và chỉ dùng dữ liệu synthetic.

Giá trị: cắt giảm thời gian PM dành cho tổng hợp/đốc thúc thủ công, phát hiện sớm rủi ro tiến độ, và đưa thông tin dự án tới cả team ngay trong công cụ chat họ dùng hằng ngày — biến quản lý sản xuất thành một cuộc hội thoại.

*(~220 từ)*

---

## Kịch bản video demo (2–3 phút)

Chuẩn bị: bridge Telegram đang chạy, mock data đã có trên Notion (15 task, Sprint 12 Active, milestone Alpha 72%, 2 task blocked). Mở sẵn 1 tab Notion để lia minh hoạ. Quay màn hình Telegram.

| Thời lượng | Cảnh | Nội dung |
|---|---|---|
| 0:00–0:18 | **Hook** | Vấn đề: PM tốn thời gian tổng hợp Notion thủ công. Title card: "Mạnh — AI PM Assistant · Team Autobot". |
| 0:18–0:32 | **Giới thiệu** | 1 slide kiến trúc: Telegram ⇄ AgentBase (Custom Agent, Qwen MaaS) ⇄ Notion + Memory. Nói nhanh 4 năng lực. |
| 0:32–0:42 | **Khai báo AI** | Gõ `/start` → Mạnh tự giới thiệu là AI (rulebook 11.1). |
| 0:42–1:05 | **Sprint tracking** | "Mạnh, sprint hiện tại sao rồi?" → tổng quan Sprint 12 + cảnh báo task quá hạn (bảng trong khung code, gọn). |
| 1:05–1:25 | **Blocker** | "Có blocker nào không?" → 2 blocker (VFX combo, Tutorial flow) + đề xuất. |
| 1:25–1:45 | **Milestone & risk** | "Alpha có kịp không?" → Alpha 72% + rủi ro trễ + đề xuất cắt scope. |
| 1:45–2:10 | **Ghi Notion** | "Tạo task 'Fix camera shake' cho Cường due 18/06" → xác nhận → **lia qua Notion thấy task mới**. |
| 2:10–2:30 | **Xuất file** | "Xuất weekly report ra file" → bot gửi **file `.md`** đính kèm ngay trong Telegram. |
| 2:30–2:50 | **Trí nhớ (điểm nhấn)** | "Nhớ giúp tuần này ưu tiên combat" → hỏi lại "tuần này mình dặn gì?" → bot **nhớ** (AgentBase Memory). |
| 2:50–3:00 | **Đóng** | Giá trị: PM hỏi-đáp tự nhiên, chủ động, nhớ ngữ cảnh. "Built on GreenNode AgentBase". |

Mẹo: quay 1 lần liền mạch; agent trả chậm thì cắt dựng. Bước **Xuất file + Trí nhớ** là khác biệt so với chatbot thường → nhấn mạnh khi voting. Giữ ≤ 3 phút (có thể bỏ bớt 1 nhịp nếu dài).

➡️ **Lời thoại (voiceover) chi tiết từng nhịp + bản đọc liền:** xem [`docs/video_script.md`](video_script.md).

---

## Concept thumbnail (16:9, 1280×720)
- Mascot robot thân thiện "Mạnh" 🤖 + yếu tố PM (bảng Kanban / biểu đồ sprint) ở nền.
- Logo nhỏ: Telegram + Notion + "GreenNode AgentBase".
- Chữ lớn: **"Mạnh — AI PM Assistant"**; góc: *Team Autobot · Agentic Assistant*.
- Công cụ gợi ý: Canva (template YouTube thumbnail) hoặc AI image gen (Midjourney/DALL·E) với prompt mô tả trên.

---

## Checklist submit
- [x] GitHub repo public
- [ ] Video demo 2–3’ (YouTube Unlisted/OneDrive)
- [x] VNG Domain Endpoint (kỹ thuật) — **+ Telegram bot luôn-bật cho voting** (xem Hosting trong `docs/DEPLOYMENT.md`/§hosting)
- [x] Mô tả use case < 300 từ (ở trên)
- [x] Tên team (Autobot) + track (Agentic Assistant)
- [ ] Thumbnail

> ⚠️ **Quan trọng cho voting (22/06+):** bridge Telegram phải chạy 24/7 (đưa lên 1 host luôn-bật), nếu không bot sẽ "im" khi BTC/voter trải nghiệm. Xem mục Hosting.
