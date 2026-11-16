# LangGraph 学习工作区（基于 langgraph 1.2.22，2026-11）

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/Luca5702/langgraph-study/main?urlpath=%2Fdoc%2Ftree%2Fnotebooks%2F01_hello_graph.ipynb)
[![NBViewer](https://raw.githubusercontent.com/jupyter/design/master/logos/Badges/nbviewer_badge.svg)](https://nbviewer.org/github/Luca5702/langgraph-study/tree/main/notebooks/)

> **LangGraph = Agent 运行时（runtime）**：控制力最强、抽象最少。
> `LangChain(create_agent)` = Agent 框架，`Deep Agents` = Agent "harness"（开箱即用的长任务 agent），二者都构建在 LangGraph 之上。
> 所以先学 LangGraph，再看 deepagents 就会觉得非常清楚。

---

## 🌐 一键在线打开 Jupyter（无需本地安装）

| 课号 | 课程主题 | 📖 直接阅读 (GitHub / NBViewer) | 🚀 在线运行 (Google Colab) | 🧪 在线 JupyterLab (Binder) |
|---|---|---|---|---|
| 01 | Hello Graph（State / Node / Edge） | [01_hello_graph.ipynb](notebooks/01_hello_graph.ipynb) · [NBViewer](https://nbviewer.org/github/Luca5702/langgraph-study/blob/main/notebooks/01_hello_graph.ipynb) | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Luca5702/langgraph-study/blob/main/notebooks/01_hello_graph.ipynb) | [Binder](https://mybinder.org/v2/gh/Luca5702/langgraph-study/main?urlpath=%2Fdoc%2Ftree%2Fnotebooks%2F01_hello_graph.ipynb) |
| 02 | State 与 Reducer（合并规则 / Overwrite / Schema） | [02_state_reducers.ipynb](notebooks/02_state_reducers.ipynb) · [NBViewer](https://nbviewer.org/github/Luca5702/langgraph-study/blob/main/notebooks/02_state_reducers.ipynb) | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Luca5702/langgraph-study/blob/main/notebooks/02_state_reducers.ipynb) | [Binder](https://mybinder.org/v2/gh/Luca5702/langgraph-study/main?urlpath=%2Fdoc%2Ftree%2Fnotebooks%2F02_state_reducers.ipynb) |
| 03 | 控制流（条件边 / 循环 / 并行 / Send / Command） | [03_control_flow.ipynb](notebooks/03_control_flow.ipynb) · [NBViewer](https://nbviewer.org/github/Luca5702/langgraph-study/blob/main/notebooks/03_control_flow.ipynb) | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Luca5702/langgraph-study/blob/main/notebooks/03_control_flow.ipynb) | [Binder](https://mybinder.org/v2/gh/Luca5702/langgraph-study/main?urlpath=%2Fdoc%2Ftree%2Fnotebooks%2F03_control_flow.ipynb) |
| 04 | 手写 ReAct Agent（LLM + ToolNode + 循环） | [04_agent_tools.ipynb](notebooks/04_agent_tools.ipynb) · [NBViewer](https://nbviewer.org/github/Luca5702/langgraph-study/blob/main/notebooks/04_agent_tools.ipynb) | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Luca5702/langgraph-study/blob/main/notebooks/04_agent_tools.ipynb) | [Binder](https://mybinder.org/v2/gh/Luca5702/langgraph-study/main?urlpath=%2Fdoc%2Ftree%2Fnotebooks%2F04_agent_tools.ipynb) |
| 05 | 持久化与记忆（Checkpointer 短期 + Store 长期） | [05_persistence_memory.ipynb](notebooks/05_persistence_memory.ipynb) · [NBViewer](https://nbviewer.org/github/Luca5702/langgraph-study/blob/main/notebooks/05_persistence_memory.ipynb) | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Luca5702/langgraph-study/blob/main/notebooks/05_persistence_memory.ipynb) | [Binder](https://mybinder.org/v2/gh/Luca5702/langgraph-study/main?urlpath=%2Fdoc%2Ftree%2Fnotebooks%2F05_persistence_memory.ipynb) |
| 06 | Human-in-the-loop（`interrupt()` 与 `Command(resume=...)`） | [06_human_in_the_loop.ipynb](notebooks/06_human_in_the_loop.ipynb) · [NBViewer](https://nbviewer.org/github/Luca5702/langgraph-study/blob/main/notebooks/06_human_in_the_loop.ipynb) | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Luca5702/langgraph-study/blob/main/notebooks/06_human_in_the_loop.ipynb) | [Binder](https://mybinder.org/v2/gh/Luca5702/langgraph-study/main?urlpath=%2Fdoc%2Ftree%2Fnotebooks%2F06_human_in_the_loop.ipynb) |
| 07 | 时间旅行（Replay 重放与 Fork 分叉） | [07_time_travel.ipynb](notebooks/07_time_travel.ipynb) · [NBViewer](https://nbviewer.org/github/Luca5702/langgraph-study/blob/main/notebooks/07_time_travel.ipynb) | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Luca5702/langgraph-study/blob/main/notebooks/07_time_travel.ipynb) | [Binder](https://mybinder.org/v2/gh/Luca5702/langgraph-study/main?urlpath=%2Fdoc%2Ftree%2Fnotebooks%2F07_time_travel.ipynb) |
| 08 | 流式输出（`stream_mode` / v2 格式 / `stream_events` v3） | [08_streaming.ipynb](notebooks/08_streaming.ipynb) · [NBViewer](https://nbviewer.org/github/Luca5702/langgraph-study/blob/main/notebooks/08_streaming.ipynb) | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Luca5702/langgraph-study/blob/main/notebooks/08_streaming.ipynb) | [Binder](https://mybinder.org/v2/gh/Luca5702/langgraph-study/main?urlpath=%2Fdoc%2Ftree%2Fnotebooks%2F08_streaming.ipynb) |
| 09 | 子图（Subgraph）与多智能体 Handoff | [09_subgraphs.ipynb](notebooks/09_subgraphs.ipynb) · [NBViewer](https://nbviewer.org/github/Luca5702/langgraph-study/blob/main/notebooks/09_subgraphs.ipynb) | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Luca5702/langgraph-study/blob/main/notebooks/09_subgraphs.ipynb) | [Binder](https://mybinder.org/v2/gh/Luca5702/langgraph-study/main?urlpath=%2Fdoc%2Ftree%2Fnotebooks%2F09_subgraphs.ipynb) |
| 10 | Functional API（`@entrypoint` + `@task`） | [10_functional_api.ipynb](notebooks/10_functional_api.ipynb) · [NBViewer](https://nbviewer.org/github/Luca5702/langgraph-study/blob/main/notebooks/10_functional_api.ipynb) | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Luca5702/langgraph-study/blob/main/notebooks/10_functional_api.ipynb) | [Binder](https://mybinder.org/v2/gh/Luca5702/langgraph-study/main?urlpath=%2Fdoc%2Ftree%2Fnotebooks%2F10_functional_api.ipynb) |
| 11 | 生产特性（RetryPolicy / CachePolicy / Runtime / 容错） | [11_production.ipynb](notebooks/11_production.ipynb) · [NBViewer](https://nbviewer.org/github/Luca5702/langgraph-study/blob/main/notebooks/11_production.ipynb) | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Luca5702/langgraph-study/blob/main/notebooks/11_production.ipynb) | [Binder](https://mybinder.org/v2/gh/Luca5702/langgraph-study/main?urlpath=%2Fdoc%2Ftree%2Fnotebooks%2F11_production.ipynb) |

---

## 📁 目录说明

| 路径 | 内容 |
|---|---|
| `notebooks/` | **11 节已预执行的 Jupyter Notebook**（自带运行结果，打开即可阅读，也可在 Colab / Binder / 本地 IDE 逐格运行） |
| `lessons/` | **11 节纯 Python 脚本**（无需 API Key） + `fake_llm.py` 离线假模型 |
| `tools/study.py` | **学习进度管理 + PageIndex 风格树状目录检索 CLI** |
| `tools/build_index.py` | 生成无向量树状目录索引 `index/course_index.json`（含 11 节课程 + 36 篇官方文档标题树与行号） |
| `tools/build_notebooks.py` | 从 `lessons/*.py` 生成 `notebooks/*.ipynb` |
| `PROGRESS.md` / `progress.json` | 学习进度与错题/笔记记录 |
| `langgraph_lab.html` | 单文件互动实验室（概念地图、超步模拟器、Reducer 实验、12 题自测） |
| `run_all.sh` | 一键创建虚拟环境并运行全部 11 课 |

## 🛠️ 本地运行与进度管理

```bash
git clone https://github.com/Luca5702/langgraph-study.git
cd langgraph-study
./run_all.sh                                       # 自动建环境并跑通 11 课

# 学习进度与树状目录检索
.venv/bin/python tools/study.py status             # 查看当前进度
.venv/bin/python tools/study.py start 01           # 标记第 01 课进行中
.venv/bin/python tools/study.py done 01 --note "已掌握"
.venv/bin/python tools/study.py search interrupt   # 搜索课程与官方文档目录树
.venv/bin/python tools/study.py tree interrupts    # 查看单篇官方文档的目录树
```

## 🔑 LangGraph 1.x 新特性速记
- `graph.stream(..., version="v2")`：统一的 `{"type","ns","data"}` 流格式（1.1+）。
- `graph.stream_events(..., version="v3")`：类型化投影 `stream.messages / .values / .subgraphs / .output`（experimental）。
- `Overwrite(value)`：绕过 reducer 直接覆盖。
- `Runtime[Context]` + `context_schema`：取代旧的 `config["configurable"]` 传运行依赖。
- `durability="exit"|"async"|"sync"`、`CachePolicy`、`RetryPolicy`、`defer=True`。
- `create_react_agent` 已迁移到 `langchain.agents.create_agent`（middleware 体系）。
