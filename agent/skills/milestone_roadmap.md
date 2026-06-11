# Skill: Milestone & Roadmap

Áp dụng khi hỏi về milestone, lộ trình phát hành, hay nguy cơ trễ mốc lớn.

## Khi nào kích hoạt
Từ khóa: "milestone", "roadmap", "alpha", "beta", "soft launch", "global launch", "còn bao lâu tới", "có kịp không", "lộ trình".

## Mốc chuẩn trong game production
Prototype → Vertical Slice → Alpha (feature complete) → Beta (content complete) →
Soft Launch (giới hạn vùng) → Global Launch → LiveOps.

## Quy trình
1. `notion.query(Milestones)` → lấy danh sách mốc + target date + status + % hoàn thành.
2. `clock.now()` → tính số ngày còn lại tới mỗi mốc.
3. Với mốc gần nhất: kéo các task/sprint liên quan để ước lượng khả năng kịp.
4. Cảnh báo nếu: ngày còn lại < khối lượng việc còn lại, hoặc có dependency/blocker chặn mốc.

## Mẫu trả lời
```
🗺️ Roadmap

✅ Vertical Slice — done (15/05)
🟡 Alpha — target 30/06 (còn 20 ngày), 72% hoàn thành
   ⚠️ Rủi ro: combat system còn 8 task, tốc độ hiện tại ~3 task/tuần → có thể trễ ~5 ngày
🔵 Beta — target 15/08 (chưa khởi động)
🔵 Soft Launch — target 30/09

👉 Đề xuất: cân nhắc cắt scope "advanced combo" khỏi Alpha hoặc bổ sung 1 dev.
```

## Nguyên tắc
- Luôn gắn cảnh báo trễ với dữ liệu (số task còn lại, velocity), không phỏng đoán cảm tính.
- Khi PM đổi target date: xác nhận → `notion.update(milestone_id, {Target: ...})` và ghi lý do vào comment.
- Đề xuất trade-off (cắt scope / dời mốc / thêm nguồn lực) nhưng để con người quyết.
