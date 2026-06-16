# Dữ liệu mẫu (synthetic) cho demo

> Dữ liệu giả lập để demo Claw-a-thon — KHÔNG phải dữ liệu thật. Nhập vào Notion để quay video.

## Sprints
| Name | Status | Start | End | Goal |
|------|--------|-------|-----|------|
| Sprint 12 | Active | 2026-06-10 | 2026-06-23 | Hoàn thiện combat system v1 |

## Milestones
| Name | Status | Target | Progress |
|------|--------|--------|----------|
| Vertical Slice | Done | 2026-05-15 | 100 |
| Alpha | In progress | 2026-06-30 | 72 |
| Beta | Not started | 2026-08-15 | 0 |
| Soft Launch | Not started | 2026-09-30 | 0 |

## Tasks (trích)
| Title | Status | Assignee | Discipline | Due |
|-------|--------|----------|------------|-----|
| Combat hitbox system | Done | Bình | Engineering | 2026-06-09 |
| Enemy AI patrol v1 | Done | Cường | Engineering | 2026-06-10 |
| Hitbox tuning | In Progress | An | Design | 2026-06-08 |
| VFX combo | Blocked | Bình | Engineering | 2026-06-13 |
| Balance boss HP | In Progress | An | Design | 2026-06-15 |

## Risks
| Title | Severity | Owner | Status |
|-------|----------|-------|--------|
| 2 task critical-path dồn vào 1 dev | Medium | PM | Open |
| Asset particle trễ ảnh hưởng VFX | High | Art Lead | Mitigating |

## Kịch bản demo (gợi ý cho video 2-3 phút)

Demo trên **Telegram** (bot `@manh_pmbot`). Dữ liệu mock đã có sẵn trên Notion (15 task, 3 sprint, 5 milestone, 4 risk).

1. `/start` → Mạnh **tự khai báo là AI** (rulebook 11.1).
2. "Mạnh, sprint hiện tại sao rồi?" → query Notion → tổng quan Sprint 12 + **cảnh báo task quá hạn** (bảng nằm trong khung code, gọn).
3. "Có blocker nào không?" → liệt kê 2 blocker (VFX combo, Tutorial flow) + lý do + **đề xuất hành động**.
4. "Alpha có kịp không?" → phân tích milestone Alpha (72%) + **rủi ro trễ** + đề xuất cắt scope.
5. "Tạo task 'Fix camera shake' cho Cường due 18/06" → agent xác nhận → **ghi vào Notion** (lia qua Notion thấy task mới).
6. "Xuất weekly report ra file giúp mình" → agent gửi **file `.md`** đính kèm về Telegram (tính năng export_file).
7. **Memory** (điểm nhấn): "Nhớ giúp tuần này ưu tiên combat nhé" → lát sau hỏi "tuần này mình dặn ưu tiên gì?" → agent **nhớ** (lưu qua AgentBase Memory, bền qua phiên).

> Mẹo quay: bám 7 nhịp trên, giữ ≤ 3 phút. Mở Notion sẵn 1 tab để minh hoạ bước 5. Bước 6-7 là khác biệt so với chatbot thường (xuất file + trí nhớ).
