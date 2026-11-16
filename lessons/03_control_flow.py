"""
第 3 课：控制流 —— 条件边、循环、并行、Send(map-reduce)、Command
=================================================================
LangGraph 的执行模型来自 Google Pregel / BSP：
  * 按 "super-step（超步）" 推进。每个超步里，所有被触发的节点"并行"执行；
  * 超步结束时，所有更新通过 reducer 合并进 state，然后决定下一批节点；
  * 没有节点被触发时，图结束。
"""
import operator

from typing_extensions import Annotated, Literal, TypedDict

from langgraph.errors import GraphRecursionError, InvalidUpdateError
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, Send


# ---------------------------------------------------------------------------
# A. 条件边 + 循环：猜数字
# ---------------------------------------------------------------------------
class GuessState(TypedDict):
    target: int
    low: int
    high: int
    guess: int
    tries: Annotated[list[int], operator.add]


def make_guess(state: GuessState):
    g = (state["low"] + state["high"]) // 2
    return {"guess": g, "tries": [g]}


def adjust(state: GuessState):
    if state["guess"] < state["target"]:
        return {"low": state["guess"] + 1}
    return {"high": state["guess"] - 1}


def route(state: GuessState) -> Literal["adjust", "__end__"]:
    # 路由函数返回 "下一个节点名"（或节点名列表 / Send 列表）
    return END if state["guess"] == state["target"] else "adjust"


guess_graph = (
    StateGraph(GuessState)
    .add_node(make_guess).add_node(adjust)
    .add_edge(START, "make_guess")
    .add_conditional_edges("make_guess", route)
    .add_edge("adjust", "make_guess")  # 形成循环
    .compile()
)


# ---------------------------------------------------------------------------
# B. 静态并行（fan-out / fan-in）
# ---------------------------------------------------------------------------
class ParState(TypedDict):
    results: Annotated[list[str], operator.add]  # 并行写同一键 -> 必须有 reducer


def mk(name):
    def node(state):
        return {"results": [name]}
    return node


par_graph = (
    StateGraph(ParState)
    .add_node("a", mk("a")).add_node("b", mk("b")).add_node("c", mk("c")).add_node("join", mk("join"))
    .add_edge(START, "a")
    .add_edge("a", "b").add_edge("a", "c")       # b 和 c 在同一个超步并行
    .add_edge(["b", "c"], "join")                 # 等 b、c 都完成才执行 join
    .compile()
)


class BadState(TypedDict):
    results: list[str]  # 没有 reducer


bad_graph = (
    StateGraph(BadState)
    .add_node("b", lambda s: {"results": ["b"]}).add_node("c", lambda s: {"results": ["c"]})
    .add_edge(START, "b").add_edge(START, "c")
    .compile()
)


# ---------------------------------------------------------------------------
# C. Send：动态 map-reduce（运行时才知道要分几份）
# ---------------------------------------------------------------------------
class MapState(TypedDict):
    topics: list[str]
    jokes: Annotated[list[str], operator.add]


class JokeInput(TypedDict):
    topic: str


def fan_out(state: MapState):
    # 返回 Send 列表：每个 Send 用"自定义的输入"调用一次目标节点
    return [Send("write_joke", {"topic": t}) for t in state["topics"]]


def write_joke(state: JokeInput):
    return {"jokes": [f"关于{state['topic']}的笑话 🤡"]}


map_graph = (
    StateGraph(MapState)
    .add_node(write_joke)
    .add_conditional_edges(START, fan_out, ["write_joke"])
    .compile()
)


# ---------------------------------------------------------------------------
# D. Command：在节点里"同时"更新状态 + 决定跳转（无需写条件边）
# ---------------------------------------------------------------------------
class TicketState(TypedDict):
    text: str
    handled_by: str


def triage(state: TicketState) -> Command[Literal["billing", "tech"]]:
    dest = "billing" if "退款" in state["text"] else "tech"
    return Command(update={"handled_by": f"triage->{dest}"}, goto=dest)


def billing(state: TicketState):
    return {"handled_by": state["handled_by"] + " ✅billing"}


def tech(state: TicketState):
    return {"handled_by": state["handled_by"] + " ✅tech"}


cmd_graph = (
    StateGraph(TicketState)
    .add_node(triage).add_node(billing).add_node(tech)
    .add_edge(START, "triage")
    .compile()
)


if __name__ == "__main__":
    out = guess_graph.invoke({"target": 73, "low": 0, "high": 100, "tries": []})
    print("A. 猜数字过程:", out["tries"])

    try:
        guess_graph.invoke({"target": 73, "low": 0, "high": 100, "tries": []}, {"recursion_limit": 4})
    except GraphRecursionError as e:
        print("A'. recursion_limit=4 触发:", type(e).__name__)

    print("B. 并行:", par_graph.invoke({"results": []})["results"])
    for step in par_graph.stream({"results": []}, stream_mode="updates"):
        print("   超步更新:", step)
    try:
        bad_graph.invoke({"results": []})
    except InvalidUpdateError as e:
        print("B'. 无 reducer 并行写入报错:", type(e).__name__)

    print("C. Send:", map_graph.invoke({"topics": ["猫", "程序员", "咖啡"], "jokes": []})["jokes"])
    print("D. Command:", cmd_graph.invoke({"text": "我要退款", "handled_by": ""}))
    print(cmd_graph.get_graph().draw_mermaid())

# 练习：
#  1. 给 B 加一个 "d" 节点，路径 a->b->d->join 与 a->c->join，join 会执行几次？
#     （试试 add_node("join", ..., defer=True) 的效果）
#  2. 用 Send 实现：把一段长文本切块 -> 并行统计字数 -> 汇总。
