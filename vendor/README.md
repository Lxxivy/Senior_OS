# vendor/ —— 参考开源仓库快照

本目录存放调研与对照用的第三方开源仓库**完整快照**，统一以“**单提交 squash 快照**”方式导入：每个仓库在 `vendor/<name>/` 下只对应**一个提交**，提交信息里写明上游 URL、上游完整 SHA、日期与许可证。目的：让后续“读代码 / grep 证据 / 改代码做原型”都在本仓库内完成，不依赖网络，也不拖入上游历史。

> 快照是**只读参考**：比赛作品不要直接依赖本目录代码；修改第三方代码请复制到 `src/` 或另建分支，并遵守各自许可证。

## 1. 导入方式（method C）

```powershell
git fetch --depth=1 https://github.com/agiresearch/AIOS.git 292d98f78c835499df18cdb6de6325bba1895862
git read-tree --prefix=vendor/AIOS/ -u FETCH_HEAD
git commit -m "vendor(AIOS): squashed snapshot of https://github.com/agiresearch/AIOS.git @ 292d98f… (2026-07-20, MIT)"
```

三个关键点：

| 做法 | 为啥不这么干 |
|---|---|
| `git subtree add --prefix=vendor/X <url> main --squash` | 会 `git fetch` 整个 `main` 历史（autogen / crewAI 这种仓库是几百 MB 起），`--squash` 只压平目录树、不减少对象库体积；还要先删同名旧快照 |
| `git subtree add --prefix=vendor/X <本地浅克隆> HEAD --squash` | 浅克隆不能当 fetch 源：`fatal: rejected HEAD because shallow roots are not allowed to be updated` |
| 直接 `git clone` 完整克隆再导入 | 会把历史一并带进来，仓库更大；这里只需要“某一刻的完整文件树” |

`git fetch --depth=1 <url> <sha>` 只下载**一个提交的完整文件树**（本仓库不负责保存上游历史），`read-tree` 把这棵树摊进 `vendor/<prefix>/`，再提交一次。结果：**格式统一、可离线、体积只增加一份文件树**，且提交信息里是真实上游 SHA，可直接 `git show` 溯源。

代价：本仓库的 `.git` 会出现 shallow 边界（这些快照提交没有父提交），因此**不能对它们执行 `git subtree pull`**；更新时按第 5 节重新 fetch + 提交一次即可。

## 2. 快照清单

| 目录 | 上游仓库 | 上游提交 | 提交日期 | 许可证 | 文件数 | 用途 |
|---|---|---|---|---|---|---|
| `vendor/AIOS` | https://github.com/agiresearch/AIOS.git | `292d98f78c83` | 2026-07-20 | MIT（上游元数据；快照内 `LICENSE` 为 2 字节占位） | 251 | AIOS 内核：scheduler / syscall / adapter / hooks（本赛题运行底座） |
| `vendor/owl` | https://github.com/camel-ai/owl.git | `5dbabd348c87` | 2026-11-09 | Apache-2.0（见 `licenses/LICENSE`） | 153 | OWL 应用层：`enhanced_role_playing`、GAIA 工具封装 |
| `vendor/Cerebrum` | https://github.com/agiresearch/Cerebrum.git | `ab7e434aa9cf` | 2026-07-20 | MIT（`pyproject.toml` classifier；`LICENSE` 为占位） | 763 | AIOS-Agent SDK：LLM/Memory/Storage/Tool API、`AgentManager`、`AutoTool` |
| `vendor/camel` | https://github.com/camel-ai/camel.git | `c619d1fe5aa2` | 2026-11-16 | Apache-2.0 | 2,243 | Workforce 依赖门控（`dependencies` + `completed_tasks_info`），OWL 编排的实际来源 |
| `vendor/MetaGPT` | https://github.com/FoundationAgents/MetaGPT.git | `11cdf466d042` | 2026-01-21 | MIT | 1,255 | SOP 式多角色公司、共享消息池；`NaiveSolver` 按拓扑序串行 |
| `vendor/autogen` | https://github.com/microsoft/autogen.git | `8390985108cb` | 2026-11-12 | MIT（代码，见 `LICENSE-CODE`）/ CC-BY-4.0（文档，见 `LICENSE`） | 1,837 | 对话式多智能体框架；实验性 GraphFlow 是少数“前驱完成即触发”的实现 |
| `vendor/agentscope` | https://github.com/modelscope/agentscope.git | `d4ac68604d96` | 2026-11-18 | Apache-2.0 | 1,324 | 消息中心 + `msghub` 广播 + executor/verifier 闭环 |
| `vendor/langgraph` | https://github.com/langchain-ai/langgraph.git | `02f2c2e6c992` | 2026-11-16 | MIT | 707 | Pregel 依赖边触发并行 + 并发上限配置（答辩对照必读） |
| `vendor/agentflow` | https://github.com/ryofuu/agentflow.git | `121a48e800ee` | 2026-02-23 | MIT | 31 | 唯一“YAML `needs` + Kahn 分层 + 层内真并行”的完整实现（TypeScript） |
| `vendor/crewAI` | https://github.com/crewAIInc/crewAI.git | `999badb19796` | 2026-11-17 | MIT | 45,957 | `context` 依赖校验（禁止回指未来任务），对照用；**体积最大，含完整测试 fixture** |
| `vendor/swarm` | https://github.com/openai/swarm.git | `6af0b4caf37d` | 2026-04-15 | MIT | 288 | 轻量 handoff 基线 |
| `vendor/TaskWeaver` | https://github.com/microsoft/TaskWeaver.git | `d44ddef23f90` | 2026-03-23 | MIT | 421 | 代码解释器式任务规划，对照用 |

