# AIOS 与 OWL 代码阅读指南（含代码规模统计）

> 面向 2026 全国大学生计算机系统能力大赛·操作系统设计赛（中西部与华南区域赛）功能挑战赛道《智能体操作系统中的多智能体协作技术》。
> 本文回答两个问题：**① `vendor/AIOS` 与 `vendor/owl` 分别有多少代码、代码在哪里；② 时间有限时应该按什么顺序读、读到什么程度算"读懂"。**
> 本文是"怎么读"，`doc/09` 是"读出了什么"（结论与行号证据），两者配合使用；所有数字均可用 §8 的脚本复现。

---

## 0. 一页速览

| 维度 | `vendor/AIOS` | `vendor/owl` |
|---|---|---|
| 快照 commit | `f46ce7c`（README 最新到 2025-07，v0.2.2 重构后） | `1794e8a`（`pyproject` version 0.0.1） |
| 全部文件 | 251 | 153 |
| **代码文件**（`.py/.sh/.rs`） | **194**（py 181 / sh 5 / rs 8） | **64**（py 61 / sh 3） |
| 原始行数 | **47,054** | **16,711** |
| **代码行数**（非空非注释） | **29,248** | **7,856** |
| 测试代码 | **43 个文件 / 11,922 代码行**（tests/） | **0**（无测试目录） |
| 文档（Markdown） | 16 篇 / 2,598 行 | 30 篇 / 5,863 行 |
| 一句话定位 | 内核 + 服务端 + 桌面虚拟环境，代码主要集中在 `aios/`（15,681 代码行） | 应用层参考实现 + Gradio WebUI + 社区示例，核心协议只有 1 个文件 |

**两个仓库合计：258 个代码文件、63,765 原始行、37,104 行代码。** 但"值得读的"远少于此：

- AIOS 的 `aios/tool/virtual_env`（桌面 VM 环境、评测器、云厂商适配）一个目录就有 **12,836 原始行，占整个 `aios/` 包的 49%**，与赛题无关，**直接跳过**；
- OWL 的 4 个 `webapp*.py`（1,328 + 1,319 + 1,291 + 803 = 4,741 原始行，占 `owl/` 包 77%）是同一 WebUI 的中/日/英/备份四份拷贝，**只读或不读**；
- **真正的内核主线（llm_core + syscall + scheduler + context + hooks + config + terminal）约 3,120 代码行**，一个下午可以精读完；
- **OWL 的核心只有 `owl/utils/enhanced_role_playing.py`（610 行）**，其余是示例与工具封装。

> 统计口径：代码行 = 非空且非注释行（Python 的 `#`、`"""..."""`；Shell/JS 的 `#`、`//`）；不含 `.git`、`__pycache__`、png/jpg/pdf/xlsx 等二进制；`aios-rs`（实验性 Rust 重写，187 代码行）计入但单独标注。

---

## 1. 目录结构与代码分布

### 1.1 AIOS：内核、测试、运行时三分

```
vendor/AIOS/                      251 文件 / 47,054 原始行
├── aios/                 132 文件 / 26,195 行 / 15,681 代码行   ← 内核与组件本体
│   ├── llm_core/           4 文件 /  2,236 行   LLM 适配、路由、本地后端
│   ├── syscall/           10 文件 /  1,599 行   系统调用对象与执行器
│   ├── scheduler/          4 文件 /    796 行   FIFO / RR 调度器
│   ├── context/            3 文件 /    465 行   上下文/中断/流式
│   ├── memory/            16 文件 /  5,238 行   记忆管理、注入、写屏障
│   ├── storage/            4 文件 /    813 行   文件系统与向量库
│   ├── tool/              60 文件 / 13,177 行   工具管理器 + 桌面虚拟环境（后者 12,836 行，可不读）
│   ├── hooks/             21 文件 /    819 行   SDK 侧装配入口（use* 工厂）
│   ├── terminal/           2 文件 /    240 行   终端意图路由
│   ├── utils/              6 文件 /    535 行   日志/压缩/ID/launch 命令
│   └── config/             1 文件 /    277 行   配置加载
├── tests/                 43 文件 / 18,582 行 / 11,922 代码行   ← 唯一的"官方用法"
│   ├── modules/memory/    29 个测试文件（写屏障、跨用户隔离、注入矩阵）
│   ├── modules/llm/        6 个（ollama/openai 的单发与并发）
│   └── modules/{storage,tool,agent_load}/ 5 个
├── runtime/                3 文件 /  1,103 行   FastAPI 内核服务（launch.py 853 行）
├── install/                1 文件 /    469 行   发行包安装脚本
├── scripts/                7 文件 /    455 行   run_terminal.py 等脚本
├── aios-rs/                8 文件 /    250 行   实验性 Rust 重写（可忽略）
├── docs/                  3 篇 md（856 行）+ 18 张图片
└── README.md              459 行（部署模式/安装/Quickstart）
```

