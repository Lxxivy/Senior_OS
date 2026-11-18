# AIOS 官方仓库 README 与架构文档要点（本地源码整理）

- **来源**：本地仓库 `E:\Senior_OS\vendor\AIOS`（git subtree 引入自 `github.com/agiresearch/AIOS`，子树合并提交 `f46ce7c…`；赛道任务以 `1794e8a` 为统一锚点）
- **原文标题**：AIOS: LLM Agent Operating System（README.md，459 行）及 `docs/` 下 CONTRIBUTE.md、SHARED_MEMORY_SYSTEM.md、memory-providers.md
- **抓取日期**：2026-11-17（本地读取，无网络请求）
- **资料属性**：开源仓库文档，仅作技术资料摘录。

## 一、AIOS 的定位：Kernel 与 SDK 分离

README 开篇即划清边界：**AIOS 是"LLM Agent Operating System"的内核（kernel）**，本身不包含 SDK；**AIOS-Agent SDK 是独立仓库 Cerebrum**（`github.com/agiresearch/Cerebrum`），负责 agent 的抽象、注册、下载与运行。本仓库 `vendor/AIOS` 只有 kernel，`requirements.txt` 里通过 `git+https://github.com/agiresearch/Cerebrum.git` 安装 SDK。这一点决定了本赛题的第一个工程风险：只 import `aios` 还不够，必须同时安装 Cerebrum，否则 `from cerebrum.llm.apis import llm_chat` 全部失败（本机实测 `ModuleNotFoundError: No module named 'cerebrum'`）。

## 二、部署模式与安装流程

README 给出四种 kernel 部署模式：Mode 1 本地 kernel、Mode 2 远程 kernel、Mode 2.5 远程 kernel 开发、Mode 3 个人远程 kernel、Mode 4 个人远程虚拟 kernel。多机场景下，**Machine 1 装 kernel + SDK，Machine 2 只装 SDK**。

安装步骤（README）：Python 3.10-3.11 → `uv pip install -r requirements.txt`（CPU）或 `requirements-cuda.txt`（GPU）→ 单独安装 Cerebrum（`git clone` + `pip install -e .`）→ 可选安装 OSWorld 虚拟化环境（computer-use MCP）。启动命令为 `bash runtime/launch_kernel.sh`，或 `python3.x -m uvicorn runtime.launch:app --host 0.0.0.0 --port 8000`，可 `nohup` 后台运行。

配置文件是 `aios/config/config.yaml`：`api_keys` 段放各家 key；`llms.models` 声明模型名、`backend`、`hostname`、`max_gpu_memory`、`eval_device`。README 给出的本机模型示例包括 `qwen2.5:7b` + `backend: ollama` + `hostname: http://localhost:11434`，以及 vLLM 的 `backend: vllm` + `hostname: http://localhost:8091/v1`。支持的 backend 覆盖 Anthropic、OpenAI、DeepSeek、Google、Groq、HuggingFace、ollama、vLLM、Novita。

## 三、配置项与"缺失的开关"

README 强调用 `aios env list` / `aios env set` / `aios refresh` 管理配置刷新。但对照 `aios/config/config.yaml.example` 可以发现一个关键事实：`scheduler` 段只有 `log_mode`，**没有并发上限、batch 大小、队列长度等任何调度参数**；`agent_factory` 段只有 `log_mode` 与 `max_workers: 64`；`use_context_manager` 是布尔开关（决定用 FIFO 还是 RR 调度器，见 `runtime/launch.py:237-268`）。也就是说，README 层面看不到"如何配置并发度"，真正决定并行度的只有 `batch_interval`（代码默认 1.0s）与 `agent_factory.max_workers`，前者甚至没有暴露到 yaml。这是赛题"并发较串行提速 ≥20%"必须自己改造的地方。

## 四、终端与 SDK 用法线索

README 指导用 `python scripts/run_terminal.py` 启动语义文件系统终端；该脚本真实展示了 SDK 的调用方式：`from cerebrum.llm.apis import llm_chat, llm_operate_file`、`from cerebrum.storage.apis import mount`，`llm_chat(agent_name="terminal", messages=[...])` 返回 dict，从 `["response"]` 里取 `response_message`；`mount(agent_name="terminal", root_dir=...)` 挂载语义文件系统。README 另说明 rollback 功能依赖 redis。

## 五、生态与相关论文

README 列出可接入的 agent 框架：OpenAGI、AutoGen、Open-Interpreter、MetaGPT；并给出 `aios-rs`（Rust 版内核）的早期示例（NoopScheduler/EchoLLM），但 `vendor/AIOS/aios-rs/README` 自述是 "early experimental scaffold … NOT feature-parity"，不能作为赛题实现基础。文末引用 AIOS（COLM 2025）、LiteCUA（arXiv 2505.18829）、A-Mem、Cerebrum（ACL 2025）、LSFS（ICLR 2025）与 "LLM as OS"（arXiv 2312.03815）等工作。

## 六、对赛题的判断

AIOS 提供了"内核 + 调度 + 系统调用 + 内存/存储/工具管理"的框架价值，但**应用层（SDK 用法、agent 模板、并发编排）不在本仓库**；`vendor/AIOS/docs/` 只有三篇说明性文档，没有完整的 SDK tutorial。因此本赛题的 4 智能体系统，必须以 Cerebrum 的 `llm_chat` 等 API 为最小依赖面，在 kernel 之上自建编排层（DAG 调度、消息总线、重试），而不能指望 AIOS 仓库自带多智能体协作组件。

## 七、复现注意事项（本地实测）

在 Windows 工作区按 README 复现时会遇到几类非文档问题，记录下来供后来者参考：① **SDK 缺失**——`requirements.txt` 用 git 依赖拉 Cerebrum，若网络受限或没单独安装，`import cerebrum` 直接报 `ModuleNotFoundError`，而 kernel 内部多处 import 它（`aios/syscall/__init__.py`、`aios/tool/manager.py`、`runtime/launch.py` 等），所以"只装 aios"是不可行的；② **启动命令**——安装脚本里写的是 `uvicorn runtime.kernel:app`，实际应用是 `runtime/launch.py`，照抄脚本会启动失败；③ **并发参数不可配**——`scheduler` 段只有 `log_mode`，`batch_interval` 硬编码在 `fifo_scheduler.py`（默认 1.0s），想要"更细粒度并发"只能改代码或调 `agent_factory.max_workers`；④ **模型服务在 Windows 上受限**——vLLM 需要 Linux + GPU，Windows 侧只能用 WSL2 或 Ollama，这会影响 7B/8B 模型的实测延迟。这些点决定了赛题实现必须把"内核依赖"当作外部服务对待，用薄客户端隔离版本风险。

## 八、关键原文摘录（英文）

> "AIOS is the LLM Agent Operating System... The AIOS-Agent SDK is available at Cerebrum."

> "Machine 1 installs the AIOS kernel and the AIOS SDK; Machine 2 only needs the AIOS SDK."

> "AIOS supports multiple LLM backends: OpenAI, Anthropic, Google, Groq, HuggingFace, ollama, vLLM, DeepSeek, Novita."
