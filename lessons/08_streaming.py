"""
第 8 课：流式输出 —— stream_mode、v2 统一格式、stream_events(v3)
=================================================================
LangGraph 有两层流式 API：
1) graph.stream(..., stream_mode=..., version="v2")   —— 原始事件
     values   : 每个超步后的完整 state
     updates  : 每个节点返回的增量
     messages : LLM 的 token（(chunk, metadata)）
     custom   : 节点里用 get_stream_writer() 推送的任意数据（进度条等）
     checkpoints / tasks / debug : 调试用
   version="v2" 让每个 chunk 都是 {"type", "ns", "data"}，格式统一（推荐）。
2) graph.stream_events(..., version="v3")  —— 新的"类型化投影"
     stream.messages / stream.values / stream.subgraphs / stream.output ...
"""
import warnings

from langgraph.config import get_stream_writer
from langgraph.graph import START, MessagesState, StateGraph

from fake_llm import get_model

# v3 目前是 experimental（beta）；需在 import langchain_core 之后设置过滤器
warnings.filterwarnings("ignore", message=".*v3 streaming protocol.*")

model = get_model()


def prepare(state: MessagesState):
    writer = get_stream_writer()
    for p in (30, 60, 100):
        writer({"progress": p, "msg": "正在检索资料..."})  # -> custom 流
    return {}


def answer(state: MessagesState):
    return {"messages": [model.invoke(state["messages"])]}


graph = (
    StateGraph(MessagesState)
    .add_node(prepare).add_node(answer)
    .add_edge(START, "prepare").add_edge("prepare", "answer")
    .compile()
)
inputs = {"messages": [{"role": "user", "content": "介绍一下 LangGraph"}]}

if __name__ == "__main__":
    print("== 1. stream_mode='updates'（v1 默认格式）==")
    for chunk in graph.stream(inputs, stream_mode="updates"):
        print("  ", {k: (type(v).__name__ if v else v) for k, v in chunk.items()})

    print("\n== 2. 多模式 + version='v2' ==")
    for part in graph.stream(inputs, stream_mode=["updates", "messages", "custom"], version="v2"):
        if part["type"] == "custom":
            print(f"   [custom] {part['data']}")
        elif part["type"] == "updates":
            print(f"   [updates] 节点 {list(part['data'])} 完成")
        elif part["type"] == "messages":
            chunk, meta = part["data"]
            print(chunk.content, end="|", flush=True)  # 用 | 分隔，看清逐 token
    print()

    print("\n== 3. stream_events(version='v3')：类型化投影 ==")
    stream = graph.stream_events(inputs, version="v3")
    for message in stream.messages:
        print(f"   来自节点 {message.node}: ", end="")
        for token in message.text:
            print(token, end="", flush=True)
        print()
    print("   最终 state 消息数:", len(stream.output["messages"]))

# 练习：
#  1. 用 stream_mode="values" 打印每个超步后的消息条数。
#  2. 结合第 6 课：stream_events 后检查 stream.interrupted / stream.interrupts。
#  3. 阅读 docs/src/oss/langgraph/event-streaming.mdx 的 "Build your own projection"。