**规模比例**：测试代码（11,922 行）相当于内核源码（15,681 行）的 **76%**——这在本赛道是"利好"：官方把 API 用法几乎都写成了测试，读测试比读文档可靠。

### 1.2 OWL：一个协议文件 + 大量示例

```
vendor/owl/                       153 文件 / 16,711 原始行
├── owl/                    9 文件 /  6,170 行 / 2,776 代码行
│   ├── utils/enhanced_role_playing.py   610 行   ← 唯一核心：双角色协作协议
│   ├── utils/gaia.py                    428 行   GAIA 评测流程
│   ├── utils/document_toolkit.py        322 行   文档解析工具封装
│   ├── utils/common.py                   36 行   工具函数
│   └── webapp.py / _zh / _jp / _backup  4,741 行  Gradio UI（四份拷贝，跳过）
├── examples/               8 文件 /  1,748 行   run.py / run_vllm.py / run_qwen.py ...
├── community_usecase/     43 文件 /  8,287 行   15 个社区示例项目（选读 1–2 个）
├── .container/             3 文件 /    377 行   Docker/容器启动
├── README.md / _zh / _ja  2,168 行（三语重复）
└── assets/                5 个图片/PDF（不计代码）
```

**OWL 没有测试目录、没有编排器实现**：真正干活的是 `camel-ai` 的 `Workforce`（`examples/run.py` 里调用），`owl/utils/enhanced_role_playing.py` 只实现"user ↔ assistant"两角色的对话协议（`OwlRolePlaying`）。这与 `doc/09` §7 的结论一致。

### 1.3 两仓库对照：谁该读多深

| 需求 | 读 AIOS | 读 OWL |
|---|---|---|
| 拿一个可运行的 LLM 后端 / 记忆 / 存储 | **必读**（llm_core、memory、storage、config） | 不需要 |
| 理解"agent 如何发一次 LLM 调用" | **必读**（hooks → syscall → scheduler → adapter） | 不需要 |
| 找多智能体协作协议范本 | 不需要 | **必读**（enhanced_role_playing.py） |
| 找"并行编排" | 读调度器 + adapter 双层线程池（但只是请求级并行） | **没有**（Workforce 在 camel-ai 里） |
| 找端侧 7B 接入写法 | 读 `llm_core/local.py` + `config.yaml.example` 的 ollama/vllm 配置 | 读 `examples/run_vllm.py` |
| 找 DAG / 依赖调度 | **没有**（内核不感知依赖） | **没有**（见 `doc/11` §5） |

---

## 2. 先读什么：三条阅读路线

### 路线 A：30 分钟"知道它是什么"（答辩前速览）

按顺序读 4 个文件即可，**不写笔记，只回答"请求从哪进、在哪排队、在哪并发、结果怎么回"**：

