"""
第 6 课：Human-in-the-loop —— interrupt() 与 Command(resume=...)
=================================================================
* 在节点内调用 interrupt(payload)：图暂停，payload 返回给调用方（result["__interrupt__"]）。
* 调用方用 graph.invoke(Command(resume=value), config) 恢复；
  恢复时该节点会"从头重新执行"，这一次 interrupt(...) 直接返回 value。
* 前提：必须有 checkpointer + thread_id。
* 规则（重要！）：
    1. 不要用 try/except 包住 interrupt（它靠抛异常实现暂停）
    2. 同一节点内多个 interrupt 的顺序不能变（按索引匹配 resume 值）
    3. interrupt 之前的副作用必须幂等（因为节点会重跑）
"""
from typing_extensions import Literal, TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt


class State(TypedDict):
    action: str
    status: str


def plan(state: State):
    print("  [plan] 计划执行:", state["action"])
    return {}


def human_review(state: State) -> Command[Literal["execute", "__end__"]]:
    print("  [human_review] 节点开始执行（恢复时会再次打印这行！）")
    decision = interrupt({"question": "是否批准该操作？", "action": state["action"]})
    # ↑ 第一次运行到这里暂停；恢复后 decision = resume 传入的值
    if decision.get("approved"):
        new_action = decision.get("edited_action", state["action"])
        return Command(goto="execute", update={"action": new_action})
    return Command(goto=END, update={"status": "❌ 被拒绝"})


def execute(state: State):
    return {"status": f"✅ 已执行：{state['action']}"}


graph = (
    StateGraph(State)
    .add_node(plan).add_node(human_review).add_node(execute)
    .add_edge(START, "plan").add_edge("plan", "human_review").add_edge("execute", END)
    .compile(checkpointer=InMemorySaver())
)

if __name__ == "__main__":
    cfg = {"configurable": {"thread_id": "review-1"}}
    print("== 第一次运行 ==")
    result = graph.invoke({"action": "删除生产数据库 users 表", "status": ""}, cfg)
    print("暂停！__interrupt__ =", result["__interrupt__"])
    print("当前 next =", graph.get_state(cfg).next)

    print("\n== 人类修改后批准 ==")
    result = graph.invoke(Command(resume={"approved": True, "edited_action": "备份 users 表"}), cfg)
    print("结果:", result)

    print("\n== 另一个线程：拒绝 ==")
    cfg2 = {"configurable": {"thread_id": "review-2"}}
    graph.invoke({"action": "给所有用户发垃圾邮件", "status": ""}, cfg2)
    print("结果:", graph.invoke(Command(resume={"approved": False}), cfg2))

# 练习：
#  1. 在一个节点里连续调用两次 interrupt（先问姓名再问年龄），观察需要 resume 几次。
#  2. 把 interrupt 放到工具函数内部（工具里也能用！），实现"调用敏感工具前需审批"。
#  3. 阅读 docs/src/oss/langgraph/interrupts.mdx 中 "Rules of interrupts"。
