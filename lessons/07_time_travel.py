"""
第 7 课：时间旅行 —— Replay（重放）与 Fork（分叉）
=================================================================
因为每个超步都有检查点，你可以：
  * Replay：用历史上某个检查点的 config 调用 invoke(None, config)，
    该检查点之前的步骤不再执行，从那里继续往后跑。
  * Fork：用 update_state(历史config, 新值) 在历史点上创建一个"分支"检查点，
    再从这个分支继续运行 —— 原历史保持不变。
"""
from typing_extensions import TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import START, StateGraph


class State(TypedDict):
    topic: str
    draft: str
    final: str


def write(state: State):
    print(f"    [write] 主题 = {state['topic']}")
    return {"draft": f"一篇关于『{state['topic']}』的草稿"}


def polish(state: State):
    print("    [polish]")
    return {"final": state["draft"] + " ✨(已润色)"}


graph = (
    StateGraph(State)
    .add_node(write).add_node(polish)
    .add_edge(START, "write").add_edge("write", "polish")
    .compile(checkpointer=InMemorySaver())
)

if __name__ == "__main__":
    cfg = {"configurable": {"thread_id": "tt"}}
    print("== 原始运行 ==")
    print(graph.invoke({"topic": "猫"}, cfg)["final"])

    history = list(graph.get_state_history(cfg))
    for s in history:
        print(f"  step={s.metadata['step']:>2} next={s.next} values={s.values}")

    # 找到 "即将执行 write" 的检查点（write 之前）
    before_write = next(s for s in history if s.next == ("write",))

    print("\n== Replay：从 write 之前重放 ==")
    print(graph.invoke(None, before_write.config)["final"])

    print("\n== Fork：把 topic 改成 '狗'，从分支继续 ==")
    fork_cfg = graph.update_state(before_write.config, {"topic": "狗"})
    print(graph.invoke(None, fork_cfg)["final"])

    print("\n最新状态:", graph.get_state(cfg).values["final"])
    print("历史检查点总数:", len(list(graph.get_state_history(cfg))))

# 练习：
#  1. 找到 "即将执行 polish" 的检查点，fork 时把 draft 改掉，观察 write 是否会重跑。
#  2. update_state 有一个 as_node 参数，试着理解它的作用（决定"下一个节点"是谁）。
