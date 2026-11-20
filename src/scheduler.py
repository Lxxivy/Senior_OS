"""DAG 任务调度器（多智能体执行骨架）

设计目标：把「调度算法」从「智能体实现」里剥离出来，让 Planner 只产出 DAG，
由调度器负责：依赖门控、资源槽位、优先级排序、并发控制、计时与报告。

关键设计（与调研结论对齐，见 doc/17）：
  - **应用层调度**：AIOS 内核不感知依赖（syscall 入队后同步 join），因此 DAG 必须在这里管。
  - **资源分类**：llm / tool / io 三类槽位，默认容量对齐端侧现实（llm=2、tool=1、io=2）。
  - **优先级 = 关键路径**：bottom-level（到汇点的最长路径）大者先跑，避免长尾任务堵住关键路径。
  - **不可抢占 + 有界并发**：任务一旦开始就跑到结束，槽位满了就等，不无限起线程。
  - **失败不静默**：任务异常会记录并阻断其下游，报告里能看出被阻断的节点。

用法：
    sched = DAGScheduler(tasks, resources={"llm": 2, "tool": 1, "io": 2})
    report = sched.run(agents)          # agents: dict[str, Callable[[Task], Any]]
    print(report.summary())
"""
from __future__ import annotations

import queue
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set

RESOURCE_KINDS = ("llm", "tool", "io")


@dataclass
class Task:
    tid: str
    agent: str                     # 用哪个 agent 执行（agents 字典的键）
    resource: str = "llm"          # llm | tool | io
    depends_on: List[str] = field(default_factory=list)
    payload: Dict[str, Any] = field(default_factory=dict)
    timeout: Optional[float] = None


@dataclass
class TaskResult:
    tid: str
    ok: bool
    output: Any = None
    error: Optional[str] = None
    start: float = 0.0
    finish: float = 0.0
    wait: float = 0.0


@dataclass
class ScheduleReport:
    makespan: float
    serial_baseline: float
    critical_path: float
    results: Dict[str, TaskResult]
    blocked: List[str]
    resources: Dict[str, int]

    @property
    def speedup(self) -> float:
        return self.serial_baseline / self.makespan if self.makespan else 0.0

    def summary(self) -> str:
        ok = sum(1 for r in self.results.values() if r.ok)
        lines = [
            f"makespan={self.makespan:.2f}s  serial={self.serial_baseline:.2f}s  "
            f"speedup={self.speedup:.2f}x  critical_path={self.critical_path:.2f}s",
            f"succeeded={ok}/{len(self.results)}  blocked={len(self.blocked)}  resources={self.resources}",
        ]
        for tid, r in self.results.items():
            if not r.ok:
                lines.append(f"  ! {tid}: {r.error}")
        if self.blocked:
            lines.append(f"  blocked due to upstream failure: {', '.join(self.blocked)}")
        return "\n".join(lines)


