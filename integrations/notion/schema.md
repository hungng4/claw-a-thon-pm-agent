# Notion Data Model — PM Agent

Agent đọc/ghi 4 database trong workspace Notion của dự án. Tạo sẵn 4 database này rồi
điền database_id vào `.env` (xem `.env.example`).

> Lưu ý luật Claw-a-thon: chỉ dùng **dữ liệu mẫu / synthetic / ẩn danh**. Không nhập PII
> hay dữ liệu khách hàng thật vào Notion khi demo.

---

## 1. Database: Tasks
| Property      | Type        | Ghi chú |
|---------------|-------------|---------|
| Title         | Title       | Tên task |
| Status        | Select      | Todo / In Progress / In Review / Done / Blocked |
| Assignee      | People/Text | Người phụ trách |
| Discipline    | Select      | Art / Design / Engineering / QA / Audio / LiveOps |
| Sprint        | Relation    | → Sprints |
| Milestone     | Relation    | → Milestones |
| Estimate      | Number      | Story point hoặc giờ |
| Due           | Date        | Hạn chót |
| Blocker note  | Text        | Lý do bị chặn (nếu Status = Blocked) |
| Release tag   | Text        | Gắn version khi đưa vào release note |

## 2. Database: Sprints
| Property   | Type   | Ghi chú |
|------------|--------|---------|
| Name       | Title  | Vd: "Sprint 12" |
| Status     | Select | Planned / Active / Closed |
| Start      | Date   | Ngày bắt đầu |
| End        | Date   | Ngày kết thúc |
| Goal       | Text   | Mục tiêu sprint |
| Velocity   | Number | Điểm hoàn thành (cập nhật khi đóng sprint) |

## 3. Database: Milestones
| Property   | Type   | Ghi chú |
|------------|--------|---------|
| Name       | Title  | Vertical Slice / Alpha / Beta / Soft Launch / Global Launch |
| Status     | Select | Not started / In progress / Done / At risk |
| Target     | Date   | Ngày mục tiêu |
| Progress   | Number | % hoàn thành (0–100) |
| Notes      | Text   | Ghi chú / lý do đổi mốc |

## 4. Database: Risks
| Property    | Type   | Ghi chú |
|-------------|--------|---------|
| Title       | Title  | Mô tả rủi ro |
| Severity    | Select | High / Medium / Low |
| Owner       | People/Text | Người xử lý |
| Mitigation  | Text   | Hành động giảm thiểu |
| Status      | Select | Open / Mitigating / Closed |
| Linked task | Relation | → Tasks (nếu có) |

---

## Mapping tool → database
- `notion.query(database, filter)` → `databases.query`
- `notion.create(database, properties)` → `pages.create` (parent = database_id)
- `notion.update(page_id, properties)` → `pages.update`
- `notion.comment(page_id, text)` → `comments.create`

Xem `notion_client.py` cho helper cụ thể.
