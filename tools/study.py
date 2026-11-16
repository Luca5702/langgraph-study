"""
LangGraph 学习助手 CLI：管理学习进度（progress.json / PROGRESS.md）+ 检索树状索引（course_index.json）。

常用命令：
  python tools/study.py status                   # 查看当前学习进度
  python tools/study.py start 01                 # 标记第 01 课为进行中
  python tools/study.py done 01 --note "理解了"   # 标记第 01 课已完成并记录笔记
  python tools/study.py note 01 "待复习：..."     # 给某课追加笔记/错题
  python tools/study.py search interrupt         # 在树状索引中搜索课程与官方文档
  python tools/study.py tree interrupts          # 查看某篇官方文档的树状目录（PageIndex 视图）
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX_PATH = ROOT / "index" / "course_index.json"
PROGRESS_PATH = ROOT / "progress.json"
PROGRESS_MD_PATH = ROOT / "PROGRESS.md"


def load_index() -> dict:
    if not INDEX_PATH.exists():
        from build_index import build
        return build()
    return json.loads(INDEX_PATH.read_text(encoding="utf-8"))


def init_progress(index_data: dict) -> dict:
    lessons = {}
    for d in index_data["docs"]:
        if d["kind"] == "lesson":
            num = d["doc_id"].split(":")[1]
            lessons[num] = {
                "title": d["title"],
                "notebook": d.get("notebook_path", ""),
                "status": "not_started",  # not_started | in_progress | completed
                "updated_at": None,
                "notes": [],
            }
    return {"current_lesson": "01", "lessons": lessons, "history": []}


def load_progress(index_data: dict) -> dict:
    if not PROGRESS_PATH.exists():
        data = init_progress(index_data)
        save_progress(data)
        return data
    return json.loads(PROGRESS_PATH.read_text(encoding="utf-8"))


def save_progress(data: dict) -> None:
    PROGRESS_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    # 同步生成易读的 PROGRESS.md
    icon = {"not_started": "⬜", "in_progress": "🟡", "completed": "✅"}
    done_cnt = sum(1 for v in data["lessons"].values() if v["status"] == "completed")
    total = len(data["lessons"])
    lines = [
        "# LangGraph 学习进度",
        "",
        f"- 总进度：**{done_cnt} / {total}** 课已完成",
        f"- 当前建议学习：**第 {data.get('current_lesson', '01')} 课**",
        "",
        "| 课号 | 状态 | 课程 | Notebook | 笔记数 |",
        "|---|---|---|---|---|",
    ]
    for num, info in sorted(data["lessons"].items()):
        nb = f"`{info['notebook']}`" if info.get("notebook") else "-"
        lines.append(f"| {num} | {icon[info['status']]} {info['status']} | {info['title']} | {nb} | {len(info['notes'])} |")
    notes_sec = ["", "## 📝 学习笔记与错题记录", ""]
    has_notes = False
    for num, info in sorted(data["lessons"].items()):
        if info["notes"]:
            has_notes = True
            notes_sec.append(f"### 第 {num} 课：{info['title']}")
            for n in info["notes"]:
                notes_sec.append(f"- [{n['time']}] {n['text']}")
            notes_sec.append("")
    if has_notes:
        lines.extend(notes_sec)
    PROGRESS_MD_PATH.write_text("\n".join(lines), encoding="utf-8")


def cmd_status(args):
    idx = load_index()
    prog = load_progress(idx)
    icon = {"not_started": "⬜", "in_progress": "🟡", "completed": "✅"}
    done = sum(1 for v in prog["lessons"].values() if v["status"] == "completed")
    print(f"== LangGraph 学习进度 ({done}/{len(prog['lessons'])}) | 当前推荐: 第 {prog['current_lesson']} 课 ==")
    for num, info in sorted(prog["lessons"].items()):
        note_hint = f" (笔记 {len(info['notes'])})" if info["notes"] else ""
        print(f"  {icon[info['status']]} {num} | {info['title']}{note_hint}")


def _norm(num: str) -> str:
    return num.zfill(2)


def cmd_update(args, new_status: str):
    idx = load_index()
    prog = load_progress(idx)
    num = _norm(args.lesson)
    if num not in prog["lessons"]:
        print(f"❌ 找不到第 {num} 课")
        return
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    prog["lessons"][num]["status"] = new_status
    prog["lessons"][num]["updated_at"] = now
    if getattr(args, "note", None):
        prog["lessons"][num]["notes"].append({"time": now, "text": args.note})
    if new_status == "in_progress":
        prog["current_lesson"] = num
    elif new_status == "completed":
        nxt = str(int(num) + 1).zfill(2)
        if nxt in prog["lessons"]:
            prog["current_lesson"] = nxt
    prog["history"].append({"time": now, "lesson": num, "action": new_status})
    save_progress(prog)
    print(f"✅ 第 {num} 课已标记为 {new_status}（下一推荐：第 {prog['current_lesson']} 课）")


def cmd_note(args):
    idx = load_index()
    prog = load_progress(idx)
    num = _norm(args.lesson)
    if num not in prog["lessons"]:
        print(f"❌ 找不到第 {num} 课")
        return
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    prog["lessons"][num]["notes"].append({"time": now, "text": args.text})
    save_progress(prog)
    print(f"📝 已记录到第 {num} 课笔记（共 {len(prog['lessons'][num]['notes'])} 条）")


def _walk_tree(nodes: list[dict], trail: list[str], q: str, hits: list[tuple]):
    for n in nodes:
        cur_trail = trail + [n["title"]]
        hay = (n["title"] + " " + n.get("summary", "")).lower()
        if q in hay:
            hits.append((" > ".join(cur_trail), n["start_line"], n["end_line"], n.get("summary", "")))
        if n.get("children"):
            _walk_tree(n["children"], cur_trail, q, hits)


def cmd_search(args):
    idx = load_index()
    q = args.query.lower()
    total = 0
    for d in idx["docs"]:
        hits = []
        if q in (d["title"] + " " + d.get("description", "")).lower():
            hits.append(("(文档标题)", 1, d["total_lines"], d.get("description", "")))
        _walk_tree(d["tree"], [], q, hits)
        if hits:
            print(f"\n📄 [{d['kind']}] {d['title']}  ({d['path']})")
            for path_str, s, e, summ in hits[:5]:
                total += 1
                print(f"   L{s}-{e}: {path_str}")
                if summ:
                    print(f"      {summ[:90]}")
    if total == 0:
        print(f"没有在目录树里找到 '{args.query}'")


def _print_tree(nodes: list[dict], indent: int = 0):
    for n in nodes:
        pad = "  " * indent
        print(f"{pad}- {n['title']}  (L{n['start_line']}-{n['end_line']})")
        if n.get("children"):
            _print_tree(n["children"], indent + 1)


def cmd_tree(args):
    idx = load_index()
    q = args.doc.lower()
    for d in idx["docs"]:
        if q in d["doc_id"].lower() or q in d["path"].lower() or q in d["title"].lower():
            print(f"🌲 {d['title']} ({d['path']}, {d['total_lines']} 行)")
            _print_tree(d["tree"])
            return
    print(f"❌ 找不到匹配 '{args.doc}' 的文档")


def main():
    p = argparse.ArgumentParser(description="LangGraph 学习助手")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")

    p_start = sub.add_parser("start")
    p_start.add_argument("lesson")

    p_done = sub.add_parser("done")
    p_done.add_argument("lesson")
    p_done.add_argument("--note", default=None)

    p_note = sub.add_parser("note")
    p_note.add_argument("lesson")
    p_note.add_argument("text")

    p_search = sub.add_parser("search")
    p_search.add_argument("query")

    p_tree = sub.add_parser("tree")
    p_tree.add_argument("doc")

    args = p.parse_args()
    if args.cmd == "status":
        cmd_status(args)
    elif args.cmd == "start":
        cmd_update(args, "in_progress")
    elif args.cmd == "done":
        cmd_update(args, "completed")
    elif args.cmd == "note":
        cmd_note(args)
    elif args.cmd == "search":
        cmd_search(args)
    elif args.cmd == "tree":
        cmd_tree(args)


if __name__ == "__main__":
    main()
