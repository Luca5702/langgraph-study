#!/usr/bin/env bash
# 一键创建环境并运行全部课程（无需任何 API Key）
set -e
cd "$(dirname "$0")"
if [ ! -d .venv ]; then
  uv venv .venv && uv pip install --python .venv/bin/python langgraph langchain-core langgraph-checkpoint-sqlite
fi
cd lessons
for f in [0-9][0-9]_*.py; do
  echo; echo "################ $f ################"
  ../.venv/bin/python "$f"
done
rm -rf memory.sqlite* __pycache__
