---
tags:
  - AI 基础
---

# 为什么模型会胡说

<div markdown="1" style="position:relative;overflow:hidden;border:1px solid rgba(255,112,67,0.28);border-radius:1rem;padding:1.25rem 1.35rem;margin:0.8rem 0 1.5rem;background:linear-gradient(135deg,rgba(255,112,67,0.14),rgba(63,81,181,0.08) 46%,rgba(0,188,212,0.10));box-shadow:0 0.65rem 1.8rem rgba(0,0,0,0.10);">
<div style="position:absolute;right:-3.8rem;top:-4.2rem;width:12rem;height:12rem;border-radius:50%;background:radial-gradient(circle,rgba(255,112,67,0.26),rgba(255,112,67,0));"></div>
<div style="position:absolute;left:-4rem;bottom:-5rem;width:14rem;height:14rem;border-radius:50%;background:radial-gradient(circle,rgba(33,150,243,0.18),rgba(33,150,243,0));"></div>
<div style="position:relative;z-index:1;">
<span style="display:inline-block;padding:0.18rem 0.55rem;border-radius:999px;background:rgba(255,112,67,0.16);color:#e65100;font-size:0.78rem;font-weight:700;letter-spacing:0.02em;">AI 基础 · 第 10 站</span>

<strong>AI 幻觉</strong>指模型生成看起来合理、语气很自信，实际却错误、虚构、无法验证或与材料冲突的内容。它最麻烦的地方在于：错得很像真的。

<div markdown="1" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(9rem,1fr));gap:0.75rem;margin-top:1rem;">
<div style="padding:0.8rem;border-radius:0.75rem;background:var(--md-default-bg-color);border:1px solid var(--md-default-fg-color--lightest);">
<strong>形式可信</strong><br><span style="color:var(--md-default-fg-color--light);font-size:0.9rem;">语言流畅、结构完整</span>
</div>
<div style="padding:0.8rem;border-radius:0.75rem;background:var(--md-default-bg-color);border:1px solid var(--md-default-fg-color--lightest);">
<strong>事实缺口</strong><br><span style="color:var(--md-default-fg-color--light);font-size:0.9rem;">来源不足、证据缺失</span>
</div>
<div style="padding:0.8rem;border-radius:0.75rem;background:var(--md-default-bg-color);border:1px solid var(--md-default-fg-color--lightest);">
<strong>需要核查</strong><br><span style="color:var(--md-default-fg-color--light);font-size:0.9rem;">关键结论回到来源</span>
</div>
</div>
</div>
</div>

> 这一页讲清楚：AI 幻觉是什么，它为什么会出现，哪些场景最容易出问题，以及普通用户和开发者怎么降低风险。

## 这章解决什么问题

你可能遇到过这些情况：

- 模型给你列了 5 篇论文，标题、作者、期刊都很完整，结果一查根本不存在；
- 它总结一篇文章时，把原文没有说过的结论加了进去；
- 它写代码时调用了一个看起来很像真的 API，实际库里没有这个函数；
- 它说「根据你刚才提到的内容」，可你根本没说过那句话；
- 它回答一个过期问题时，语气非常确定，内容却停留在旧版本；
- 它拿检索结果回答问题，却把搜索结果里的噪音当成事实。

这些都可以放进「AI 幻觉」这个大篮子里。

可以先记一句人话：**幻觉不是模型崩溃，它更像模型把缺失的信息补成了一段像样的文本。**

## 什么是 AI 幻觉

