#!/usr/bin/env python3
"""Set GitHub Actions secrets từ .env + .greennode.json (cho workflow deploy).

Yêu cầu: GitHub CLI đã đăng nhập (gh auth login).
Chạy từ thư mục gốc repo:  python3 scripts/setup_github_secrets.py
"""
import json
import os
import subprocess

REPO = "hungng4/claw-a-thon-pm-agent"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Biến lấy từ .env (id/secret không nhạy + secret thật)
ENV_KEYS = [
    "LLM_API_KEY", "MEMORY_ID", "MEMORY_STRATEGY_ID", "NOTION_TOKEN",
    "NOTION_DB_TASKS", "NOTION_DB_SPRINTS", "NOTION_DB_MILESTONES", "NOTION_DB_RISKS",
]


def load_env(path):
    d = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            d[k.strip()] = v.strip()
    return d


def main():
    g = json.load(open(os.path.join(ROOT, ".greennode.json"), encoding="utf-8"))
    e = load_env(os.path.join(ROOT, ".env"))

    vals = {
        "GREENNODE_CLIENT_ID": g.get("client_id", ""),
        "GREENNODE_CLIENT_SECRET": g.get("client_secret", ""),
    }
    for k in ENV_KEYS:
        vals[k] = e.get(k, "")

    missing = []
    for k, v in vals.items():
        if not v:
            print("⚠️  SKIP (rỗng):", k)
            missing.append(k)
            continue
        # giá trị truyền qua stdin -> không lộ trên dòng lệnh
        subprocess.run(["gh", "secret", "set", k, "--repo", REPO], input=v.encode(), check=True)
        print("✅ set", k)

    total = len(vals) - len(missing)
    print(f"\nXong: set {total}/{len(vals)} secret." + (f"  Thiếu: {', '.join(missing)}" if missing else "  (đủ)"))


if __name__ == "__main__":
    main()
