# Skill: Sprint & Task Tracking

Áp dụng khi người dùng hỏi về sprint hiện tại, tiến độ, chia/gán task, hoặc tổng hợp standup.

## Khi nào kích hoạt
Từ khóa: "sprint", "task", "tiến độ", "standup", "ai đang làm gì", "còn bao nhiêu việc", "burndown", "assign".

## Quy trình
1. `clock.now()` để biết hôm nay và sprint nào đang active.
2. `notion.query(Sprints, status=Active)` → lấy sprint hiện tại (ngày bắt đầu/kết thúc, goal).
3. `notion.query(Tasks, sprint=<id>)` → lấy toàn bộ task của sprint.
4. Phân nhóm theo status: Todo / In Progress / In Review / Done / Blocked.
5. Tính nhanh: % hoàn thành (Done / tổng), số task quá hạn (due < today & ≠ Done), số ngày còn lại.

## Mẫu trả lời — tổng quan sprint
```
📊 Sprint 12 (10/06 → 23/06) — còn 4 ngày
Goal: Hoàn thiện combat system v1

Tiến độ: 14/22 task ✅ (64%)
🟡 In progress: 5 · 🔴 Quá hạn: 2 · ⛔ Blocked: 1

⚠️ Cần chú ý:
- "Hitbox tuning" (An) quá hạn 2 ngày
- "VFX combo" (Bình) đang blocked chờ asset từ Art
```

## Chia / gán task
- Khi tạo task: bắt buộc có Title, Assignee, Sprint, Due, Estimate (nếu có).
- Tóm tắt task sắp tạo → chờ duyệt → `notion.create(Tasks, {...})`.
- Khi đổi assignee/status: `notion.update(page_id, {...})` sau khi xác nhận.

## Standup digest
Khi được gọi "tổng hợp standup" hoặc chạy theo lịch sáng:
- Hôm qua done: liệt kê task chuyển sang Done trong 24h.
- Hôm nay: task In Progress theo từng người.
- Blocker: task Blocked + lý do (lấy từ field Blocker note).
Giữ digest ngắn, nhóm theo người.

## Nguyên tắc
- Không tự ý đóng task của người khác.
- Burndown xấu (còn nhiều task mà sắp hết sprint) → nêu cảnh báo + đề xuất giãn scope hoặc thêm người.
