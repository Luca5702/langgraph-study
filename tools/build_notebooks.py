"""
把 lessons/01_*.py ~ 11_*.py 转换成结构清晰、可直接逐格运行的 Jupyter Notebook（notebooks/*.ipynb）。
特点：
  * 顶部自动把 lessons/ 加入 sys.path，所以 `from fake_llm import get_model` 在 Notebook 里也能直接跑。
  * 文档字符串 -> Markdown 讲解格。
  * 按 `# ---` 分段拆成多个可独立运行的 Code Cell。
  * 文末 `# 练习：` -> Markdown 练习格。
  * 绑定 kernelspec: langgraph-study（Python (LangGraph Study)）。
"""
from __future__ import annotations

import re
import textwrap
from pathlib import Path

import nbformat as nbf

ROOT = Path(__file__).resolve().parent.parent
LESSONS_DIR = ROOT / "lessons"
NB_DIR = ROOT / "notebooks"


def parse_lesson(path: Path) -> nbf.NotebookNode:
    text = path.read_text(encoding="utf-8")
    nb = nbf.v4.new_notebook()
    nb.metadata["kernelspec"] = {
        "display_name": "Python (LangGraph Study)",
        "language": "python",
        "name": "langgraph-study",
    }

    # 1) 提取顶部 docstring
    m = re.match(r'^"""\n(.*?)\n"""\n(.*)$', text, re.S)
    if m:
        doc, body = m.group(1), m.group(2)
    else:
        doc, body = path.stem, text

    doc_lines = doc.splitlines()
    title = doc_lines[0].strip()
    rest_lines = []
    for l in doc_lines[1:]:
        if set(l.strip()) <= {"="}:
            continue
        # 把 2/4 空格缩进的 * / - 列表转成标准 Markdown 列表
        s = re.sub(r"^\s{2,}([*•-])\s+", "- ", l)
        s = re.sub(r"^\s{4,}", "  ", s)
        rest_lines.append(s)
    rest_doc = "\n".join(rest_lines).strip()
    md_intro = f"# {title}\n\n{rest_doc}" if rest_doc else f"# {title}"
    nb.cells.append(nbf.v4.new_markdown_cell(md_intro))

    # 2) 提取末尾练习注释
    ex_match = re.search(r"\n(# 练习：.*)\Z", body, re.S)
    exercises = ""
    if ex_match:
        exercises = "\n".join(re.sub(r"^#\s?", "", l) for l in ex_match.group(1).splitlines())
        body = body[:ex_match.start()].rstrip() + "\n"

    # 2.5) Colab / Binder 自举：如果环境没有 langgraph，自动安装（第 01 课或用到 fake_llm 的课）
    if path.stem.startswith("01_") or "fake_llm" in body:
        colab_boot = (
            "# 💡 在 Google Colab / Binder 中首次运行时自动安装依赖（本地已有环境会直接跳过）\n"
            "import importlib.util, subprocess, sys\n"
            "if importlib.util.find_spec('langgraph') is None:\n"
            "    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-q', 'langgraph', 'langchain-core', 'langgraph-checkpoint-sqlite'])\n"
        )
        if "fake_llm" in body:
            colab_boot += (
                "from pathlib import Path\n"
                "import urllib.request\n"
                "for p in [Path('lessons'), Path.cwd().parent / 'lessons']:\n"
                "    if p.exists():\n"
                "        sys.path.insert(0, str(p.resolve()))\n"
                "        break\n"
                "else:\n"
                "    if not Path('fake_llm.py').exists():\n"
                "        urllib.request.urlretrieve('https://raw.githubusercontent.com/Luca5702/langgraph-study/main/lessons/fake_llm.py', 'fake_llm.py')\n"
            )
        nb.cells.append(nbf.v4.new_code_cell(colab_boot))

    # 4) 拆开主代码与 if __name__ == "__main__":
    main_split = re.split(r'\nif __name__ == ["\']__main__["\']:\n', body, maxsplit=1)
    def_part = main_split[0].strip()
    run_part = textwrap.dedent(main_split[1]).strip() if len(main_split) > 1 else ""

    # 按 # --- 分隔段拆成小格，方便逐段运行
    chunks = re.split(r"\n# -+\n", def_part)
    for c in chunks:
        c = c.strip()
        if c:
            nb.cells.append(nbf.v4.new_code_cell(c))

    if run_part:
        nb.cells.append(nbf.v4.new_markdown_cell("## 运行实验"))
        nb.cells.append(nbf.v4.new_code_cell(run_part))

    if exercises:
        nb.cells.append(nbf.v4.new_markdown_cell(f"## ✏️ {exercises}"))

    return nb


def build_all():
    NB_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(LESSONS_DIR.glob("[0-9][0-9]_*.py"))
    for p in files:
        nb = parse_lesson(p)
        out = NB_DIR / f"{p.stem}.ipynb"
        nbf.write(nb, out)
    print(f"✅ 已生成 {len(files)} 个 Notebook 到 {NB_DIR}")


if __name__ == "__main__":
    build_all()
