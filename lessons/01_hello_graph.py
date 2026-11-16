"""
第 1 课：Hello Graph —— LangGraph 的三要素：State / Node / Edge
=================================================================
核心心智模型：
  * State（状态）：一个共享的"黑板"，通常是 TypedDict。
  * Node（节点）：普通 Python 函数，输入当前 state，返回 "要更新的部分 state"（dict）。
  * Edge（边）：决定下一个运行哪个节点。START / END 是两个特殊的虚拟节点。
  * builder.compile() 之后得到一个 CompiledStateGraph（本质是一个 Pregel 运行时），
    它实现了 Runnable 接口：invoke / stream / batch / ainvoke ...

运行：  python lessons/01_hello_graph.py
"""
from typing_extensions import TypedDict

from langgraph.graph import END, START, StateGraph


# 1) 定义状态
class State(TypedDict):
    name: str
    greeting: str
    shout: str


# 2) 定义节点：只返回"要改的键"，没返回的键保持不变
def greet(state: State) -> dict:
    print(f"  [greet] 收到 state = {state}")
    return {"greeting": f"你好, {state['name']}!"}


def shout(state: State) -> dict:
    print(f"  [shout] 收到 state = {state}")
    return {"shout": state["greeting"].upper() + " !!!"}


# 3) 构建图
builder = StateGraph(State)
builder.add_node("greet", greet)
builder.add_node("shout", shout)
builder.add_edge(START, "greet")
builder.add_edge("greet", "shout")
builder.add_edge("shout", END)

graph = builder.compile()

if __name__ == "__main__":
    print("== 图结构（Mermaid，可粘贴到 https://mermaid.live 查看）==")
    print(graph.get_graph().draw_mermaid())

    print("== invoke ==")
    result = graph.invoke({"name": "LangGraph"})
    print("最终 state:", result)

    # 也可以用链式写法（1.x 中 add_node/add_edge 返回 builder 本身）
    graph2 = (
        StateGraph(State)
        .add_node(greet)  # 不写名字时，默认用函数名作为节点名
        .add_node(shout)
        .add_edge(START, "greet")
        .add_edge("greet", "shout")
        .compile()  # 没有出边的节点会自动结束
    )
    print("链式写法结果:", graph2.invoke({"name": "World"})["shout"])

# 练习：
#  1. 新增一个节点 count，计算 greeting 的字符数，放在 greet 和 shout 之间。
#  2. 如果节点返回了一个 State 中不存在的键，会发生什么？试试看。
