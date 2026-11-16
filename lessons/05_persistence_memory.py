"""
第 5 课：持久化与记忆 —— Checkpointer（短期/线程记忆）+ Store（长期/跨线程记忆）
=================================================================
* Checkpointer：每个超步结束都保存一个 StateSnapshot（检查点）。
    - 用 config={"configurable": {"thread_id": "..."}} 区分会话（线程）。
    - 带来：多轮对话记忆、人机协同(interrupt)、时间旅行、容错恢复。
    - 实现：InMemorySaver（开发）、SqliteSaver、PostgresSaver（生产）...
* Store：跨线程共享的 key-value（可选语义搜索）存储，按 namespace 组织。
    - 典型用途：用户画像/偏好等"长期记忆"。
    - 节点里通过 runtime.store 访问。
"""
import sqlite3
from dataclasses import dataclass

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.runtime import Runtime
from langgraph.store.memory import InMemoryStore


# ---------------------------------------------------------------------------
# A. 短期记忆：一个会"记得"之前说过什么的聊天机器人
# ---------------------------------------------------------------------------
def chatbot(state: MessagesState):
    humans = [m.content for m in state["messages"] if m.type == "human"]
    return {"messages": [{"role": "ai", "content": f"这是你在本线程的第 {len(humans)} 句话，历史：{humans}"}]}


builder = StateGraph(MessagesState).add_node(chatbot).add_edge(START, "chatbot")
memory_graph = builder.compile(checkpointer=InMemorySaver())


# ---------------------------------------------------------------------------
# B. 长期记忆：Store + Runtime context（用户 id 通过 context 传入，不放进 state）
# ---------------------------------------------------------------------------
@dataclass
class Ctx:
    user_id: str


def remember(state: MessagesState, runtime: Runtime[Ctx]):
    ns = ("users", runtime.context.user_id, "prefs")
    text = state["messages"][-1].content
    if text.startswith("我喜欢"):
        runtime.store.put(ns, key=text, value={"pref": text[3:]})
    prefs = [item.value["pref"] for item in runtime.store.search(ns)]
    return {"messages": [{"role": "ai", "content": f"我记得你喜欢：{prefs}"}]}


store = InMemoryStore()
ltm_graph = (
    StateGraph(MessagesState, context_schema=Ctx)
    .add_node(remember).add_edge(START, "remember")
    .compile(checkpointer=InMemorySaver(), store=store)
)


if __name__ == "__main__":
    t1 = {"configurable": {"thread_id": "t1"}}
    t2 = {"configurable": {"thread_id": "t2"}}
    for text in ["你好", "我叫小明", "我刚才说了什么？"]:
        out = memory_graph.invoke({"messages": [{"role": "user", "content": text}]}, t1)
        print("A[t1]", out["messages"][-1].content)
    out = memory_graph.invoke({"messages": [{"role": "user", "content": "新会话"}]}, t2)
    print("A[t2]", out["messages"][-1].content, " <- 不同 thread_id，记忆隔离")

    snap = memory_graph.get_state(t1)
    print("\nget_state: 消息数 =", len(snap.values["messages"]), "| next =", snap.next,
          "| checkpoint_id =", snap.config["configurable"]["checkpoint_id"][:8], "...")
    print("get_state_history（最新在前）:")
    for s in memory_graph.get_state_history(t1):
        print(f"   step={s.metadata['step']:>2} source={s.metadata['source']:<6} next={s.next} msgs={len(s.values.get('messages', []))}")

    print("\nB. 长期记忆（跨线程）")
    ltm_graph.invoke({"messages": [{"role": "user", "content": "我喜欢咖啡"}]},
                     {"configurable": {"thread_id": "a"}}, context={"user_id": "u1"})
    out = ltm_graph.invoke({"messages": [{"role": "user", "content": "我喜欢爬山"}]},
                           {"configurable": {"thread_id": "b"}}, context={"user_id": "u1"})
    print("  u1 / 线程 b:", out["messages"][-1].content)
    out = ltm_graph.invoke({"messages": [{"role": "user", "content": "你好"}]},
                           {"configurable": {"thread_id": "c"}}, context={"user_id": "u2"})
    print("  u2 / 线程 c:", out["messages"][-1].content, " <- 不同用户，namespace 隔离")

    print("\nC. SqliteSaver：进程重启后记忆仍在（文件 memory.sqlite）")
    conn = sqlite3.connect("memory.sqlite", check_same_thread=False)
    sql_graph = builder.compile(checkpointer=SqliteSaver(conn))
    out = sql_graph.invoke({"messages": [{"role": "user", "content": "持久化测试"}]}, {"configurable": {"thread_id": "disk"}})
    print("  ", out["messages"][-1].content, "  <- 多运行几次本脚本，计数会增长")

# 练习：
#  1. 用 graph.update_state(config, {...}) 手动往某个线程里塞一条消息。
#  2. 消息越来越多怎么办？阅读 docs/src/oss/langgraph/add-memory.mdx 中 "trim / summarize" 部分。
