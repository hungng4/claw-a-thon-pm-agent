#!/usr/bin/env bash
# Chạy toàn bộ test offline (không cần MaaS/Notion/Zalo thật).
set -e
cd "$(dirname "$0")"
echo "== compile =="
python3 -m py_compile integrations/notion/notion_client.py src/agent.py src/zalo_adapter.py
echo "== test 1: Notion property conversion =="
python3 tests/test_notion_props.py
echo "== test 2: agent reply loop (mock LLM + Notion) =="
python3 tests/test_agent_smoke.py
echo "== test 3: Zalo webhook =="
python3 tests/test_zalo_webhook.py
echo ""
echo "✅ DONE — tất cả test offline PASS."
