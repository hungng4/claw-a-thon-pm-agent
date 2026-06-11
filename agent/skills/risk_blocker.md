# Skill: Risk & Blocker Management

Áp dụng khi phát hiện / theo dõi rủi ro, blocker, hoặc dependency chéo giữa các bộ phận.

## Khi nào kích hoạt
Từ khóa: "blocker", "bị chặn", "đang kẹt", "rủi ro", "risk", "phụ thuộc", "chờ", "dependency", "vướng".
Hoặc chủ động: khi quét task thấy status = Blocked, hoặc task chờ output của bộ phận khác.

## Phân loại bộ phận game production
Art · Design · Engineering · QA · Audio · LiveOps · Production.
Dependency chéo thường gặp: Engineering chờ asset từ Art; QA chờ build từ Engineering; Design chờ data balance.

## Quy trình
1. `notion.query(Risks)` + `notion.query(Tasks, status=Blocked)`.
2. Với mỗi blocker: xác định ai chặn ai (from team → to team), task bị ảnh hưởng, thời gian kẹt.
3. Đánh giá mức độ: Cao (chặn milestone) · Trung bình (chặn sprint) · Thấp.
4. Đề xuất owner xử lý + hành động cụ thể.

## Mẫu trả lời
```
🔴 Blocker đang mở (3)

1. [Cao] "VFX combo" — Engineering chờ asset particle từ Art (kẹt 3 ngày)
   → Đề xuất: An (Art) ưu tiên xuất asset trước 12/06, hoặc dùng placeholder để dev tiếp.
2. [TB] "Balance boss HP" — Design chờ data từ playtest
   → Đề xuất: chốt lịch playtest nội bộ ngày mai.

⚠️ Rủi ro mới phát hiện:
- 2 task critical-path dồn vào 1 mình Bình → single point of failure.
```

## Ghi nhận rủi ro mới
Khi PM/team nêu một rủi ro: tóm tắt → `notion.create(Risks, {Title, Severity, Owner, Mitigation, Status})`.

## Nguyên tắc
- Mỗi blocker phải có **owner** và **hành động kế tiếp**, không để treo.
- Nêu dependency chéo sớm, trước khi nó thành blocker.
- Không quy trách nhiệm cá nhân; tập trung vào tháo gỡ.