class DAGScheduler:
    def __init__(self, tasks: List[Task], resources: Optional[Dict[str, int]] = None,
                 policy: str = "critical_path", poll_interval: float = 0.005) -> None:
        self.tasks = {t.tid: t for t in tasks}
        if len(self.tasks) != len(tasks):
            raise ValueError("存在重复的 task id")
        self.resources = {"llm": 2, "tool": 1, "io": 2}
        if resources:
            self.resources.update(resources)
        self.policy = policy
        self.poll_interval = poll_interval
        self._validate()

    # ------------------------------------------------------------ 校验与优先级
    def _validate(self) -> None:
        for t in self.tasks.values():
            for d in t.depends_on:
                if d not in self.tasks:
                    raise ValueError(f"{t.tid} 依赖不存在的任务 {d}")
            if t.resource not in RESOURCE_KINDS:
                raise ValueError(f"{t.tid} 的资源类型非法：{t.resource}")
        indeg = {tid: len(t.depends_on) for tid, t in self.tasks.items()}
        succ: Dict[str, List[str]] = {tid: [] for tid in self.tasks}
        for t in self.tasks.values():
            for d in t.depends_on:
                succ[d].append(t.tid)
        stack = [tid for tid, n in indeg.items() if n == 0]
        seen = 0
        while stack:
            cur = stack.pop()
            seen += 1
            for s in succ[cur]:
                indeg[s] -= 1
                if indeg[s] == 0:
                    stack.append(s)
        if seen != len(self.tasks):
            raise ValueError("DAG 存在环")

    def bottom_level(self) -> Dict[str, float]:
        """bottom-level = 自身 + 到汇点的最长后继路径；未知时长时按 1 计，可用 estimate 覆盖"""
        succ: Dict[str, List[str]] = {tid: [] for tid in self.tasks}
        for t in self.tasks.values():
            for d in t.depends_on:
                succ[d].append(t.tid)
        memo: Dict[str, float] = {}

        def bl(tid: str) -> float:
            if tid in memo:
                return memo[tid]
            w = float(self.tasks[tid].payload.get("estimate_s", 1.0))
            memo[tid] = w + max((bl(s) for s in succ[tid]), default=0.0)
            return memo[tid]

        for tid in self.tasks:
            bl(tid)
        return memo

    # ------------------------------------------------------------ 执行
    def run(self, agents: Dict[str, Callable[[Task], Any]]) -> ScheduleReport:
        t0 = time.perf_counter()
        bl = self.bottom_level()
        caps = dict(self.resources)
        state: Dict[str, str] = {tid: "pending" for tid in self.tasks}   # pending/running/ok/failed/blocked
        results: Dict[str, TaskResult] = {}
        comp_done: Dict[str, float] = {}
        succ: Dict[str, List[str]] = {tid: [] for tid in self.tasks}
        remaining: Dict[str, Set[str]] = {tid: set(t.depends_on) for tid, t in self.tasks.items()}
        for t in self.tasks.values():
            for d in t.depends_on:
                succ[d].append(t.tid)

        events: "queue.Queue[str]" = queue.Queue()
        lock = threading.Lock()

        def worker(task: Task) -> None:
            start = time.perf_counter() - t0
            try:
                fn = agents[task.agent]
                out = fn(task)
                with lock:
                    results[task.tid] = TaskResult(task.tid, True, out, None, start,
                                                   time.perf_counter() - t0, 0.0)
                    state[task.tid] = "ok"
            except Exception as exc:  # noqa: BLE001 - 调度器必须兜住任何异常
                with lock:
                    results[task.tid] = TaskResult(task.tid, False, None, f"{type(exc).__name__}: {exc}",
                                                   start, time.perf_counter() - t0, 0.0)
                    state[task.tid] = "failed"
            finally:
                with lock:
                    caps[task.resource] += 1
                events.put(task.tid)

        while True:
            with lock:
                pending = [self.tasks[tid] for tid, st in state.items() if st == "pending"]
                ready = [t for t in pending if not remaining[t.tid]]
            if self.policy == "critical_path":
                ready.sort(key=lambda t: (-bl[t.tid], t.tid))
            elif self.policy == "spt":
                ready.sort(key=lambda t: (float(t.payload.get("estimate_s", 1.0)), t.tid))
            elif self.policy == "lpt":
                ready.sort(key=lambda t: (-float(t.payload.get("estimate_s", 1.0)), t.tid))
            else:  # fifo
                ready.sort(key=lambda t: list(self.tasks).index(t.tid))
            for t in ready:
                if caps[t.resource] <= 0:
                    continue
                with lock:
                    caps[t.resource] -= 1
                    state[t.tid] = "running"
                threading.Thread(target=worker, args=(t,), daemon=True).start()

            with lock:
                all_finished = all(st in ("ok", "failed", "blocked") for st in state.values())
            if all_finished:
                break

            try:
                finished_tid = events.get(timeout=self.poll_interval)
            except queue.Empty:
                continue
            st = state[finished_tid]
            comp_done[finished_tid] = time.perf_counter() - t0
            if st in ("ok", "failed"):
                with lock:
                    for s in succ[finished_tid]:
                        remaining[s].discard(finished_tid)

            # 上游失败的节点：阻断其所有下游（避免“永远等不到”）
            with lock:
                changed = True
                while changed:
                    changed = False
                    for tid, s in state.items():
                        if s == "pending":
                            t = self.tasks[tid]
                            if any(state[d] in ("failed", "blocked") for d in t.depends_on):
                                state[tid] = "blocked"
                                results[tid] = TaskResult(tid, False, None, "upstream failed")
                                changed = True

        makespan = time.perf_counter() - t0
        serial = sum(float(t.payload.get("estimate_s", 0.0)) for t in self.tasks.values())
        blocked = [tid for tid, st in state.items() if st == "blocked"]
        # 等待时间：开始时刻 - 其前驱最晚完成时刻
        waits = []
        for tid, r in results.items():
            deps = self.tasks[tid].depends_on
            ready_at = max((comp_done[d] for d in deps if d in comp_done), default=0.0)
            r.wait = max(0.0, r.start - ready_at)
            waits.append(r.wait)
        return ScheduleReport(makespan=makespan, serial_baseline=serial,
                              critical_path=max(bl.values()), results=results,
                              blocked=blocked, resources=self.resources)


def topo_order(tasks: List[Task]) -> List[str]:
    """串行基线用的拓扑序（同文件方便对照）"""
    by_id = {t.tid: t for t in tasks}
    indeg = {t.tid: len(t.depends_on) for t in tasks}
    succ: Dict[str, List[str]] = {t.tid: [] for t in tasks}
    for t in tasks:
        for d in t.depends_on:
            succ[d].append(t.tid)
    ready = [tid for tid, n in indeg.items() if n == 0]
    out: List[str] = []
    while ready:
        cur = ready.pop(0)
        out.append(cur)
        for s in succ[cur]:
            indeg[s] -= 1
            if indeg[s] == 0:
                ready.append(s)
    return out