学术界常用的定义很接近。Huang 等人在综述论文 [A Survey on Hallucination in Large Language Models](https://arxiv.org/abs/2311.05232) 里把大语言模型幻觉描述为生成 **plausible yet nonfactual content**，也就是「看似合理但不符合事实的内容」。

HaluEval 论文 [HaluEval: A Large-Scale Hallucination Evaluation Benchmark for Large Language Models](https://arxiv.org/abs/2305.11747) 给了另一个很实用的判断：如果模型生成的内容**与来源冲突**，或者**无法被事实知识验证**，就可能是幻觉。

放到日常使用里，可以拆成三层：

| 层次 | 怎么判断 | 例子 |
| --- | --- | --- |
| 与现实冲突 | 现实世界里查不到或事实相反 | 编造不存在的公司收购 |
| 与材料冲突 | 用户给的文档里没有，甚至相反 | 总结合同时新增了一条付款条款 |
| 无法验证 | 看起来合理，但找不到来源 | 捏造论文、链接、采访原话 |

所以，幻觉不等于「回答不好」。有些回答写得很漂亮，错得也很完整。

## 为什么幻觉看起来那么真

LLM 每一步都在根据当前上下文预测下一个 token。上一章讲过，模型会先计算候选 token 的概率，再通过 temperature、top-k、top-p 等策略选出下一个 token。

这套机制很擅长生成自然语言。

问题也在这里。

模型学到的是大量文本里的表达模式、事实关联、格式习惯和推理痕迹。它知道一篇论文引用「通常长什么样」，知道新闻稿「通常怎么写」，知道 Python 文档「通常有哪些字段」。当它缺少真实依据时，仍然可能沿着这些格式继续补全。

先看一张链路图。

<div markdown="1" style="overflow-x:auto;padding:0.5rem 0 0.8rem;margin:1rem 0;">
<div markdown="1" style="min-width:1080px;">

~~~mermaid
flowchart LR
    A[用户问题] --> B[当前上下文]
    B --> C{上下文里有足够证据吗?}
    C -->|有| D[基于材料组织回答]
    C -->|没有| E[根据训练中学到的模式补全]
    E --> F{输出是否经过核查?}
    D --> F
    F -->|有| G[更可信的答案]
    F -->|没有| H[可能出现幻觉]
~~~

</div>
</div>

幻觉的迷惑性来自两点。

第一，模型的语言能力很强。它可以把错误内容写得像报告、像论文、像律师函、像 API 文档。

第二，模型默认倾向于完成任务。用户问了一个问题，它通常会努力给答案。训练和产品体验都在鼓励「有用、完整、自然」的回答。遇到证据不足时，如果系统没有明确允许它停下来，它就可能继续生成。

Anthropic 在 [Reduce hallucinations](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations) 文档里给的第一条建议很直接：明确允许模型说「I don't know」。这条建议背后有个朴素逻辑：模型需要知道，承认资料不足也是合格输出。

## 幻觉最常见的类型

入门阶段不用背复杂分类，先抓住这些高频类型。

| 类型 | 表现 | 常见场景 |
| --- | --- | --- |
| 事实幻觉 | 编造人物、事件、机构、产品能力 | 问答、科普、新闻总结 |
| 引用幻觉 | 生成不存在的论文、链接、法条、页码 | 学术写作、报告、法律检索 |
| 数字幻觉 | 数字、比例、年份、排名错了 | 财报总结、行业分析、参数对比 |
| 材料幻觉 | 总结时加入原文没有的信息 | PDF 总结、会议纪要、合同审查 |
| 代码幻觉 | 编造函数、参数、包名、配置项 | 编程助手、API 接入 |
| 推理幻觉 | 步骤看着顺，关键一步偷换条件 | 数学、逻辑题、策略分析 |
| 记忆幻觉 | 假装记得用户说过的话 | 长对话、跨会话记忆 |
| 多模态幻觉 | 错认图片中的物体、关系或文字 | 图像理解、视频理解 |

Rawte 等人在 EMNLP 2023 论文 [The Troubling Emergence of Hallucination in Large Language Models](https://aclanthology.org/2023.emnlp-main.155/) 里做过更细的分类，还把数字、地理、时间、虚构实体等错误拆开评估。对普通用户来说，先知道「它会在哪些地方编」更重要。

## 幻觉从哪里来

幻觉没有单一原因。它通常是几类因素叠在一起。

### 1. 训练数据里本来就有错

模型从大规模文本里学习语言，互联网上有事实，也有谣言、过时资料、误解和重复转载。

TruthfulQA 论文 [TruthfulQA: Measuring How Models Mimic Human Falsehoods](https://arxiv.org/abs/2109.07958) 专门测试模型会不会模仿人类常见错误信念。论文包含 817 个问题，覆盖 38 个类别。实验发现，最佳模型只在 58% 的问题上回答真实，人类表现约为 94%；更大的模型在这个基准上也不一定更真实。

这个结果很刺耳。

如果训练文本里有大量流行误解，模型学得越好，可能越会复现这些「大家都这么说」的错话。

### 2. 模型没有直接观测世界

你问「现在深圳天气怎么样」，裸模型不能自己看窗外，也不能天然访问实时天气。它只能根据上下文和参数里的知识生成回答。除非产品接入天气 API、搜索或定位工具。

所以，对实时信息、私有信息、刚发生的事件，模型很容易靠旧知识或模式猜。

### 3. 上下文缺材料

如果你让模型「总结这份报告的风险」，但没有给报告全文，它只能根据报告标题、你的描述和常见报告结构推测。

推测可能有帮助，也可能变成幻觉。

Prompt 越像在要求它必须交付完整答案，模型越容易把缺口补上。

### 4. 长上下文里漏掉关键信息

材料放进上下文，也不代表模型一定抓住。前一章提到过 [Lost in the Middle](https://arxiv.org/abs/2307.03172)：相关信息放在上下文开头或结尾时，模型表现通常更好；藏在长上下文中间时，模型更容易漏掉。

这就是为什么你上传一大份 PDF，模型仍然可能漏掉第 87 页那条限制。

### 5. 采样参数把低概率候选放进来了

高 temperature、宽 top-p、宽 top-k 会让输出更发散。写故事时这很有用，做事实核查时就可能添乱。

但低温也不能彻底解决幻觉。低温可能让模型稳定地输出同一个错误答案。上一章说过，采样参数只能控制「怎么选 token」，不能替你验证事实。

### 6. RAG 检索也会出错

RAG 能降低幻觉，但它不是免疫盾。

Lewis 等人在 [Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks](https://arxiv.org/abs/2005.11401) 里提出把模型参数中的知识和外部可检索知识结合起来，让模型能基于 Wikipedia 检索结果生成更具体、更事实化的文本。

这条路很重要。

可检索结果如果不准、切块太碎、召回漏了、排序错了、网页里有噪音，模型仍然可能把错误材料组织成更像真的答案。Huang 等人的综述也专门提到，检索增强 LLM 在对抗幻觉时仍有局限。

## 幻觉为什么危险

NIST 在生成式 AI 风险画像 [NIST AI 600-1](https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf) 中把这类风险称为 **confabulation**。这个词很贴切，它强调模型会产出流畅、自信、看起来完整的虚构内容。

幻觉的风险和场景强相关。

| 场景 | 幻觉影响 |
| --- | --- |
| 写诗、脑暴、标题 | 可能只是风格跑偏 |
| 普通资料总结 | 可能误导学习和判断 |
| 企业知识库问答 | 可能污染内部决策 |
| 代码生成 | 可能引入 bug 或安全漏洞 |
| 医疗、法律、金融建议 | 可能造成真实损害 |
| 新闻、公告、公开传播 | 可能破坏信息完整性 |
| Agent 自动操作 | 可能把错误判断变成真实动作 |

OWASP 的 [Top 10 for Large Language Model Applications](https://owasp.org/www-project-top-10-for-large-language-model-applications/) 里有一项叫 **Overreliance**，可以理解成过度依赖模型输出。它提醒开发者和用户：LLM 输出如果未经批判性评估，可能带来错误决策、安全漏洞和法律责任。

这里要把「内容生成」和「行动执行」分开看。

模型写错一句话，影响有限。模型拿着错误判断去发邮件、改数据库、下订单、删文件，风险就完全变了。这也是 OWASP 另一个风险 **Excessive Agency** 关注的地方：不要给模型过多未经约束的自主行动权限。

## 如何降低 AI 幻觉

先说清楚：**幻觉只能降低，很难承诺彻底消灭。**

比较靠谱的做法，是把「生成」改造成「有证据的生成」。

<div markdown="1" style="overflow-x:auto;padding:0.5rem 0 0.8rem;margin:1rem 0;">
<div markdown="1" style="min-width:1120px;">

~~~mermaid
flowchart LR
    A[明确问题] --> B[提供可靠材料]
    B --> C[要求先提取证据]
    C --> D[基于证据回答]
    D --> E[标注来源]
    E --> F[检查无依据结论]
    F --> G[人工或程序复核]
~~~

</div>
</div>

### 普通用户可以这样做

| 做法 | Prompt 写法 | 作用 |
| --- | --- | --- |
| 允许它停下来 | 如果资料不足，请说「无法确认」 | 减少硬猜 |
| 限定来源 | 只基于我提供的材料回答 | 避免混入外部印象 |
| 先要证据 | 先列出原文引用，再回答 | 让结论有支点 |
| 要求标注不确定 | 把无法确认的信息单独列出 | 防止混进正文 |
| 降低温度 | 事实任务用低 temperature | 让输出更稳 |
| 多跑几次对比 | 同一问题生成 3 次，看差异 | 找出不稳定点 |
| 关键内容人工核查 | 对数字、引用、结论逐条查源 | 防止错用 |

一个好用的模板：

<pre><code>请只基于我提供的材料回答问题。

回答前先提取与问题相关的原文证据。
如果材料里没有答案，请说「材料中没有足够信息」，不要猜测。

输出格式：
1. 相关证据
2. 基于证据的回答
3. 无法确认的信息
4. 需要我继续核查的点</code></pre>

这个模板不神奇，只是把模型从「自由发挥」拉回「按材料办事」。

### 开发者可以这样做

如果你在做 AI 应用，降低幻觉要靠系统设计，不能只靠一句提示词。

| 层面 | 做法 | 适合场景 |
| --- | --- | --- |
| 数据 | 建可靠知识库，清理过期和重复资料 | 企业问答、客服 |
| 检索 | 评估召回率、重排效果和引用命中 | RAG 系统 |
| 生成 | 限制回答范围，要求引用证据 | 事实问答 |
| 输出 | 做格式校验、来源校验、事实核查 | 报告、公告、代码 |
| 权限 | 高风险工具调用前人工确认 | Agent、自动化工作流 |
| 评测 | 建幻觉测试集和回归测试 | 产品迭代 |
| 监控 | 记录用户反馈和错误案例 | 线上系统 |

Google Vertex AI 的 [Grounding 文档](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/grounding/overview?hl=zh-cn) 把 grounding 定义为把模型输出连接到可验证信息源的能力。它的价值很明确：减少模型生成不真实内容，把回答固定到数据源，并通过来源链接提高可审核性。

Anthropic 的 [Citations 文档](https://platform.claude.com/docs/en/build-with-claude/citations) 也体现了同一思路：把回答里的具体主张绑定到原始文档中的具体位置，用户可以回到原文验证。

OpenAI 的 [Text generation 文档](https://developers.openai.com/api/docs/guides/text) 则更偏工程实践：用 `developer` 消息放高优先级规则，用 Structured Outputs 约束 JSON，用 evals 评估提示词行为，用固定模型版本减少生产环境漂移。

## 如何评测幻觉

幻觉评测大概分三类。

| 评测对象 | 怎么测 | 代表资源 |
| --- | --- | --- |
| 回答是否真实 | 用问题集测试模型是否输出事实答案 | [TruthfulQA](https://arxiv.org/abs/2109.07958) |
| 是否识别幻觉 | 给模型看文本，让它判断有没有幻觉 | [HaluEval](https://arxiv.org/abs/2305.11747) |
| 生成内容是否自洽 | 同一问题多次采样，比较事实是否一致 | [SelfCheckGPT](https://arxiv.org/abs/2303.08896) |

SelfCheckGPT 的想法很有意思。它不依赖外部数据库，也不需要看模型内部概率。它让同一个黑盒模型对同一问题多次生成答案，然后比较这些答案是否互相支持。论文的核心假设是：模型真正掌握的事实，在多次采样中更容易保持一致；幻觉内容更容易出现分歧和矛盾。

这对普通用户也有启发。

当你问一个重要问题，模型第一次答得很自信，不妨换个问法再问一次，再让它审查前一轮回答。多次输出互相打架的地方，大概率需要人工查源。

## 常见误区

??? warning "误区 1：AI 幻觉就是模型撒谎"

    撒谎需要意图。模型没有人的动机，它是在根据上下文和概率生成文本。
    
    更准确的理解是：模型在证据不足、目标不清或检索有噪音时，仍然把答案补全成了自然语言。

??? warning "误区 2：模型越大，幻觉越少"

    模型变大通常会提升很多能力，但真实性不一定线性提升。TruthfulQA 的早期实验就发现，更大的模型可能更会模仿训练数据中的流行错误说法。
    
    对事实任务来说，模型能力、训练目标、对齐方式、检索质量和核查流程都重要。

??? warning "误区 3：接入 RAG 后就不会幻觉"

    RAG 能显著改善事实任务，但检索结果可能错，知识库可能旧，切块可能丢上下文，模型也可能没有忠实使用证据。
    
    好的 RAG 系统需要评估检索、引用和生成三段链路。

??? warning "误区 4：temperature 调成 0 就能消灭幻觉"

    低温让输出更稳定，但稳定不等于正确。
    
    如果模型缺少事实依据，低温可能只是让它更稳定地重复同一个错误。

??? warning "误区 5：有引用就一定可信"

    引用也可能被编造，或者引用存在但无法支撑结论。
    
    真正要看的是：来源是否存在、来源是否权威、引用片段是否真的支持那句话。

## 最小实验：亲手观察一次幻觉

你可以拿常用模型做一个小实验。

提示词：

<pre><code>请列出 5 篇关于「AI 幻觉和中文科普写作」的学术论文，包含标题、作者、年份、DOI，并总结每篇论文结论。</code></pre>

然后做三件事：

1. 复制每个 DOI 去搜索；
2. 检查论文标题和作者是否匹配；
3. 看总结内容是否真的来自论文。

你很可能会发现，有些条目格式很完整，但查不到。

这就是引用幻觉最典型的样子。

再把提示词改成：

<pre><code>请只列出你能提供可靠来源链接的论文。
如果找不到足够论文，请直接说数量不足。
每条必须包含可访问链接，并说明你为什么认为它相关。</code></pre>

对比两次输出，你会更直观地看到：给模型「可以不凑够数量」的权限，幻觉会少很多。

## 练习题 / 小实验

??? question "练习 1：识别幻觉类型"

    判断下面输出可能属于哪类幻觉：
    
    <div class="highlight"><pre><code>根据《2024 中国大模型安全白皮书》第 17 页，所有主流模型的幻觉率都低于 1%。</code></pre></div>
    
    ??? done "参考思路"
    
        先查这份白皮书是否存在，再查第 17 页有没有这句话。若来源不存在或页码不匹配，就是引用幻觉。若来源存在但结论不支持这句话，就是材料幻觉或事实幻觉。

??? question "练习 2：改写提示词"

    把下面提示词改得更不容易诱发幻觉：
    
    <div class="highlight"><pre><code>帮我总结一下这家公司过去三年的融资情况，要详细一点。</code></pre></div>
    
    ??? done "参考思路"
    
        可以改成：请只基于我提供的材料总结这家公司过去三年的融资情况。每一笔融资都要列出日期、金额、投资方和来源链接。材料里没有的信息请标注「未找到」，不要补全。

??? question "练习 3：检查 RAG 回答"

    找一个带联网或知识库功能的 AI 产品，问它一个事实问题。要求它给出处，然后逐条打开来源。
    
    观察：
    
    - 来源是否能打开？
    - 来源是否真的包含答案？
    - 模型有没有把来源里的信息改写错？
    - 有没有把多个来源的内容混在一起？

??? question "练习 4：多次采样对比"

    用同一个问题连续问模型 3 次，或者让它生成 3 个候选答案。
    
    如果三个版本的关键事实不一致，把这些事实列出来逐条查证。
    
    ??? done "参考思路"
    
        多次输出都一致，也不能直接证明正确；但多次输出互相矛盾，基本可以说明模型对这部分信息不稳定，需要查源。

## 小结

这章你只需要带走五句话：

- **AI 幻觉是看似合理但事实不可靠的生成内容。**
- **它常见于事实、引用、数字、代码、材料总结、推理和记忆场景。**
- **幻觉来自训练数据、上下文缺口、生成机制、采样参数、检索噪音和使用方式的叠加。**
- **RAG、引用、grounding、低温、结构化输出和评测都能降低风险，但不能保证归零。**
- **关键事实要回到来源，关键操作要有人类确认。**

学会识别幻觉之后，你看 AI 回答会多一层习惯：先看它说得顺不顺，再看它有没有证据。

后者更重要。

## 下一步

<div markdown="1" style="border:1px solid var(--md-default-fg-color--lightest);border-left:4px solid var(--md-accent-fg-color);border-radius:0.85rem;padding:1rem 1.1rem;margin:0.9rem 0;background:linear-gradient(135deg,var(--md-code-bg-color),rgba(255,112,67,0.06));">

理解了模型为什么会胡说之后，下一站建议进入 Prompt 章节：

<a href="../../prompt/" style="display:block;margin-top:0.75rem;padding:0.85rem 1rem;border-radius:0.65rem;background:var(--md-default-bg-color);text-decoration:none;border:1px solid var(--md-default-fg-color--lightest);">
  <strong>Prompt 总览 →</strong><br>
  <span style="color:var(--md-default-fg-color--light);font-size:0.92rem;">开始学习怎么把任务、材料、约束和输出格式说清楚。</span>
</a>

</div>