1. `vendor/AIOS/README.md` §Architecture + §Quickstart（约 120 行）：五种部署模式与 `uvicorn runtime.launch:app` 启动方式；
2. `vendor/AIOS/runtime/launch.py:728` 的 `handle_query`（约 70 行）：HTTP 入口，`query_type` 四选一分派；
3. `vendor/AIOS/aios/scheduler/fifo_scheduler.py:206` 的 `process_llm_requests`（约 30 行）：攒批循环；
4. `vendor/AIOS/aios/llm_core/adapter.py:533-557`：`ThreadPoolExecutor` 分组并发的 25 行。

### 路线 B：半天"吃透内核主线"（写编排器之前必做）

在路线 A 基础上补 5 个文件（合计约 2,600 行，精读约 3–4 小时）：

| # | 文件 | 行数 | 读它回答什么问题 |
|---|---|---|---|
| 1 | `aios/syscall/__init__.py` | 364 | `Syscall(Thread)` 就是"进程控制块"：`event`、状态、时间戳、优先级（`:6` 起；`run()` 在 `:297`，`:307` 置 event、`:311` `event.wait()`） |
| 2 | `aios/syscall/syscall.py` | 861 | 执行器如何把 query 变成 syscall 并**同步阻塞**（`SyscallExecutor:37`、`_execute_syscall:82`、`execute_request:705`、`create_syscall_executor:835`） |
| 3 | `aios/llm_core/adapter.py` | 1,089 | 一次 LLM syscall 如何被路由、分组、双层线程池执行、错误如何兜底（`execute_llm_syscalls:433`、分组 `:524-531`、外层池 `:553`、`_process_batch_for_model:625`、`execute_llm_syscall:676`） |
| 4 | `aios/hooks/modules/agent.py` + `hooks/stores/_global.py` | 189 + 37 | SDK 侧装配：`useFactory:15`、`submitAgent:24`、`awaitAgentExecution:81`；**四类请求队列是模块级全局单例**（`_global.py:11-37`） |
| 5 | `aios/config/config_manager.py` + `aios/config/config.yaml.example` | 277 | 配置项含义：`use_context_manager`（决定 FIFO/RR）、models/backend、memory provider |

读完应能画出 §3 的时序图。

### 路线 C：一天"全貌 + 可复用点"

- 上午：路线 B；
- 下午上：`aios/memory/{manager.py,context_injector.py,write_barrier.py}`（427 + 790 + 392 行）——多 agent 共享记忆的隔离与可见性，**赛题做"共享评审历史"时必读**；
- 下午中：`tests/modules/llm/ollama/test_single.py` 与 `test_concurrent.py`——**抄真实调用参数**；`tests/modules/memory/` 挑 3 个写屏障测试看断言方式；
- 下午下：OWL `owl/utils/enhanced_role_playing.py`（610 行，重点 `step:255` 与 `run_society:481`）+ `examples/run.py`（238 行，`construct_agent_list:45`、`construct_workforce:173`、`main:217`）+ `examples/run_vllm.py`（284 行，7B 本地端点写法）；
- 晚上：把 `doc/09` 的行号结论对照源码抽查 10 处，确认"读到的和文档写的一致"。

**不建议**给 `aios/tool/virtual_env/**`（12,836 行）、`owl/webapp*.py`（4,741 行）、`community_usecase/**`（8,287 行，除非要找 prompt 灵感）分配时间。

---

## 3. 一条请求的完整生命周期（读代码时的主线）

```mermaid
sequenceDiagram
    autonumber
    participant SDK as SDK 编排器
    participant API as Kernel API
    participant EX as SyscallExecutor
    participant Q as 全局请求队列
    participant SCH as FIFOScheduler
    participant AD as LLMAdapter
    SDK->>API: POST /query (query_type=llm)
    API->>EX: execute_request(agent_name, LLMQuery)  [:728,:705]
    EX->>EX: _execute_syscall -> 构造 Syscall(Thread)  [:82]
    EX->>Q: add_message(syscall)
    EX->>EX: syscall.start(); syscall.join()  ← 调用线程同步阻塞
    Note over EX: Syscall.run() 只做 event.wait()
    loop 每 batch_interval 秒
        SCH->>Q: 非阻塞取空队列，攒成 batch  [:206-232]
    end
    SCH->>AD: execute_llm_syscalls(batch)  [:433]
    AD->>AD: 按模型分组，外层池并发 [:524-557]
    AD->>AD: 组内内层池逐条执行 [:625,:644]
    AD-->>EX: 回写 response，event.set() 唤醒
    EX-->>API: 返回 LLMResponse
    API-->>SDK: JSON
```

