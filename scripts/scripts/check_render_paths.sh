#!/usr/bin/env bash
set -euo pipefail

required_files=(render.yaml requirements.txt bot.py)
missing=0

for f in "${required_files[@]}"; do
  if [[ ! -f "$f" ]]; then
    echo "❌ Missing file in repo root: $f"
    missing=1
  fi
done

if [[ $missing -eq 1 ]]; then
  echo "\nПохоже, вы запускаете команду не из корня проекта."
  exit 1
fi

echo "✅ Repo root contains required files: render.yaml, requirements.txt, bot.py"
echo "Если Render пишет 'requirements.txt not found', проверьте в сервисе:"
echo "- Runtime: Python (не Docker)"
echo "- Root Directory: пусто или ."
echo "- Build Command: python -m pip install -r ./requirements.txt"
echo "- Start Command: python ./bot.py"
