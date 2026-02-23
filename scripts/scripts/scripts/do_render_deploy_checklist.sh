#!/usr/bin/env bash
set -euo pipefail

echo "== 1) Проверка ветки/blueprint =="
./scripts/check_render_blueprint.sh || true

echo

echo "== 2) Проверка структуры путей =="
./scripts/check_render_paths.sh || true

echo

echo "== 3) Проверка .env и синтаксиса =="
if [[ ! -f .env ]]; then
  echo "ℹ️  .env не найден. Создаю через setup_env.sh"
  ./scripts/setup_env.sh
fi
./scripts_render_preflight.sh || true

echo

echo "== 4) Проверка, какой коммит увидит Render =="
./scripts/check_render_deploy_commit.sh || true

echo
cat <<'MSG'
Готово. Дальше в Render:
1) Branch: main
2) Blueprint Path: render.yaml
3) Environment: BOT_TOKEN, ADMIN_CHAT_ID
4) Manual Deploy
MSG
