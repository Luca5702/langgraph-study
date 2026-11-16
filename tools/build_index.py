"""
PageIndex 风格的「无向量树状目录索引」生成器（零 API 成本）。
扫描：
  1. lessons/*.py          —— 本地 11 节课程
  2. repos/docs/src/oss/langgraph/*.mdx —— 官方最新文档
输出：
  index/course_index.json  —— 包含标题树、起止行号、摘要，支持按目录快速定位
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LESSONS_DIR = ROOT / "lessons"
DOCS_DIR = ROOT / "repos" / "docs" / "src" / "oss" / "langgraph"
INDEX_PATH = ROOT / "index" / "course_index.json"

HEADING_RE = re.compile(r"^(#{1,4})\s+(.+?)\s*$")
LESSON_SEC_RE = re.compile(r"^#\s*(?:---+|A\.|B\.|C\.|D\.|练习|\d+\.)\s*(.+?)\s*$")


def _clean_summary(lines: list[str], start: int, end: int) -> str:
    """提取某一段落前几行有效文本作为简短摘要。"""
    buf = []
    in_code = False
    for raw in lines[start:min(end, start + 18)]:
        s = raw.strip()
        if s.startswith("```"):
            in_code = not in_code
            continue
        if in_code or not s or s.startswith((":::", "<", "---", "import ", "from ")):
            continue
        s = re.sub(r"[`*#]", "", s)
        buf.append(s)
        if sum(len(x) for x in buf) >= 120:
            break
    text = " ".join(buf)
    return (text[:120] + "...") if len(text) > 120 else text


def index_mdx(path: Path) -> dict:
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    title, desc = path.stem, ""
    i = 0
    if lines and lines[0].strip() == "---":
        for j in range(1, min(20, len(lines))):
            if lines[j].strip() == "---":
                i = j + 1
                break
            if lines[j].startswith("title:"):
                title = lines[j].split(":", 1)[1].strip().strip('"\'')
            elif lines[j].startswith("description:"):
                desc = lines[j].split(":", 1)[1].strip().strip('"\'')

    # 收集标题并构建树
    flat = []
    in_code = False
    for idx in range(i, len(lines)):
        s = lines[idx].strip()
        if s.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        m = HEADING_RE.match(s)
        if m:
            level = len(m.group(1))
            heading = re.sub(r"<[^>]+>", "", m.group(2)).strip()
            flat.append({"level": level, "title": heading, "start_line": idx + 1, "children": []})

    for k, node in enumerate(flat):
        end_line = flat[k + 1]["start_line"] - 1 if k + 1 < len(flat) else len(lines)
        node["end_line"] = end_line
        node["summary"] = _clean_summary(lines, node["start_line"], end_line)

    # 转为嵌套树
    root_nodes: list[dict] = []
    stack: list[dict] = []
    for node in flat:
        while stack and stack[-1]["level"] >= node["level"]:
            stack.pop()
        if stack:
            stack[-1]["children"].append(node)
        else:
            root_nodes.append(node)
        stack.append(node)

    return {
        "doc_id": f"doc:{path.stem}",
        "kind": "official_doc",
        "title": title,
        "description": desc,
        "path": str(path.relative_to(ROOT)),
        "total_lines": len(lines),
        "tree": root_nodes,
    }


def index_lesson(path: Path) -> dict:
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    title = path.stem
    summary = ""
    if lines and lines[0].strip().startswith('"""'):
        doc_lines = []
        for l in lines[1:15]:
            if '"""' in l:
                break
            if l.strip() and not set(l.strip()) <= {"="}:
                doc_lines.append(l.strip())
        if doc_lines:
            title = doc_lines[0]
            summary = " ".join(doc_lines[1:4])

    sections = []
    for idx, line in enumerate(lines):
        s = line.strip()
        if s.startswith("# ---") or s.startswith("# =========="):
            continue
        if re.match(r"^#\s*(?:[A-D]\.|[1-9]\.|练习：?|----------)", s):
            clean = re.sub(r"^#\s*[-\s]*", "", s).strip("- ")
            if clean:
                sections.append({"level": 2, "title": clean, "start_line": idx + 1, "end_line": idx + 1, "children": []})

    for k, sec in enumerate(sections):
        sec["end_line"] = sections[k + 1]["start_line"] - 1 if k + 1 < len(sections) else len(lines)

    return {
        "doc_id": f"lesson:{path.stem[:2]}",
        "kind": "lesson",
        "title": title,
        "description": summary,
        "path": str(path.relative_to(ROOT)),
        "notebook_path": f"notebooks/{path.stem}.ipynb",
        "total_lines": len(lines),
        "tree": sections,
    }


def build() -> dict:
    docs = []
    for p in sorted(LESSONS_DIR.glob("[0-9][0-9]_*.py")):
        docs.append(index_lesson(p))
    if DOCS_DIR.exists():
        for p in sorted(DOCS_DIR.glob("*.mdx")):
            docs.append(index_mdx(p))

    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {"schema": "pageindex-tree-v1", "total_docs": len(docs), "docs": docs}
    INDEX_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


if __name__ == "__main__":
    data = build()
    lessons_cnt = sum(1 for d in data["docs"] if d["kind"] == "lesson")
    docs_cnt = sum(1 for d in data["docs"] if d["kind"] == "official_doc")
    print(f"✅ 已生成 {INDEX_PATH}（课程 {lessons_cnt} 篇 + 官方文档 {docs_cnt} 篇）")
