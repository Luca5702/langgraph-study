"""
第 2 课：State 与 Reducer —— "节点返回的更新如何合并进状态"
=================================================================
* 默认行为：后写覆盖前写（last-write-wins）。
* Annotated[类型, reducer]：指定合并函数 reducer(旧值, 新值) -> 合并后的值。
  - operator.add：列表拼接
  - add_messages：消息专用，按 id 追加/替换/删除（RemoveMessage）
* Overwrite(value)：本次更新绕过 reducer，直接替换。
* input_schema / output_schema：控制图对外的输入、输出键；
  节点内部还可以有"私有"状态。
"""
import operator

from langchain_core.messages import AIMessage, HumanMessage, RemoveMessage
from typing_extensions import Annotated, TypedDict

from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.graph.message import add_messages
from langgraph.types import Overwrite


# ---------------------------------------------------------------------------
# A. 默认覆盖 vs operator.add
# ---------------------------------------------------------------------------
class LogState(TypedDict):
    last: str                              # 没有 reducer -> 覆盖
    history: Annotated[list[str], operator.add]  # 有 reducer -> 追加


def step_a(state: LogState):
    return {"last": "a", "history": ["a"]}


def step_b(state: LogState):
    return {"last": "b", "history": ["b"]}


def reset(state: LogState):
    # 绕过 reducer，直接清空并替换
    return {"history": Overwrite(["<reset>"])}


g = (
    StateGraph(LogState)
    .add_node(step_a).add_node(step_b).add_node(reset)
    .add_edge(START, "step_a").add_edge("step_a", "step_b").add_edge("step_b", "reset")
    .compile()
)


# ---------------------------------------------------------------------------
# B. 自定义 reducer
# ---------------------------------------------------------------------------
def keep_max(old: int, new: int) -> int:
    return max(old, new)


class MaxState(TypedDict):
    best: Annotated[int, keep_max]


g_max = (
    StateGraph(MaxState)
    .add_node("n1", lambda s: {"best": 3})
    .add_node("n2", lambda s: {"best": 1})
    .add_edge(START, "n1").add_edge("n1", "n2")
    .compile()
)


# ---------------------------------------------------------------------------
# C. 消息状态：add_messages / MessagesState
# ---------------------------------------------------------------------------
class ChatState(TypedDict):
    messages: Annotated[list, add_messages]  # 等价于直接继承 MessagesState


def bot(state: ChatState):
    last = state["messages"][-1]
    return {"messages": [AIMessage(content=f"你说的是：{last.content}", id="ai-1")]}


def edit_bot(state: ChatState):
    # 同 id 的消息会被"替换"而不是追加
    return {"messages": [AIMessage(content="(已修订) 我理解了你的意思", id="ai-1")]}


def drop_first(state: ChatState):
    # RemoveMessage 按 id 删除消息
    return {"messages": [RemoveMessage(id=state["messages"][0].id)]}


g_chat = (
    StateGraph(ChatState)
    .add_node(bot).add_node(edit_bot).add_node(drop_first)
    .add_edge(START, "bot").add_edge("bot", "edit_bot").add_edge("edit_bot", "drop_first")
    .compile()
)


# ---------------------------------------------------------------------------
# D. 输入 / 输出 / 私有 schema
# ---------------------------------------------------------------------------
class InputState(TypedDict):
    question: str


class OutputState(TypedDict):
    answer: str


class OverallState(InputState, OutputState):
    pass


class PrivateState(TypedDict):
    scratch: str  # 只在节点间传递，不出现在输出中


def think(state: InputState) -> PrivateState:
    return {"scratch": f"思考『{state['question']}』..."}


def answer(state: PrivateState) -> OutputState:
    return {"answer": state["scratch"] + " 答案是 42"}


g_schema = (
    StateGraph(OverallState, input_schema=InputState, output_schema=OutputState)
    .add_node(think).add_node(answer)
    .add_edge(START, "think").add_edge("think", "answer")
    .compile()
)

if __name__ == "__main__":
    print("A.", g.invoke({"last": "", "history": ["init"]}))
    print("B.", g_max.invoke({"best": 0}))
    out = g_chat.invoke({"messages": [HumanMessage("你好", id="h-1")]})
    print("C.", [(type(m).__name__, m.content) for m in out["messages"]])
    print("D.", g_schema.invoke({"question": "生命的意义"}), "(注意 scratch 不在输出里)")
    print("MessagesState 的字段:", MessagesState.__annotations__)

# 练习：
#  1. 写一个 reducer，把 dict 做深度合并（merge）。
#  2. 两个并行节点同时写同一个"没有 reducer"的键，会报什么错？（提示：InvalidUpdateError，第 3 课验证）
