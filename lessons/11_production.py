"""
第 11 课：生产级特性 —— 重试、缓存、运行时上下文、容错恢复
=================================================================
* RetryPolicy：节点抛异常时自动重试（指数退避）。
* CachePolicy + cache：相同输入的节点结果被缓存（可设 ttl）。
* Runtime[Context]：把"依赖"(模型名、DB 连接、用户 id) 注入节点，不污染 state。
* 容错：节点失败时，同一超步内已成功节点的结果会被保存（pending writes），
  修复后用 invoke(None, config) 从失败处继续，而不是从头再来。
* durability="exit" | "async" | "sync"：检查点写入时机（性能 vs 可靠性权衡）。
"""
import time
from dataclasses import dataclass

from typing_extensions import TypedDict

from langgraph.cache.memory import InMemoryCache
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import START, StateGraph
from langgraph.runtime import Runtime
from langgraph.types import CachePolicy, RetryPolicy


class State(TypedDict):
    x: int
    y: int
    z: str


# ---------- 重试 ----------
attempts = {"n": 0}


def flaky(state: State):
    attempts["n"] += 1
    if attempts["n"] < 3:
        raise ConnectionError(f"第 {attempts['n']} 次调用失败（模拟网络抖动）")
    return {"y": state["x"] * 2}


retry_graph = (
    StateGraph(State)
    .add_node("flaky", flaky, retry_policy=RetryPolicy(max_attempts=5, initial_interval=0.05))
    .add_edge(START, "flaky")
    .compile()
)


# ---------- 缓存 ----------
def slow_square(state: State):
    time.sleep(0.5)
    return {"y": state["x"] ** 2}


cache_graph = (
    StateGraph(State)
    .add_node("slow_square", slow_square, cache_policy=CachePolicy(ttl=60))
    .add_edge(START, "slow_square")
    .compile(cache=InMemoryCache())
)


# ---------- 运行时上下文 ----------
@dataclass
class Ctx:
    model_name: str
    user_id: str


def use_ctx(state: State, runtime: Runtime[Ctx]):
    return {"z": f"用 {runtime.context.model_name} 为 {runtime.context.user_id} 服务"}


ctx_graph = StateGraph(State, context_schema=Ctx).add_node(use_ctx).add_edge(START, "use_ctx").compile()


# ---------- 容错恢复 ----------
broken = {"on": True}


def step1(state: State):
    print("    step1 执行")
    return {"y": 1}


def step2(state: State):
    print("    step2 执行")
    if broken["on"]:
        raise RuntimeError("step2 崩了！")
    return {"z": "完成"}


ft_graph = (
    StateGraph(State)
    .add_node(step1).add_node(step2)
    .add_edge(START, "step1").add_edge("step1", "step2")
    .compile(checkpointer=InMemorySaver())
)

if __name__ == "__main__":
    print("1. 重试:", retry_graph.invoke({"x": 21}), f"共尝试 {attempts['n']} 次")

    for i in range(2):
        t = time.time()
        cache_graph.invoke({"x": 9})
        print(f"2. 缓存 第{i+1}次耗时 {time.time()-t:.2f}s")

    print("3. 上下文:", ctx_graph.invoke({"x": 0}, context=Ctx(model_name="gemini-2.5-flash", user_id="u42"))["z"])

    print("4. 容错恢复:")
    cfg = {"configurable": {"thread_id": "ft"}}
    try:
        ft_graph.invoke({"x": 0}, cfg, durability="sync")
    except RuntimeError as e:
        print("    出错:", e, "| next =", ft_graph.get_state(cfg).next)
    broken["on"] = False  # "修复 bug"
    print("    恢复 ->", ft_graph.invoke(None, cfg), "(注意 step1 没有重跑)")
