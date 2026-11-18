# vendor/ —— 参考开源库快照

本目录存放调研与对照用的第三方开源仓库**快照**，全部以 `git subtree add --squash` 方式导入（单个 squash 提交，不带上游历史）。目的：让后续“读代码 / grep 证据 / 改代码做原型”都在本仓库内完成，不依赖网络。

> 快照是**只读参考**：比赛作品不要直接依赖本目录代码；修改第三方代码请另建分支或复制到 `src/`，并遵守各自许可证。

## 1. 快照清单

| 目录 | 上游仓库 | 上游提交 | 提交日期 | 许可证 | 文件数 | 资产裁剪 | 用途 |
|---|---|---|---|---|---|---|---|
| `vendor/AIOS` | gh:agiresearch/AIOS | `292d98f` | — | MIT（上游元数据；快照内 `LICENSE` 为 2 字节占位） | 251 | — | AIOS 内核：scheduler / syscall / adapter / hooks（本赛题运行底座） |
| `vendor/owl` | gh:camel-ai/owl | `5dbabd3` | — | Apache-2.0（见 `vendor/owl/licenses/LICENSE`） | 153 | — | OWL 应用层：`enhanced_role_playing`、GAIA 工具封装 |
| `vendor/Cerebrum` | gh:agiresearch/Cerebrum | `ab7e434aa9cf` | 2026-07-20 | MIT（`pyproject.toml` classifier；`LICENSE` 文件为 2 字节占位） | 763 | — | AIOS-Agent SDK：`llm` / `memory` / `storage` / `tool` API、`AgentManager`、`AutoTool` |
| `vendor/camel` | gh:camel-ai/camel | `c619d1fe5aa2` | 2026-11-16 | Apache-2.0 | 2015 | 129.1 MB / 228 个 | Workforce 依赖门控（`dependencies` + `completed_tasks_info`），OWL 编排的实际来源 |
| `vendor/MetaGPT` | gh:FoundationAgents/MetaGPT | `11cdf466d042` | 2026-01-21 | MIT | 1148 | 29.8 MB / 92 个 | SOP 式多角色公司、共享消息池；`NaiveSolver` 按拓扑序串行 |
| `vendor/autogen` | gh:microsoft/autogen | `8390985108cb` | 2026-11-12 | MIT（代码，见 `LICENSE-CODE`）/ CC-BY-4.0（文档，见 `LICENSE`） | 1696 | 47.1 MB / 135 个 | 对话式多智能体框架；实验性 GraphFlow 是少数“前驱完成即触发”的实现 |
| `vendor/agentscope` | gh:modelscope/agentscope | `d4ac68604d96` | 2026-11-18 | Apache-2.0 | 1324 | — | 消息中心 + `msghub` 广播 + executor/verifier 闭环 |
| `vendor/langgraph` | gh:langchain-ai/langgraph | `02f2c2e6c992` | 2026-11-16 | MIT | 700 | — | Pregel 依赖边触发并行 + 并发上限配置（答辩对照必读） |
| `vendor/agentflow` | gh:ryofuu/agentflow | `121a48e800ee` | 2026-02-23 | MIT | 31 | — | 唯一“YAML `needs` + Kahn 分层 + 层内真并行”的完整实现（TypeScript） |
| `vendor/crewAI` | gh:crewAIInc/crewAI | `999badb19796` | 2026-11-17 | MIT | 1157 | 13.7 MB / 10 个 + `tests/ docs/ examples/` 目录 | `context` 依赖校验（禁止回指未来任务），对照用 |
| `vendor/swarm` | gh:openai/swarm | `6af0b4caf37d` | 2026-04-15 | MIT | 288 | — | 轻量 handoff 基线 |
| `vendor/TaskWeaver` | gh:microsoft/TaskWeaver | `d44ddef23f90` | 2026-03-23 | MIT | 421 | — | 代码解释器式任务规划，对照用 |

合计 **9,543 个文件**（其中新导入 10 个仓库 9,543 个文件；AIOS/owl 为更早导入）。导入报告：`build/vendor_import_report.json`（脚本 `build/vendor_import.py`）。

## 2. 为什么是“镜像 + squash”而不是直接 subtree

`build/reposrc/` 下的参考克隆全部是 `git clone --depth 1`（浅克隆）。`git subtree add <浅克隆> HEAD --squash` 会失败：

```
warning: rejected HEAD because shallow roots are not allowed to be updated
fatal: Needed a single revision
```

因此脚本先在 `build/vendor_tmp/<name>/` 用工作树重建一个**普通（非浅）仓库**并提交为镜像快照，再把镜像 squash 进 `vendor/`。每个 vendor 提交的 message 都写明了上游 URL、上游 SHA、日期与许可证，所以“squashed 丢历史”不影响溯源。