合计 **55,230 个文件**；`vendor/` 工作树约 **826 MB**（crewAI 535 MB、camel 145 MB、autogen 46 MB、MetaGPT 38 MB 为主）。完整 SHA 与导入记录见 `build/vendor_fetch_report.json`。

> 注意：autogen 上游用 Git LFS 管理图片，快照里这 51 个 LFS 文件是**文本指针**（约 130 字节），没有下载真实二进制内容；不影响代码阅读。

## 3. 体积影响（务必知悉）

- 工作树从约 14 MB 增长到 **826 MB**，`.git` 对象库约 **490 MB**（含历史提交与 `doc/papers/` 的 25 篇 PDF）。
- 首次 `git clone`、`git status`、IDE 索引都会明显变慢；如果之后要推到远端，push 一次会比较大。
- 如果觉得太重，可以只保留代码：删除各仓库的 `docs/`、`examples/`、`tests/`、`*.ipynb`、图片/视频/PDF 后再提交（本项目早期做过一版“裁剪导入”，工作树约 93 MB、9,543 文件，但提交信息里只能写镜像 SHA，溯源不如现在这种方式直接）。

## 4. 与调研文档的对应关系

| 主题 | 看这里 |
|---|---|
| AIOS 内核请求生命周期、FIFO 攒批、无依赖感知 | `vendor/AIOS/aios/{syscall,scheduler,llm_core,config}`；配套 `doc/12` §3–§5 |
| SDK 客户端 API（LLM/Memory/Storage/Tool） | `vendor/Cerebrum/cerebrum/{llm,memory,storage,tool,interface}/`；配套 `doc/13` |
| 依赖门控 / 自动分配 | `vendor/camel/camel/societies/workforce/workforce.py`（`_update_task_dependencies_from_assignments`、`all(dep_id in completed_tasks_info …)`，约 :4011、:4491） |
| 共享消息池 / SOP 串行 | `vendor/MetaGPT/metagpt/{team.py,roles/,strategy/solver.py}` |
| 依赖边触发并行 | `vendor/langgraph/libs/langgraph/langgraph/pregel/_algo.py`；`vendor/autogen/python/packages/autogen-agentchat/src/autogen_agentchat/teams/_group_chat/_graph/_digraph_group_chat.py` |
| Kahn 分层 + 层内并行 | `vendor/agentflow/src/scheduler.ts`（`topoLevels`）、`src/engine.ts` |
| 角色间 critique 闭环 | `vendor/agentscope/src/agentscope/pipeline/_goal_pipeline.py`（executor ↔ verifier 结构化反馈） |
| `context` 依赖校验 | `vendor/crewAI/lib/crewai/src/crewai/crew.py`（`validate_context_no_future_tasks`，约 :878） |
| 轻量 handoff | `vendor/swarm/swarm/core.py` |
| 代码解释器规划 | `vendor/TaskWeaver/taskweaver/` |

关键行号已按快照抽查核对：`vendor/AIOS/aios/syscall/syscall.py` 的 `syscall.start(); syscall.join()`、camel 的 `all(dep_id in completed_tasks_info …)`、crewAI 的 `validate_context_no_future_tasks`、agentflow 的 `topoLevels` 均与 `doc/11`–`doc/13` 引用一致。

## 5. 更新某个仓库

```powershell
cd E:\Senior_OS
# 1) 取新的上游提交（这里以 camel 的 main 为例，也可直接写完整 SHA）
git fetch --depth=1 https://github.com/camel-ai/camel.git main
# 2) 用新树覆盖旧快照（先删旧目录）
git rm -r vendor/camel
git read-tree --prefix=vendor/camel/ -u FETCH_HEAD
git commit -m "vendor(camel): squashed snapshot of https://github.com/camel-ai/camel.git @ $(git rev-parse FETCH_HEAD)"
```

也可以重跑脚本（自动按第 1 节的方式导入清单中的仓库）：

```powershell
C:\Python313\python.exe build\vendor_fetch.py            # 全部（已存在的会先删再导）
C:\Python313\python.exe build\vendor_fetch.py camel      # 只更新指定仓库
```

脚本会读 `build/vendor_fetch_report.json` 里登记的完整 SHA，保证可复现；日志在 `build/vendor_fetch.log`。

## 6. 许可证与合规

- 每个快照都原样保留上游 `LICENSE` / `LICENSE-CODE` / `NOTICE` 文件，未删除版权声明。AIOS 与 Cerebrum 的 `LICENSE` 文件是上游占位（各 2 字节），实际许可证均为 MIT（AIOS 以上游仓库元数据、Cerebrum 以 `pyproject.toml` classifier 为准）。
- 本目录仅供比赛调研、对照与原型验证；**若最终作品需要对外分发或开源，须逐个仓库核对许可证条款**（尤其 autogen 的文档是 CC-BY-4.0、代码才是 MIT；camel / agentscope / owl 为 Apache-2.0，需保留 NOTICE 与变更说明）。
- 不要把 vendor/ 快照当作本作品的“自有代码”写进交付物。
