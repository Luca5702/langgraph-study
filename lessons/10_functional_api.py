"""
第 10 课：Functional API —— @entrypoint + @task（不画图也能享受持久化/中断）
=================================================================
* @task：一个可被检查点记录的工作单元，调用返回 future，.result() 取值；可并行。
* @entrypoint(checkpointer=...)：工作流入口，用普通 Python 控制流（if/for/while）。
* 同样支持 interrupt()、Command(resume=...)、流式、previous（上一轮返回值）。
* 何时用：已有命令式代码想加上持久化/HITL；何时用 Graph API：需要可视化、复杂分支、并行状态合并。
"""
import time

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.func import entrypoint, task
from langgraph.types import Command, interrupt


@task
def write_section(topic: str) -> str:
    time.sleep(0.3)  # 模拟耗时（并行时总耗时 ≈ 0.3s 而非 0.9s）
    return f"《{topic}》章节内容"


@task
def combine(sections: list[str]) -> str:
    return "\n".join(sections)


@entrypoint(checkpointer=InMemorySaver())
def report_workflow(topics: list[str]) -> dict:
    t0 = time.time()
    futures = [write_section(t) for t in topics]  # 并行启动
    sections = [f.result() for f in futures]
    draft = combine(sections).result()
    elapsed = time.time() - t0
    # 💡 恢复(resume)时整个 entrypoint 会从头重跑，但已完成的 @task 结果直接从检查点读取，
    #    不会再执行 —— 所以恢复后打印的 parallel_seconds ≈ 0。这正是 @task 的意义：
    #    把有副作用/耗时的操作包进 task，保证重放时不重复执行。

    feedback = interrupt({"draft": draft, "ask": "满意吗？输入修改意见或 'ok'"})
    if feedback != "ok":
        draft += f"\n（已根据意见修改：{feedback}）"
    return {"report": draft, "parallel_seconds": round(elapsed, 2)}


@entrypoint(checkpointer=InMemorySaver())
def counter(n: int, *, previous: int | None = None) -> int:
    # previous = 同一线程上一次的返回值 —— 函数式的"短期记忆"
    return (previous or 0) + n


if __name__ == "__main__":
    cfg = {"configurable": {"thread_id": "f1"}}
    for chunk in report_workflow.stream(["状态", "节点", "边"], cfg, stream_mode="updates"):
        print("  ", chunk)
    print("\n恢复：")
    print(report_workflow.invoke(Command(resume="多加一些例子"), cfg))

    c = {"configurable": {"thread_id": "c"}}
    print("\ncounter:", [counter.invoke(5, c) for _ in range(3)])

# 练习：把第 4 课的 ReAct agent 用 Functional API 重写（参考 docs/src/oss/langgraph/functional-api.mdx）。