**四个必须记住的机制**（答辩被问到"并行到底发生在哪"时用）：

1. **调用线程是同步阻塞的**：`syscall.join()` 在 `syscall.py` 的 `_execute_syscall` 里，所以"并发"不是靠单次调用不阻塞，而是**靠应用层先并发发起**；
2. **攒批窗口 `batch_interval` 默认 1.0 秒**（`fifo_scheduler.py:70`），窗口内到达的请求合成一批；
3. **批内并发是双层线程池**（`adapter.py:553` 外层按模型组、`:644` 内层组内逐条），**无全局并发上限**；
4. **完成信号是 `event.set()`**：`Syscall.run()` 在 `:297` 只等待，执行器完成后置 response 并唤醒。

---

## 4. 关键文件"读什么"清单

### 4.1 AIOS（按优先级）

| 优先级 | 文件 | 行数 | 读后必须能回答 |
|---|---|---|---|
| **P0** | `runtime/launch.py` | 853 | 服务如何初始化（`initialize_components:297`、`initialize_scheduler:237`）、`useSysCall()` 在模块导入时创建全局执行器（`:69`）、有哪些端点（`/agents/submit:601`、`/query:728`） |
| **P0** | `aios/syscall/__init__.py` | 364 | `Syscall` 的字段与生命周期；为什么它是 `Thread` 却不执行任务 |
| **P0** | `aios/syscall/syscall.py` | 861 | `_execute_syscall:82` 的"入队-等待-重试"逻辑；`execute_request:705` 按 `action_type` 分派；写屏障在 acceptance 阶段介入 |
| **P0** | `aios/scheduler/fifo_scheduler.py` | 346 | 四个 processor 线程（`start:316`）、LLM 攒批（`:206`）、批执行（`:155`） |
| **P0** | `aios/llm_core/adapter.py` | 1,089 | 路由 `get_model_idxs`（`:522`）、双层线程池、错误处理（`_handle_completion_error:378`） |
| P1 | `aios/scheduler/base.py` | 151 | 调度器抽象与四线程模型（`start_processing_threads:89`） |
| P1 | `aios/hooks/modules/*.py` + `hooks/stores/_global.py` | 819 + 37 | SDK 工厂函数如何组装组件、全局单例队列 |
| P1 | `aios/config/config_manager.py` | 277 | 配置键与默认值（`use_context_manager` 默认 false → FIFO） |
| P1 | `aios/context/simple_context.py` | 443 | 中断/时间片/HF 流式（只在 RR 路径使用，赛题可跳过细节） |
| P2 | `aios/memory/manager.py` / `context_injector.py` / `write_barrier.py` | 427 / 790 / 392 | 记忆 provider、上下文注入、写屏障（做共享记忆时读） |
| P2 | `aios/storage/*`、`aios/tool/manager.py` | 813 / 118 | 存储与工具执行 |
| P2 | `aios/terminal/intent_router.py` | 223 | 终端自然语言转 syscall（演示可用） |
| **跳读** | `aios/tool/virtual_env/**` | 12,836 | 桌面 VM / 评测器，与本赛题无关 |
| **跳读** | `aios-rs/**` | 250 | 实验性 Rust 重写，只有骨架 |

### 4.2 OWL（按优先级）

