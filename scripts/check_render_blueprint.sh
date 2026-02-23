#!/usr/bin/env bash
set -euo pipefail

BLUEPRINT_FILE="render.yaml"
TARGET_BRANCH="main"

if [[ ! -f "$BLUEPRINT_FILE" ]]; then
  echo "❌ $BLUEPRINT_FILE не найден в текущей папке"
  exit 1
fi

current_branch="$(git branch --show-current)"
if [[ "$current_branch" != "$TARGET_BRANCH" ]]; then
  echo "⚠️ Сейчас ветка: $current_branch (ожидалась: $TARGET_BRANCH)"
  echo "Переключитесь/переименуйте ветку и запушьте:"
  echo "  git branch -M $TARGET_BRANCH"
  echo "  git push -u origin $TARGET_BRANCH"
  exit 1
fi

if ! git ls-files --error-unmatch "$BLUEPRINT_FILE" >/dev/null 2>&1; then
  echo "❌ $BLUEPRINT_FILE не добавлен в git"
  echo "Сделайте: git add $BLUEPRINT_FILE && git commit -m 'add render blueprint'"
  exit 1
fi

echo "✅ Локально всё ок: файл $BLUEPRINT_FILE есть и ветка $TARGET_BRANCH активна."
echo "Дальше обязательно запушьте в remote:"
echo "  git push -u origin $TARGET_BRANCH"
