"""
第 4 课：从零手写一个 ReAct Agent（LLM + 工具 + 循环）
=================================================================
Agent = 一个带循环的图：
    START -> llm --(有 tool_calls?)--> tools -> llm -> ... -> END
                 \--(没有)----------------------------> END

* langgraph.prebuilt.ToolNode：执行 AIMessage 中的 tool_calls，返回 ToolMessage
* langgraph.prebuilt.tools_condition：有工具调用就去 "tools"，否则 END
* 生产中更常用 `langchain.agents.create_agent`（基于 LangGraph 构建），
  但亲手写一次能让你真正理解它在做什么。
"""
from langchain_core.messages import SystemMessage
from langchain_core.tools import tool

from langgraph.graph import START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from fake_llm import get_model


@tool
def get_weather(city: str) -> str:
    """查询城市天气。"""
    fake = {"北京": "晴 12°C", "上海": "小雨 16°C", "深圳": "多云 24°C", "旧金山": "雾 14°C"}
    return f"{city}：{fake.get(city, '未知')}"


@tool
def calculator(expression: str) -> str:
    """计算一个算术表达式。"""
    return str(eval(expression, {"__builtins__": {}}))  # 仅为教学，生产勿用 eval


tools = [get_weather, calculator]
model = get_model().bind_tools(tools)


def llm(state: MessagesState):
    msgs = [SystemMessage("你是一个乐于助人的助手。")] + state["messages"]
    return {"messages": [model.invoke(msgs)]}


builder = StateGraph(MessagesState)
builder.add_node("llm", llm)
builder.add_node("tools", ToolNode(tools))
builder.add_edge(START, "llm")
builder.add_conditional_edges("llm", tools_condition)  # -> "tools" 或 END
builder.add_edge("tools", "llm")
agent = builder.compile()


def show(result):
    for m in result["messages"]:
        extra = f" tool_calls={m.tool_calls}" if getattr(m, "tool_calls", None) else ""
        print(f"  {type(m).__name__:12s} | {m.content}{extra}")


if __name__ == "__main__":
    print(agent.get_graph().draw_mermaid())
    for q in ["上海今天天气怎么样？", "帮我算一下 12*7+3", "你好"]:
        print(f"\n>>> {q}")
        show(agent.invoke({"messages": [{"role": "user", "content": q}]}))

# 练习：
#  1. 新增一个工具 get_time(city)，并让假模型（fake_llm.py）识别 "几点"。
#  2. 用 stream_mode="updates" 观察每一步是哪个节点产生了什么消息。
#  3. 装上真模型（见 fake_llm.py 顶部说明），对比行为。