| 优先级 | 文件 | 行数 | 读后必须能回答 |
|---|---|---|---|
| **P0** | `owl/utils/enhanced_role_playing.py` | 610 | 双角色协议如何构造消息（`_init_agents:68`、`_construct_gaia_sys_msgs:182`）、`step:255` 的轮次与 `TASK_DONE` 判定、`run_society:481` 的统计口径 |
| **P0** | `examples/run.py` | 238 | Workforce 的真实构造（`construct_workforce:173`）、任务如何下发与汇总（`main:217`） |
| P1 | `examples/run_vllm.py` | 284 | 7B 本地 OpenAI 兼容端点写法（`ModelPlatformType.OPENAI_COMPATIBLE_MODEL` + url/api_key） |
| P1 | `owl/utils/gaia.py` | 428 | GAIA 数据集加载、答案比对、评测指标 |
| P2 | `owl/utils/document_toolkit.py` | 322 | PDF/Word/图片解析工具封装范式 |
| **跳读** | `owl/webapp*.py`（4 份） | 4,741 | Gradio UI，与内核/协作逻辑无关 |
| 选读 | `community_usecase/` 15 个项目 | 8,287 | 找 prompt/工具组合灵感时读 1–2 个（如 `excel_analyzer`、`stock-analysis`） |

---

## 5. 读代码时必须带上的 10 个"坑"

这些是文档与代码不一致、或容易误判的地方，**踩中任何一个都会写出跑不起来的集成代码**：

1. **RR 调度器在 LLM 路径上必崩**：`rr_scheduler.py:180-181` 把单个 `Syscall` 对象直接传给 `_execute_batch_syscalls`，而后者按列表遍历（`:134` 附近 `for syscall in batch`）→ `TypeError`。**保持 `use_context_manager: false`**（`launch.py:242` 默认值），走 FIFO。
2. **`batch_interval` 代码与注释不一致**：默认值 `1.0`（`fifo_scheduler.py:70`），但 docstring 写 "Defaults to 0.1"（`:85`）。调参时以代码为准。
3. **`install.sh` 的启动命令是错的**：`:116` 用 `uvicorn runtime.kernel:app`，但仓库里没有 `runtime/kernel.py`，真实入口是 `runtime/launch.py`（README `:321`）。照抄安装脚本会启动失败。
4. **`runtime/launch.py` 传入的 `get_*_syscall=None` 不是 bug**：`fifo_scheduler_nonblock`（`hooks/modules/scheduler.py:124-145`）会在 None 时回填 `_global.py` 的全局队列 getter。**排查"调度器不消费请求"时先看这一步**。
5. **队列是进程级全局单例**（`hooks/stores/_global.py:11-37`）：一个进程里起两个 kernel 会共享队列；写测试时要隔离进程，否则会出现"请求被另一个实例消费"的诡异现象。
6. **`useSysCall()` 在 `launch.py:69` 模块级执行**：导入即创建全局执行器与队列，之后 `initialize_components` 再把 memory/context_injector 挂上去。理解初始化顺序才能解释"为什么配置里的 memory provider 影响的是执行器属性"。
7. **OWL 的 Workforce 不在本仓库**：`examples/run.py` 从 `camel` 导入，`owl` 包内没有任何编排器实现。读 OWL 只能学到"双角色协议"和"Workforce 用法示例"。
8. **4 个 `webapp*.py` 是同一 UI 的四份拷贝**（中/日/英/备份），不要以为有三个不同前端；改 UI 只改 `webapp.py`。
9. **`community_usecase/` 是社区贡献的示例集合**（15 个项目，含 3 个 MCP 案例），不是框架核心；其中的 `a_share_investment_agent_camel` 自带一套 `src/agents`，读它容易误以为 OWL 有多 agent 框架。
10. **`tool/virtual_env` 与赛题无关**：桌面 VM、云厂商（AWS/Azure/GCP/Docker/VirtualBox/VMware）适配、GUI 评测器都在这里（12,836 行，占 `aios/` 包 49%）；读它会大量消耗时间而对"多智能体协作"零帮助。

---

## 6. 与赛题实现的对接顺序（读完就动手）

