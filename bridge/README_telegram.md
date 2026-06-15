# Telegram ↔ Mạnh bridge (khuyến nghị)

Bridge nối **Telegram** với agent **Mạnh** trên AgentBase bằng **long-polling** —
chạy trên máy bạn (hoặc bất kỳ máy nào có internet), **không cần URL công khai**.

```
[Chat/Nhóm Telegram] ⇄ Telegram Bot API ⇄ telegram_bridge.py (máy bạn) ⇄ Mạnh (AgentBase)
```

## Hành xử
- **Nhóm**: chỉ trả lời khi tin bắt đầu `Mạnh`/`/manh`, là `/command`, @mention bot, hoặc reply vào tin của bot.
- **Chat 1-1**: trả lời mọi tin.

## Các bước

1. **Tạo bot, lấy token** — trong Telegram chat với **@BotFather**:
   - `/newbot` → đặt tên + username (kết thúc bằng `bot`, vd `manh_pm_bot`).
   - BotFather trả về **token** dạng `123456:ABC-...`.
   - (Khuyến nghị cho nhóm) `/setprivacy` → chọn bot → **Disable** nếu muốn bot đọc mọi tin để bắt prefix `Mạnh ...`; hoặc để **Enable** (mặc định) thì trong nhóm bot chỉ thấy `/command`, @mention, reply — vẫn hoạt động.

2. **Cài deps** (đã có trong `requirements.txt`):
   ```bash
   pip install requests
   ```

3. **Chạy bridge**:
   ```bash
   export TELEGRAM_BOT_TOKEN="123456:ABC-..."           # token từ BotFather
   export AGENT_ENDPOINT_URL="https://endpoint-36cacee7-c038-4d8a-9e8f-1202f51d4624.agentbase-runtime.aiplatform.vngcloud.vn"
   export BOT_USERNAME="manh_pm_bot"                      # để nhận @mention trong nhóm (không gồm @)
   python3 bridge/telegram_bridge.py
   ```

4. Nhắn cho bot (DM): gõ gì cũng được. Trong nhóm: `Mạnh sprint sao rồi?` hoặc `/start`.

## Biến môi trường

| Biến | Mặc định | Ý nghĩa |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | (bắt buộc) | token từ @BotFather |
| `AGENT_ENDPOINT_URL` | (bắt buộc) | URL endpoint agent trên AgentBase |
| `BOT_USERNAME` | — | username bot (không @), để nhận diện @mention |
| `BOT_PREFIXES` | `mạnh,/manh,manh` | prefix kích hoạt trong nhóm |
| `AGENT_TIMEOUT` | `60` | timeout (giây) gọi agent |
| `POLL_TIMEOUT` | `30` | long-poll timeout getUpdates |

## Mapping hội thoại
- `user_id` (người gửi) → header `X-GreenNode-AgentBase-User-Id` (actor cho long-term memory).
- `chat_id` (chat/nhóm) → header `X-GreenNode-AgentBase-Session-Id` (mỗi nhóm = một mạch hội thoại + Memory riêng).

> Telegram là kênh **chính thức, dễ & ổn định** — khác openzca (Zalo cá nhân, rủi ro ToS).
> Bản openzca vẫn còn trong repo (`bridge/openzca_bridge.py`) như phương án phụ.
