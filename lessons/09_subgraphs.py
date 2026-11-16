"""
第 9 课：子图（Subgraph）与多智能体的基础
=================================================================
两种用法：
  A. 共享状态键：把编译好的子图直接 add_node(subgraph)，父子通过同名键通信。
  B. 不同 schema：在一个普通节点函数里调用 subgraph.invoke()，自己做输入/输出转换。
多智能体（supervisor / handoff）本质上就是：每个 agent 是一个子图，
用 Command(goto=..., graph=Command.PARENT) 在父图中跳转。
"""
import operator

from typing_extensions import Annotated, TypedDict

from langgraph.graph import START, StateGraph
from langgraph.types import Command


# ---------- A. 共享键 ----------
class Shared(TypedDict):
    log: Annotated[list[str], operator.add]


sub_a = (
    StateGraph(Shared)
    .add_node("sub_step1", lambda s: {"log": ["  子图 step1"]})
    .add_node("sub_step2", lambda s: {"log": ["  子图 step2"]})
    .add_edge(START, "sub_step1").add_edge("sub_step1", "sub_step2")
    .compile()
)
parent_a = (
    StateGraph(Shared)
    .add_node("before", lambda s: {"log": ["父图 before"]})
    .add_node("child", sub_a)  # 子图直接作为节点
    .add_node("after", lambda s: {"log": ["父图 after"]})
    .add_edge(START, "before").add_edge("before", "child").add_edge("child", "after")
    .compile()
)
# ⚠️ 坑：运行后你会看到 "父图 before" 出现了两次！
#   原因：子图收到父图的 log=['父图 before']，执行完后把"完整的" log 作为输出返回给父图，
#   父图的 reducer(operator.add) 又把它拼接了一次。
#   修复思路：用函数包一层，只把"子图新增的部分"交还给父图（或改用去重 reducer / 不同的键）。


def child_wrapper(state: Shared):
    out = sub_a.invoke(state)
    return {"log": out["log"][len(state["log"]):]}  # 只返回新增项


parent_a_fixed = (
    StateGraph(Shared)
    .add_node("before", lambda s: {"log": ["父图 before"]})
    .add_node("child", child_wrapper)
    .add_node("after", lambda s: {"log": ["父图 after"]})
    .add_edge(START, "before").add_edge("before", "child").add_edge("child", "after")
    .compile()
)


# ---------- B. 不同 schema ----------
class SubState(TypedDict):
    text: str
    words: int


sub_b = StateGraph(SubState).add_node("count", lambda s: {"words": len(s["text"].split())}).add_edge(START, "count").compile()


class ParentState(TypedDict):
    doc: str
    stats: str


def call_sub(state: ParentState):
    out = sub_b.invoke({"text": state["doc"]})  # 手动转换输入
    return {"stats": f"共 {out['words']} 个词"}  # 手动转换输出


parent_b = StateGraph(ParentState).add_node(call_sub).add_edge(START, "call_sub").compile()


# ---------- C. 从子图跳回父图的另一个节点（handoff） ----------
class HState(TypedDict):
    path: Annotated[list[str], operator.add]


def agent_a_work(state: HState):
    # 子图内部决定：交给父图中的 agent_b
    return Command(update={"path": ["agent_a 处理完，handoff→agent_b"]}, goto="agent_b", graph=Command.PARENT)


agent_a = StateGraph(HState).add_node(agent_a_work).add_edge(START, "agent_a_work").compile()
multi = (
    StateGraph(HState)
    .add_node("agent_a", agent_a, destinations=("agent_b",))
    .add_node("agent_b", lambda s: {"path": ["agent_b 完成"]})
    .add_edge(START, "agent_a")
    .compile()
)

if __name__ == "__main__":
    print("A.", *parent_a.invoke({"log": []})["log"], sep="\n   ")
    print("A(修复版).", *parent_a_fixed.invoke({"log": []})["log"], sep="\n   ")
    print("   带 subgraphs=True 的流：")
    for ns, upd in parent_a.stream({"log": []}, stream_mode="updates", subgraphs=True):
        print("    ns=", ns, upd)
    print("B.", parent_b.invoke({"doc": "LangGraph makes agents durable and controllable"}))
    print("C.", multi.invoke({"path": []})["path"])
    print(parent_a.get_graph(xray=True).draw_mermaid())

# 练习：
#  1. 给 parent_a 加 checkpointer，调用 get_state(cfg, subgraphs=True) 看子图状态。
#  2. 阅读 repos/langgraph-101/notebooks 中的 multi-agent 示例。
