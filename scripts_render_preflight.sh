#!/usr/bin/env bash
set -euo pipefail

if [[ ! -f .env ]]; then
  echo "❌ .env not found. Run: cp .env.example .env"
  exit 1
fi

required=(BOT_TOKEN ADMIN_CHAT_ID)
missing=0
for key in "${required[@]}"; do
  if ! grep -Eq "^${key}=.+" .env; then
    echo "❌ Missing required env: ${key}"
    missing=1
  fi
done

if [[ $missing -eq 1 ]]; then
  echo "\nИсправьте .env и повторите проверку."
  exit 1
fi

python -m py_compile bot.py

echo "✅ Preflight OK: .env заполнен, синтаксис bot.py корректный."
echo "Дальше можно деплоить в Render (Blueprint) или запускать локально: python bot.py"
