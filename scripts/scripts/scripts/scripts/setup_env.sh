#!/usr/bin/env bash
set -euo pipefail

ENV_FILE=".env"
EXAMPLE_FILE=".env.example"

if [[ ! -f "$EXAMPLE_FILE" ]]; then
  echo "❌ $EXAMPLE_FILE not found"
  exit 1
fi

if [[ -f "$ENV_FILE" ]]; then
  echo "ℹ️  $ENV_FILE already exists. It will not be overwritten."
else
  cp "$EXAMPLE_FILE" "$ENV_FILE"
  echo "✅ Created $ENV_FILE from $EXAMPLE_FILE"
fi

ensure_key() {
  local key="$1"
  if ! grep -Eq "^${key}=" "$ENV_FILE"; then
    echo "${key}=" >> "$ENV_FILE"
  fi
}

ensure_key "BOT_TOKEN"
ensure_key "ADMIN_CHAT_ID"
ensure_key "ADMIN_USERNAMES"

set_value_if_empty() {
  local key="$1"
  local value="$2"
  if grep -Eq "^${key}=$" "$ENV_FILE"; then
    sed -i "s|^${key}=$|${key}=${value}|" "$ENV_FILE"
  fi
}

set_value_if_empty "ADMIN_USERNAMES" "cloudmanagerss"

cat <<'MSG'

Дальше заполните обязательные значения в .env:
- BOT_TOKEN=токен_от_BotFather
- ADMIN_CHAT_ID=ваш_telegram_id

Проверка перед деплоем:
./scripts_render_preflight.sh
MSG
