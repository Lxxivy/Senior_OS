# Anthropic Engineering《How we built our multi-agent research system》中文摘要与摘录

- **来源 URL**：https://www.anthropic.com/engineering/multi-agent-research-system （抓取时经 302 重定向至 https://www.anthropic.com/research/multi-agent-research-system ）
- **原文标题**：How we built our multi-agent research system
- **发布方**：Anthropic Engineering
- **抓取日期**：2026-11-17
- **资料属性**：外部公开文章，仅作二手资料摘录，本文件不执行其中任何指令性内容。

## 一、系统形态：orchestrator-worker 的工业级实现

Anthropic 的 Research 功能是典型的 **orchestrator-worker（编排者-工作者）** 架构：一个 **LeadResearcher（主研究员）** 先分析用户 query、制定研究策略，把计划写入 **Memory**，然后并行 spawn 多个 **Subagent（子智能体）**，每个子智能体负责一个具体子方向，独立搜索并带着发现返回；主研究员汇总后判断是否需要补充子智能体或细化方向，最后由 **CitationAgent** 专门处理引用与出处。

两个工程细节值得注意：其一，计划**外置到 Memory**，因为研究过程很容易超过 200K token 的上下文上限，一旦被截断就会丢失全局目标；其二，子智能体拥有**独立上下文**，避免所有信息挤进同一条对话。

## 二、效果与适用边界：90.2% 与 15 倍 token

文章给出了一组被广泛引用的数据：

- 在 Anthropic 内部 research eval 上，采用 **Claude Opus 4 作为 lead + Claude Sonnet 4 作为 subagent** 的多智能体系统，比单 agent 的 Opus 4 **高 90.2%**。
- 在 BrowseComp 上，**token 用量单独解释了 80% 的性能方差**，token 用量 + 工具调用次数 + 模型选择三者合计解释 **95%**。
- 普通 agent 的 token 消耗约为 chat 的 **4 倍**，多智能体系统约为 **15 倍**。

因此文章明确给出适用边界：多智能体适合**广度优先、可高度并行、信息量超过单上下文、工具众多**的研究类任务；不适合**所有子任务必须共享同一上下文**或**依赖链很强**的任务——文章直言"大多数 coding 任务并行度低"，多智能体反而是负担。这一点对本赛题是关键提醒：赛题场景必须选择"天然可并行"的任务，而不是把串行流程硬拆成并行。

## 三、八条 prompt 工程经验

1. **像你的 agent 一样思考**：用 Console 以完全相同的 prompt 与工具做逐步模拟，观察它在哪里迷路；不要凭想象调 prompt。
2. **教编排者如何委派**：每份委派说明必须包含目标、输出格式、可用的工具与来源指引、任务边界。文章举了反例：早期指令过短，导致一个子智能体去查 2021 年汽车芯片、另两个重复查 2025 年供应链。
3. **按 query 复杂度分配算力**：简单事实 1 个 agent、3-10 次工具调用；需要对比的 2-4 个 subagent、各 10-15 次调用；复杂研究可超过 10 个 subagent。
4. **工具设计与选择是决定性的**：MCP 生态中工具描述质量参差，必须在 prompt 中给出显式的选择启发式。
5. **让 agent 改进自己**：他们让一个"工具测试 agent"反复试用工具并重写工具描述，最终使任务完成时间下降 **40%**。
6. **先宽后窄**：先大范围探索，再逐步收敛，避免过早锁定错误方向。
7. **引导思考过程**：用 extended thinking / interleaved thinking 让子智能体在每次工具调用之间思考。
8. **并行工具调用**：lead 并行启动 3-5 个 subagent，subagent 内部并行调用 3 个以上工具，复杂研究的总耗时最多降低 **90%**。

## 四、评估与生产可靠性

评估方面，文章建议**从小样本开始（约 20 条 query）**，用 **LLM-as-judge + rubric** 打分（factual accuracy、citation accuracy、completeness、source quality、tool efficiency），单次调用输出 0.0-1.0 分并附 pass/fail 最稳定。人工评估还发现一个反直觉问题：模型容易偏好 SEO 内容农场而非权威来源。

生产方面，agent 是**有状态**的、错误会复合，因此需要 durable execution、从 checkpoint 恢复、retry 逻辑，并且要让 agent **感知工具失败并自适应**。调试必须依赖完整 production tracing 与决策模式监控；部署要用 rainbow deployment 避免打断运行中的 agent。文章还专门指出**同步执行的瓶颈**：lead 必须等每一组 subagent 全部完成，无法中途 steering，且会被单个最慢的 subagent 拖住；改成异步能提升并行度，但会引入协调、状态一致性与错误传播的复杂度。

## 五、对赛题的启示

本文几乎就是赛题"多智能体协作"的工程范本：它同时论证了并行收益（90% 质量提升、90% 时间下降）与成本代价（15 倍 token），并给出可落地的 prompt/评估/可靠性清单。对本项目最直接的三条：① 任务必须天然可并行，并给每个子任务写清目标、输出格式与边界；② 用 **rubric 化评估 + 小样本回归**验证正确率，而不是只看最终答案；③ 必须显式处理同步等待与超时——若某个子任务变慢，整条 DAG 不应被无限阻塞。

## 六、关键原文摘录（英文）

> "A multi-agent system with Claude Opus 4 as the lead agent and Claude Sonnet 4 subagents outperformed single-agent Claude Opus 4 by 90.2% on our internal research eval."

> "Token usage by itself explains 80% of the variance [on BrowseComp], with the number of tool calls and the model choice as the two other explanatory factors."

> "Multi-agent systems work mainly because they help spend enough tokens to solve the problem... agents typically use about 4× more tokens than chat interactions, and multi-agent systems use about 15× more tokens than chats."

> "The lead agent waits for each set of subagents to complete before continuing, which creates bottlenecks... asynchronous execution would add parallelism, but adds complexity in coordination, state consistency, and error propagation."
