#!/usr/bin/env bash
set -euo pipefail

TARGET_BRANCH="main"
current_branch="$(git branch --show-current)"
local_head="$(git rev-parse --short HEAD)"
local_msg="$(git log -1 --pretty=%s)"

echo "Local branch: $current_branch"
echo "Local HEAD:   $local_head ($local_msg)"

if [[ "$current_branch" != "$TARGET_BRANCH" ]]; then
  echo "❌ Вы не на ветке $TARGET_BRANCH"
  echo "Сделайте: git branch -M $TARGET_BRANCH"
  exit 1
fi

if ! git remote get-url origin >/dev/null 2>&1; then
  echo "⚠️ Remote 'origin' не настроен. Render не увидит локальные коммиты без push."
  echo "Добавьте remote и запушьте:"
  echo "  git remote add origin <repo-url>"
  echo "  git push -u origin $TARGET_BRANCH"
  exit 0
fi

git fetch origin "$TARGET_BRANCH" --quiet || true
if git rev-parse --verify "origin/$TARGET_BRANCH" >/dev/null 2>&1; then
  remote_head="$(git rev-parse --short origin/$TARGET_BRANCH)"
  remote_msg="$(git log -1 --pretty=%s origin/$TARGET_BRANCH)"
  echo "Remote HEAD:  $remote_head ($remote_msg)"

  if [[ "$local_head" != "$remote_head" ]]; then
    echo "❌ Render будет деплоить старый коммит, пока вы не запушите изменения."
    echo "Сделайте: git push origin $TARGET_BRANCH"
    exit 1
  fi

  echo "✅ Local и origin/$TARGET_BRANCH совпадают. Render должен брать актуальный коммит."
else
  echo "⚠️ В origin нет ветки $TARGET_BRANCH."
  echo "Сделайте: git push -u origin $TARGET_BRANCH"
fi