| 步骤 | 读什么 | 产出 |
|---|---|---|
| ① 跑通单次调用 | `tests/modules/llm/ollama/test_single.py`、`README` Quickstart | 一次 `llm_chat` 返回 `response_message` |
| ② 跑通并发 | `tests/modules/llm/ollama/test_concurrent.py`、`adapter.py:433` | 4 线程同时发请求，确认墙钟 < 串行 |
| ③ 接编排器 | 本指南 §3 时序图 + `doc/09` §8 架构 | 应用层 DAG：`Semaphore(max_parallel=4)` + `asyncio.to_thread(llm_chat)` |
| ④ 复用记忆 | `aios/memory/*` + `tests/modules/memory/` 任一隔离测试 | 多 agent 共享/隔离策略 |
| ⑤ 参考协议 | `owl/utils/enhanced_role_playing.py:255` + `examples/run.py` | `TASK/PLAN/PATCH/REVIEW/TEST_RESULT` 消息协议 |

> 一句话：**AIOS 提供"单次调用 + 记忆 + 存储"，OWL 提供"两角色协议范本"，DAG 编排与并行控制必须自己写**——这正是 `doc/11` 认定的创新空位 G1。

---

## 7. 自测 12 问（答不上就回去读对应文件）

1. 一次 `llm_chat` 从 HTTP 到返回，经过哪 5 个组件？各自文件与关键行号？
2. `Syscall` 为什么继承 `Thread`？它的 `run()` 真的"执行"了吗？
3. `batch_interval` 默认多少？它决定了什么？调小有什么副作用？
4. 批内并发的两层线程池分别在哪一行创建？为什么按"模型组"分组？
5. 内核有没有"同时最多 N 个 LLM 请求"的上限？在哪里配置？
6. FIFO 与 RR 的差别是什么？为什么赛题环境应该用 FIFO？
7. `use_context_manager: true` 会发生什么？为什么？
8. `get_*_syscall=None` 传进去之后，调度器从哪里拿到队列？
9. 四类请求队列为什么是全局单例？对写测试有什么影响？
10. AIOS 的"记忆写屏障"解决什么问题？在 acceptance 阶段的哪一段代码？
11. OWL 的 `OwlRolePlaying.step` 如何判断任务完成？`round_limit` 起什么作用？
12. `examples/run_vllm.py` 接入本地 7B 时，`url` 与 `api_key` 分别对应什么？

---

## 8. 统计复现

```bash
# 目录/语言/代码行统计（输出 build/vendor_code_stats.json）
python build/vendor_code_stats.py

# 关键文件单文件行数 + virtual_env 占比
python build/key_file_lines.py
```

- 脚本位置：`build/vendor_code_stats.py`、`build/key_file_lines.py`（`build/` 已在 `.gitignore` 中，属于过程材料）；
- 统计口径：代码行 = 非空非注释行；Python 文档字符串按注释处理（简化处理，多行字符串按首尾 `"""` 配对）；
- 快照时点：2026-11-18 工作区；AIOS 来自 `git subtree` 合并 `f46ce7c`，OWL 来自 `1794e8a`。

## 9. 与既有文档的关系

| 文档 | 关系 |
|---|---|
| `doc/09-AIOS与OWL代码库调研与SDK实践.md` | **结论版**：内核能力边界、SDK 用法、四个坑、架构方案；本文是它的"阅读方法版" |
| `doc/04-智能体操作系统内核与并发服务-精读.md` | 论文层面的内核/并发理论；本文是源码层面的落地 |
| `doc/11-同类项目调研与创新空位分析.md` | 已核实"AIOS 内核不感知依赖"（`syscall.py:171-186`，见其 §5.2），本文 §3/§5 与之互证 |
| `doc/10-调研方法与规范/` | 本文的"精读"部分遵循 `02-精读与写作规范.md` 的三层阅读法 |

## 10. 更新记录

| 日期 | 版本 | 变更 |
|---|---|---|
| 2026-11-18 | v1.0 | 首次发布：两份仓库代码规模统计、三条阅读路线、请求生命周期时序图、关键文件清单、10 个坑、自测 12 问 |
