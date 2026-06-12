# openzca ↔ Mạnh bridge

Shim nối **Zalo (tài khoản cá nhân qua [openzca](https://openzca.com))** với agent **Mạnh** trên AgentBase.
Chạy **trên máy bạn** (cạnh openzca), KHÔNG deploy lên AgentBase.

```
[Nhóm Zalo] ⇄ openzca (máy bạn) ⇄ bridge này ⇄ Mạnh (AgentBase)
```

## Hành xử
- **Nhóm**: chỉ trả lời khi tin bắt đầu bằng prefix `Mạnh`/`/manh`/`manh` **hoặc** bot được @mention.
- **Chat 1-1 (DM)**: trả lời mọi tin.
- openzca mặc định bỏ qua tin của chính tài khoản → không lặp.

## Cài & chạy

1. **Cài deps** (đã có trong `requirements.txt`):
   ```bash
   pip install flask requests
   ```

2. **Cài + đăng nhập openzca** (Node 18+):
   ```bash
   npm install -g openzca      # hoặc theo hướng dẫn trên openzca.com
   openzca login               # quét QR bằng app Zalo (nên dùng tài khoản phụ)
   ```

3. **Chạy bridge** (điền endpoint agent đã deploy):
   ```bash
   export AGENT_ENDPOINT_URL="https://endpoint-36cacee7-c038-4d8a-9e8f-1202f51d4624.agentbase-runtime.aiplatform.vngcloud.vn"
   # tuỳ chọn: BOT_PREFIXES, BOT_USER_ID (để nhận @mention), BRIDGE_PORT (mặc 3000)
   python3 bridge/openzca_bridge.py
   ```

4. **Bật listener openzca trỏ webhook vào bridge**:
   ```bash
   openzca listen --webhook http://localhost:3000/hook -k
   ```

Giờ nhắn trong nhóm: `Mạnh sprint hiện tại sao rồi?` → openzca → bridge → Mạnh → trả lời về nhóm.

## Biến môi trường

| Biến | Mặc định | Ý nghĩa |
|---|---|---|
| `AGENT_ENDPOINT_URL` | (bắt buộc) | URL endpoint agent trên AgentBase |
| `BRIDGE_PORT` | `3000` | cổng server nhận webhook |
| `OPENZCA_BIN` | `openzca` | đường dẫn CLI openzca |
| `BOT_PREFIXES` | `mạnh,/manh,manh` | prefix kích hoạt trong nhóm |
| `BOT_USER_ID` | — | id Zalo của bot, để nhận diện @mention |
| `AGENT_TIMEOUT` | `60` | timeout (giây) gọi agent |

## Lưu ý cần chỉnh khi gặp payload thật
Mình rút field theo tài liệu openzca (`content`, `threadId`, `senderId`, `chatType`, `mentionIds`).
Lần đầu chạy, kiểm tra payload thật bằng `openzca listen --raw | head -1` — nếu tên field/giá trị
`chatType` khác (vd nhóm là số khác `1`), chỉnh `is_group()` / `extract()` trong `openzca_bridge.py`.

⚠️ Tự động hoá tài khoản Zalo cá nhân có thể vi phạm ToS Zalo (rủi ro khoá acc). Dùng tài khoản phụ cho demo.
```
