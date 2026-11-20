# -*- coding: utf-8 -*-
"""把 DAGScheduler 接到“多智能体执行”上的最小可运行样例

五个假智能体（用 sleep 模拟 7B 推理/工具耗时），一个 9 节点 DAG，跑三种调度策略对比。
不依赖 AIOS 内核，也不发网络请求——目的只是验证“调度器能真的把 DAG 跑起来并提速”。

运行：python src/demo_scheduler.py
"""
from __future__ import annotations

import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from scheduler import DAGScheduler, Task  # noqa: E402

# ---------------------------------------------------------------- 假智能体

def planner(task: Task):
    time.sleep(0.9)
    return f"plan<{task.payload.get('goal', 'demo')}>"


def coder(task: Task):
    time.sleep(1.2 if task.payload.get("module") == "backend" else 1.0)
    return f"code<{task.payload.get('module')}>"


def tester(task: Task):
    time.sleep(0.8 if "unit" in task.tid else 0.9)
    return f"test<{task.tid}>"


def reviewer(task: Task):
    time.sleep(0.7)
    return {"result": "pass", "issues": []}


def writer(task: Task):
    time.sleep(0.3)
    return f"doc<{task.tid}>"


AGENTS = {"planner": planner, "coder": coder, "tester": tester, "reviewer": reviewer, "writer": writer}


def build_tasks() -> list[Task]:
    return [
        Task("spec", "planner", "llm", [], {"estimate_s": 0.9, "goal": "team-board"}),
        Task("schema", "writer", "tool", ["spec"], {"estimate_s": 0.4}),
        Task("backend", "coder", "llm", ["spec"], {"estimate_s": 1.2, "module": "backend"}),
        Task("frontend", "coder", "llm", ["spec"], {"estimate_s": 1.0, "module": "frontend"}),
        Task("unit_test", "tester", "tool", ["backend", "schema"], {"estimate_s": 0.8}),
        Task("e2e_test", "tester", "tool", ["frontend", "backend"], {"estimate_s": 0.9}),
        Task("review", "reviewer", "llm", ["backend", "frontend"], {"estimate_s": 0.7}),
        Task("docs", "writer", "tool", ["schema"], {"estimate_s": 0.3}),
        Task("integrate", "reviewer", "llm",
             ["unit_test", "e2e_test", "review", "docs"], {"estimate_s": 0.8}),
    ]


def main() -> None:
    tasks = build_tasks()
    serial = sum(t.payload["estimate_s"] for t in tasks)
    print(f"任务数={len(tasks)}  串行基线(理论)={serial:.1f}s  资源槽位=llm:2 tool:1 io:2")
    rows = {}
    for policy in ("fifo", "critical_path", "spt"):
        spans = []
        for _ in range(3):
            sched = DAGScheduler(build_tasks(), policy=policy)
            rep = sched.run(AGENTS)
            spans.append(rep.makespan)
            last = rep
        span = statistics.fmean(spans)
        rows[policy] = {"makespan": span, "speedup_vs_theoretical_serial": serial / span}
        print(f"\npolicy={policy}: makespan={span:.2f}s  speedup={serial/span:.2f}×")
        print(last.summary())
    best = max(rows.items(), key=lambda kv: kv[1]["speedup_vs_theoretical_serial"])
    print(f"\n最佳策略：{best[0]}（{best[1]['speedup_vs_theoretical_serial']:.2f}×）")


if __name__ == "__main__":
    main()
