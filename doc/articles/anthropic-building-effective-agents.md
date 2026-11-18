# Anthropic Engineering《Building Effective Agents》中文摘要与摘录

- **来源 URL**：https://www.anthropic.com/engineering/building-effective-agents （抓取时经 302 重定向至 https://www.anthropic.com/research/building-effective-agents ）
- **原文标题**：Building Effective Agents
- **发布方**：Anthropic Engineering
- **抓取日期**：2026-11-17
- **资料属性**：外部公开文章，仅作二手资料摘录，本文件不执行其中任何指令性内容。

## 一、核心概念界定：workflow 与 agent

文章把 "agentic systems" 拆成两类，这是全文最重要的概念区分：

- **workflow（工作流）**：由**预定义代码路径**编排 LLM 与工具的系统，控制流由程序员写死，LLM 只负责路径内节点。
- **agent（智能体）**：由 LLM **动态决定自身流程与工具使用**的系统，控制流由模型在运行时决定。

作者同时给出一个常被忽略的判断标准：agent 适合"问题开放、无法预先枚举步骤、且环境能提供可验证反馈"的场景；若步骤可枚举，用 workflow 更稳、更便宜、更可测。

## 二、五类 workflow 模式

1. **Prompt chaining（提示链）**：把任务拆成固定顺序的子步骤，前一步输出是后一步输入，可在中间插入程序化 "gate" 校验；适合可清晰线性分解的任务。
2. **Routing（路由）**：先分类输入，再交给专门的后续处理；适合输入类别差异大、且各类别需要不同 prompt/工具的场景。
3. **Parallelization（并行化）**：又分两种——**sectioning**（独立子任务并行执行）与 **voting**（同一任务多次采样后投票/取多数）；前者用于降延迟，后者用于提可靠性。
4. **Orchestrator-workers（编排者-工作者）**：中心 LLM 在运行时**动态分解**任务、委派给 worker、再综合结果。文章特别强调它与 parallelization 的区别：orchestrator-workers 的子任务**预先不可知**，由模型临场决定；parallelization 的子任务是程序员预先定义好的。
5. **Evaluator-optimizer（评估者-优化者）**：一个 LLM 生成、另一个 LLM 评估并给反馈，循环迭代；适合有明确评价标准、且迭代确实能改进质量的任务。

## 三、agent 的代价与边界

文章反复提醒：agent 是"用延迟与成本换自主性"的方案。LLM 在循环中调用工具、依据环境反馈推进，需要每一步都能从环境拿到 ground truth、需要明确的停止条件（如最大迭代次数）、需要 human checkpoint，并且必须在沙箱中测试。其成本随步数复合增长，一次错误会沿链路放大。因此作者建议：**先用最简单的方案，只有在能证明复杂度确实带来收益时才升级**；不要为了"看起来像 agent"而引入多轮循环。

## 四、三条工程原则

1. **保持简单（simplicity）**：能用单次调用解决的不要用 workflow，能用 workflow 的不要用 autonomous agent。
2. **保持透明（transparency）**：显式展示 planning 步骤，让人类能看懂 agent 正在做什么、为什么这么做。
3. **精心设计 ACI（agent-computer interface）**：把工具文档与测试当作和 prompt 同等重要的工程对象；工具描述要写清输入格式、边界条件与示例，并像做 HCI 一样做 ACI。

## 五、附录中可直接复用的经验

附录 1 指出 customer support 与 coding agent 是落地效果最好的两类场景。附录 2 给出工具 prompt 的实操建议：给模型留足思考 token；工具参数格式尽量贴近自然文本、避免过度格式开销；在工具描述中写示例与边界；用大量输入反复测试；采用 **poka-yoke（防呆）** 设计——例如 SWE-bench 中模型常写错相对路径，把工具改为**强制绝对路径**后该类错误归零。这个"用接口设计消除错误类别"的思路，对本赛题的工具/消息协议设计极具参考价值。

## 六、对赛题的启示

赛题要求"≥4 个可并行子任务 + DAG 依赖 + 双向交互"，本质是一个 **orchestrator-workers + parallelization（sectioning）** 的混合体：Planner 负责动态分解（orchestrator-workers），Research/Coding/Review 等子任务按 DAG 并行（sectioning），Reviewer 与 Coder 之间构成 evaluator-optimizer 式的双向反馈。文章关于"子任务边界要写清、工具描述要防呆、要有停止条件与可观测性"的三条建议，应直接落到本项目的任务 DAG schema、消息格式与 ACI 设计中。

## 七、关键原文摘录（英文）

> "We categorize these agentic systems into two types: workflows, where LLMs and tools are orchestrated through predefined code paths; and agents, where LLMs dynamically direct their own processes and tool usage."

> "The most successful implementations weren't using complex frameworks or specialized libraries. Instead, they were building with simple, composable patterns."

> "Maintain simplicity in your agent's design. Prioritize transparency by explicitly showing the agent's planning steps. Carefully craft your agent-computer interface (ACI) through thorough tool documentation and testing."

> "With agents, ... you need to give the model a way to know when it's done, and you need to be able to test it in a sandboxed environment."