## 3. 资产裁剪

媒体/二进制资产体积巨大（camel 145 MB、crewAI 535 MB、autogen 55 MB、MetaGPT 38 MB），全部导入会让仓库膨胀到 700 MB 以上。裁剪规则：

- 跳过 `node_modules` / `.venv` / `__pycache__` / `dist` / `build` 等构建产物目录；
- 丢弃 `.pdf .png .jpg .gif .webp .svg .ico .mp4 .ipynb .lock .zip .whl .onnx .pkl .parquet .safetensors` 等媒体/二进制/数据文件，以及单文件 > 2 MB 的资源；
- crewAI 额外丢弃 `tests/ docs/ examples/ .github/`（其体积主要是测试 fixture）。

**代码、测试代码、Markdown 文档文本均保留**，只删掉不能用于代码分析的资产，因此 `doc/04/05/06/09/11/12/13` 引用的行号在 vendor 快照里依然有效。

两点已知差异：

1. `git add -A` 会遵守各仓库自带的 `.gitignore`，所以镜像里复制的文件数与进入 vendor 的文件数略有出入（MetaGPT 少 15、autogen 少 6、langgraph 少 7、Cerebrum 少 0）。
2. crewAI 上游布局是 `lib/crewai/src/crewai/crew.py`（不是 `src/crewai/crew.py`），引用时以 `vendor/` 实际路径为准。

## 4. 与调研文档的对应关系

| 主题 | 看这里 |
|---|---|
| AIOS 内核请求生命周期、FIFO 攒批、无依赖感知 | `vendor/AIOS/aios/{syscall,scheduler,llm_core,config}`；配套 `doc/12` §3–§5 |
| SDK 客户端 API（LLM/Memory/Storage/Tool） | `vendor/Cerebrum/cerebrum/{llm,memory,storage,tool,interface}/`；配套 `doc/13` |
| 依赖门控 / 自动分配 | `vendor/camel/camel/societies/workforce/workforce.py`（`_update_task_dependencies_from_assignments`、`all(dep_id in completed_tasks_info …)`） |
| 共享消息池 / SOP 串行 | `vendor/MetaGPT/metagpt/{team.py,roles/,strategy/solver.py}` |
| 依赖边触发并行 | `vendor/langgraph/libs/langgraph/langgraph/pregel/_algo.py`；`vendor/autogen/python/packages/autogen-agentchat/src/autogen_agentchat/teams/_group_chat/_graph/_digraph_group_chat.py` |
| Kahn 分层 + 层内并行 | `vendor/agentflow/src/scheduler.ts`（`topoLevels`）、`src/engine.ts` |
| 角色间 critique 闭环 | `vendor/agentscope/src/agentscope/pipeline/_goal_pipeline.py`（executor ↔ verifier 结构化反馈） |
| `context` 依赖校验 | `vendor/crewAI/lib/crewai/src/crewai/crew.py`（`validate_context_no_future_tasks`） |
| 轻量 handoff | `vendor/swarm/swarm/core.py` |
| 代码解释器规划 | `vendor/TaskWeaver/taskweaver/` |

## 5. 更新 / 重新导入

```powershell
cd E:\Senior_OS
# 重新导入全部缺失库（脚本对已存在的 vendor/<name> 自动跳过）
C:\Python313\python.exe build\vendor_import.py

# 更新某个库：先删旧快照，再从新克隆重新导入
git rm -r vendor/camel
Remove-Item -Recurse -Force build\vendor_tmp\camel
C:\Python313\python.exe build\vendor_import.py
```

`build/reposrc/` 里保留的是 `--depth 1` 克隆，用于重新生成镜像；`build/` 已被 `.gitignore` 忽略，不会进仓库。

## 6. 许可证与合规

- 每个快照都原样保留了上游 `LICENSE` / `LICENSE-CODE` / `NOTICE` 文件，未删除版权声明。注意 AIOS 与 Cerebrum 快照内的 `LICENSE` 文件是上游占位文件（各 2 字节），两者的实际许可证均为 MIT（AIOS 以上游仓库元数据、Cerebrum 以 `pyproject.toml` classifier 为准）。
- 本目录仅供比赛调研、对照与原型验证；**若最终作品需要对外分发或开源，须逐个仓库核对许可证条款**（尤其 autogen 的文档是 CC-BY-4.0、代码才是 MIT；camel / agentscope 为 Apache-2.0，需保留 NOTICE 与变更说明）。
- 不要把 vendor/ 快照当作本作品的“自有代码”写进交付物。
