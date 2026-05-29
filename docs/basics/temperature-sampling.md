---
tags:
  - AI 基础
---

# 温度与采样参数

<div markdown="1" style="position:relative;overflow:hidden;border:1px solid rgba(255,112,67,0.28);border-radius:1rem;padding:1.25rem 1.35rem;margin:0.8rem 0 1.5rem;background:linear-gradient(135deg,rgba(255,112,67,0.14),rgba(63,81,181,0.08) 46%,rgba(0,188,212,0.10));box-shadow:0 0.65rem 1.8rem rgba(0,0,0,0.10);">
<div style="position:absolute;right:-3.8rem;top:-4.2rem;width:12rem;height:12rem;border-radius:50%;background:radial-gradient(circle,rgba(255,112,67,0.26),rgba(255,112,67,0));"></div>
<div style="position:absolute;left:-4rem;bottom:-5rem;width:14rem;height:14rem;border-radius:50%;background:radial-gradient(circle,rgba(33,150,243,0.18),rgba(33,150,243,0));"></div>
<div style="position:relative;z-index:1;">
<span style="display:inline-block;padding:0.18rem 0.55rem;border-radius:999px;background:rgba(255,112,67,0.16);color:#e65100;font-size:0.78rem;font-weight:700;letter-spacing:0.02em;">AI 基础 · 第 9 站</span>

<strong>温度、Top-k、Top-p</strong>决定模型从候选 token 里怎么选下一个 token。它们不负责增加知识，负责控制输出时的随机性、稳定性和多样性。

<div markdown="1" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(9rem,1fr));gap:0.75rem;margin-top:1rem;">
<div style="padding:0.8rem;border-radius:0.75rem;background:var(--md-default-bg-color);border:1px solid var(--md-default-fg-color--lightest);">
<strong>Temperature</strong><br><span style="color:var(--md-default-fg-color--light);font-size:0.9rem;">把概率分布调尖或调平</span>
</div>
<div style="padding:0.8rem;border-radius:0.75rem;background:var(--md-default-bg-color);border:1px solid var(--md-default-fg-color--lightest);">
<strong>Top-k</strong><br><span style="color:var(--md-default-fg-color--light);font-size:0.9rem;">只看前 k 个候选</span>
</div>
<div style="padding:0.8rem;border-radius:0.75rem;background:var(--md-default-bg-color);border:1px solid var(--md-default-fg-color--lightest);">
<strong>Top-p</strong><br><span style="color:var(--md-default-fg-color--light);font-size:0.9rem;">只看累计概率达到 p 的候选池</span>
</div>
</div>
</div>
</div>

> 这一页讲清楚：为什么同一个问题会有不同回答，temperature、top-k、top-p 到底在改什么，以及新手怎么按任务调参数。

## 这章解决什么问题

你可能遇到过这些情况：

- 同一个问题问两次，答案细节变了；
- 写代码时，模型一会儿给这个函数名，一会儿给另一个函数名；
- 让它写标题，低温很稳但没灵气，高温很有趣但偶尔跑飞；
- API 里有 temperature、top_p、top_k、seed、frequency_penalty，一排旋钮看着很吓人；
- 你把 temperature 调成 0，以为输出会 100% 一样，结果偶尔还有差异。

这些都和**解码策略（decoding strategy）**有关。

模型每次生成下一个 token 时，会先给大量候选 token 打分，再把分数变成概率。解码策略负责回答一个很具体的问题：**下一步到底选谁？**

先看整条链路。

<div markdown="1" style="overflow-x:auto;padding:0.5rem 0 0.8rem;margin:1rem 0;">
<div markdown="1" style="min-width:1120px;">

~~~mermaid
flowchart LR
    A[当前上下文<br/>Prompt + 历史 + 材料] --> B[模型计算下一个 token 的 logits]
    B --> C[Temperature 调整分布]
    C --> D[Top-k / Top-p 截断候选池]
    D --> E[惩罚项调整重复倾向]
    E --> F[按策略选择或采样]
    F --> G[生成一个 token]
    G --> H{是否结束?}
    H -->|否| A
    H -->|是| I[得到完整回答]
~~~

</div>
</div>

可以先记一句人话：**Prompt 决定模型往哪儿走，采样参数决定它走得稳不稳、散不散。**

如果 Prompt 含糊，调参数救不了方向。参数能做的是把输出从「很保守」推到「更发散」，或者从「发散过头」拉回「更稳定」。

## 模型生成文字时，到底在选什么

LLM 是一类自回归语言模型。它每次只做一件事：根据当前上下文预测下一个 token。

在 Hugging Face 的 [generation strategies 文档](https://huggingface.co/docs/transformers/main/en/generation_strategies)里，decoding strategy 被定义为决定模型如何选择下一个生成 token 的规则。最简单的规则叫 **Greedy Search（贪心搜索）**：每一步都选概率最高的 token。

这听起来很合理。

问题也从这里开始。

贪心每一步都选最可能的词，短答案通常很稳，长文本却容易变得机械、重复。Hugging Face 文档里直接提醒：greedy search 适合较短、创意优先级不高的任务，生成长序列时可能开始重复。Hugging Face 的经典文章 [How to generate text](https://huggingface.co/blog/how-to-generate) 也展示过 GPT-2 生成时反复出现同一句话的例子。

这就是采样参数存在的原因。它们让模型不要只盯着概率最高的那个 token，而是在一个可控范围内保留变化。

## logits、softmax 和概率分布

模型不会一开始就吐出「下一个词概率 68%」这种东西。它先输出一组原始分数，常叫 **logits**。

logits 可以理解成模型对每个候选 token 的偏好分。分数越高，模型越想选它。接着系统会用 **softmax** 把这些分数变成概率。

公式长这样：

<div class="arithmatex">
\[
P(x_i)=\frac{e^{z_i}}{\sum_j e^{z_j}}
\]
</div>

这里的 $z_i$ 是第 $i$ 个 token 的 logit。

Temperature 会插在 softmax 前面：

<div class="arithmatex">
\[
P(x_i)=\frac{e^{z_i/T}}{\sum_j e^{z_j/T}}
\]
</div>

$T$ 就是 temperature。

<div markdown="1" style="overflow-x:auto;padding:0.5rem 0 0.8rem;margin:1rem 0;">
<div markdown="1" style="min-width:980px;">

~~~mermaid
flowchart LR
    A[模型输出原始分数<br/>logits] --> B[除以 Temperature<br/>z / T]
    B --> C[softmax]
    C --> D[概率分布]
    D --> E[采样或选择下一个 token]
~~~

</div>
</div>

- **T < 1**：高分 token 更突出，概率分布更尖，输出更稳。
- **T = 1**：保持模型原始分布。
- **T > 1**：不同候选之间差距变小，概率分布更平，输出更随机。

这也是为什么温度经常被叫做「创意旋钮」。温度调高后，低概率 token 有更多机会被选中，回答会更有变化。温度调低后，模型更愿意走最安全的路线。

## 用一个小例子看温度变化

假设模型正在补全这句话：

> The mouse ate the ____

模型原始预测大概是：

| 候选 token | T = 1 时的概率 | 低温时的倾向 | 高温时的倾向 |
| --- | ---: | --- | --- |
| cheese | 68% | 几乎总选它 | 仍然常见 |
| crumb | 25% | 机会变小 | 机会变大 |
| cable | 5.6% | 基本出局 | 偶尔出现 |
| moon | 0.5% | 基本出局 | 极少数时候冒出来 |

低温时，模型大概率写「老鼠吃奶酪」。

高温时，模型可能写「老鼠吃月亮」。这可能是诗，也可能是胡说。

这里没有绝对好坏，只有任务匹配。你让模型写 JSON 配置，月亮没有用。你让模型写儿童诗，月亮可能很好。

## Temperature：控制随机性，不控制事实性

Anthropic 的 [Messages API 文档](https://platform.claude.com/docs/en/api/messages)把 `temperature` 描述为注入回答中的随机性，范围是 `0.0` 到 `1.0`，默认值是 `1.0`。文档建议，分析类和多选题任务可以靠近 `0.0`，创意和生成类任务可以靠近 `1.0`。

Google Vertex AI 的 [Gemini 推理参数文档](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/model-reference/inference?hl=zh-cn)也给了类似解释：temperature 控制 token 选择的随机性，低值适合更确定、更少开放性的回答，高值会让回答更多样。文档里 Gemini 2.0 Flash / Flash-Lite 的 temperature 范围是 `0.0 - 2.0`，默认值是 `1.0`。

不同平台的范围不完全一样，所以别死记「温度一定是 0 到 2」。看你正在用的 API 文档。

更关键的是：**温度不会让模型突然知道更多事实。**

它只改变模型从已有概率分布里怎么选 token。事实任务里，低温通常更稳；创意任务里，高温通常更有变化。可如果模型没见过、上下文没给、检索没查到，温度再低也可能编。

这就接到下一章的幻觉问题了。

## Greedy Search：最稳，也最容易无聊

如果每一步都选概率最高的 token，这叫 greedy decoding。

| 特点 | 表现 |
| --- | --- |
| 稳定性 | 高 |
| 多样性 | 低 |
| 适合场景 | 短答案、分类、固定格式、简单抽取 |
| 风险 | 长文本重复、措辞死板、错过更自然的表达 |

Hugging Face 文档里说，`num_beams=1` 且 `do_sample=False` 时就是 greedy decoding。它在短输出里很好用，比如判断「有/无」、输出一个标签、生成一个很短的结构化字段。

但它也有明显短板。

Ari Holtzman 等人在论文 [The Curious Case of Neural Text Degeneration](https://arxiv.org/abs/1904.09751) 里提出一个很重要的观察：把似然最大化当作生成目标，会导致文本平淡、奇怪地重复。论文的核心判断很刺耳：高质量人类语言并不总是由最高概率词一路组成。

这句话很好理解。

人写文章时，太安全的词会变成套话。模型每一步都选最安全的词，末尾也会长出一股模板味。

## Beam Search：保留多条路线，但不一定适合聊天

Beam search（束搜索）会在每一步保留多条候选序列。比如 `num_beams=5`，模型会同时追踪 5 条可能路线，末尾选整体概率更高的序列。

它解决了 greedy 的一个问题：greedy 每一步只看眼前，可能错过后面更好的组合。Beam search 至少会多看几条路线。

Hugging Face 的 [How to generate text](https://huggingface.co/blog/how-to-generate) 里提到，beam search 常用于机器翻译、摘要这类输出长度较可预测的任务。但开放式生成，比如对话、故事、长文续写，beam search 经常显得保守、重复，多个候选之间差异也可能很小。

可以这样记：

| 解码方式 | 适合什么 | 容易出什么问题 |
| --- | --- | --- |
| Greedy | 短答案、固定格式 | 重复、死板 |
| Beam Search | 翻译、摘要、语音识别、图像描述 | 开放式生成里偏保守 |
| Sampling | 聊天、创作、头脑风暴 | 随机性变强，可能跑题 |

入门阶段做 Chat 类应用，最常接触的还是 temperature、top-k、top-p 这些采样参数。

## Top-k：只从前 k 个里抽

**Top-k sampling** 的规则很直接：模型把所有候选 token 按概率排序，只保留前 k 个，其他候选概率设为 0，再从剩下的候选里抽样。

<div markdown="1" style="overflow-x:auto;padding:0.5rem 0 0.8rem;margin:1rem 0;">
<div markdown="1" style="min-width:980px;">

~~~mermaid
flowchart LR
    A[模型预测下一个 token<br/>词表里有大量候选] --> B[按概率从高到低排序]
    B --> C{Top-k = 5}
    C --> D[只保留前 5 个]
    D --> E[其他候选概率设为 0]
    E --> F[重新归一化]
    F --> G[从 5 个候选中采样]
~~~

</div>
</div>

几个常见值：

| Top-k | 效果 |
| ---: | --- |
| 1 | 只看最可能的 token，接近 greedy |
| 10 | 候选池很窄，输出较稳 |
| 40 / 50 | 常见开放式生成设置，保留一定变化 |
| 0 或关闭 | 不按 k 截断，具体含义看框架实现 |

Hugging Face 的文章提到，GPT-2 采用过 Top-k sampling，文章示例里也常用 `top_k=50`。Top-k 的优点是简单，能直接砍掉长尾里一大堆奇怪候选。

它的缺点也来自简单。

k 是固定的。某一步模型很确定，只需要 3 个候选就够了，Top-k=50 仍会保留 50 个。另一步模型很不确定，可能有 80 个合理候选，Top-k=50 又会砍掉一部分还不错的词。

## Top-p：按累计概率动态截断

**Top-p sampling** 也叫 **Nucleus Sampling（核采样）**。它不固定保留几个候选，会保留一个「累计概率达到 p 的最小候选集合」。

看一个例子：

| 候选 token | 概率 | 累计概率 |
| --- | ---: | ---: |
| blue | 40% | 40% |
| clear | 30% | 70% |
| cloudy | 15% | 85% |
| dark | 10% | 95% |
| purple | 5% | 100% |

如果 `top_p = 0.9`，模型会从上往下累加，直到累计概率超过 90%。这里会保留 blue、clear、cloudy、dark，排除 purple。

<div markdown="1" style="overflow-x:auto;padding:0.5rem 0 0.8rem;margin:1rem 0;">
<div markdown="1" style="min-width:980px;">

~~~mermaid
flowchart LR
    A[模型预测下一个 token] --> B[按概率从高到低排序]
    B --> C[依次累加概率]
    C --> D{累计概率达到 top-p?}
    D -->|否| E[继续加入下一个候选]
    E --> C
    D -->|是| F[停止扩展候选池]
    F --> G[只在这个候选池里采样]
~~~

</div>
</div>

Top-p 的好处是动态。

模型很确定时，候选池会自动变小。模型不确定时，候选池会自动变大。

Holtzman 等人的 [The Curious Case of Neural Text Degeneration](https://arxiv.org/abs/1904.09751) 就是 Top-p / nucleus sampling 的经典来源之一。论文认为，从概率分布的动态核心区域采样，可以保留多样性，同时截断不可靠的长尾候选，让文本更接近人类语言的流畅度和连贯性。

## Top-k 和 Top-p 怎么配

实际系统里，你经常会看到两种路线。

一种路线是只调一个主旋钮。

Anthropic 文档把 `top_p` 和 `top_k` 都标为高级用法，普通场景优先用 temperature 会更直观。很多产品界面也只露出 temperature，因为它最好理解。

另一种路线是组合使用。

Hugging Face 的 [How to generate text](https://huggingface.co/blog/how-to-generate) 给过组合示例：`top_k=50` 加 `top_p=0.95`。这样 Top-k 先限制最低质量的长尾，Top-p 再根据累计概率动态收缩候选池。

两种路线都能用。新手建议按这个顺序来：

1. 先用默认参数跑一遍；
2. 输出太跳，先降 temperature；
3. 低温后仍有怪词，再收紧 top_p 或 top_k；
4. 只改一个参数，记录变化；
5. 找到稳定范围后再微调。

别一口气把 temperature、top_p、top_k 全拧到极端值。那样很难判断到底是哪一个参数带来了变化。

## 其他常见旋钮

采样参数不止 temperature、top-k、top-p。API 和本地推理框架里还会出现这些名字。

| 参数 | 管什么 | 怎么理解 |
| --- | --- | --- |
| `seed` | 随机种子 | 尽量让同一请求复现同类结果 |
| `frequency_penalty` | 频率惩罚 | 某个 token 出现越多，后面越不想再用它 |
| `presence_penalty` | 存在惩罚 | 只要某个 token 出现过，后面就降低它再次出现的倾向 |
| `repetition_penalty` | 重复惩罚 | 常见于开源推理框架，用来压低重复内容 |
| `no_repeat_ngram_size` | 禁止重复 n-gram | 防止固定短语反复出现 |
| `typical_p` | 典型采样 | 优先保留信息量更「典型」的 token |
| `candidateCount` / `num_return_sequences` | 多候选输出 | 一次生成多个版本，方便挑选 |

### seed：帮你复现，但别迷信

很多人以为只要固定 seed，输出就会完全一样。

真实情况更麻烦。

Google Vertex AI 文档说，`seed` 会让模型尽最大努力为重复请求提供相同回答，但**不保证确定性输出**。即使用相同 seed，换模型、改 temperature 或调整其他参数，结果也可能变化。Anthropic 文档也提醒，即使 temperature 设为 `0.0`，结果也不会完全确定。

所以 seed 更适合做调参对比和测试复现，别把它当成法律级保证。

### 惩罚项：减少复读机味

重复惩罚类参数解决的是另一类问题：模型写着写着开始复读。

Hugging Face 的文章举过 `no_repeat_ngram_size=2` 的例子，它会禁止重复出现任何 2-gram。这个方法能减少明显重复，但也会伤到合理重复。比如你写一篇介绍 New York 的文章，如果禁止重复 2-gram，`New York` 这个词组可能只能出现一次，这就很离谱。

惩罚项适合轻微使用。重复明显时加一点，别上来拉满。

### typical_p：另一种避开无聊和乱飞的方法

`typical_p` 来自 **Typical Sampling**。Clara Meister 等人的论文 [Locally Typical Sampling](https://arxiv.org/abs/2202.00666) 从信息论角度看生成：一个自然 token 的信息量通常接近当前分布的期望信息量。

它不单纯追最高概率，也不单纯追累计概率，而是看一个 token 的信息量是否「典型」。

这会排除两类候选：

- 太容易的 token，容易让文本变平、变重复；
- 太离谱的 token，容易让文本跑题。

入门阶段不一定要用它。你只要知道，解码策略并不止 Top-k 和 Top-p，业界一直在找更好的方式平衡流畅、多样和稳定。

## 不同任务怎么选参数

下面这张表可以直接用作起点。具体数值要按你使用的模型和平台再测。

| 任务 | Temperature | Top-p | Top-k | 说明 |
| --- | ---: | ---: | ---: | --- |
| 分类、抽取、固定标签 | 0 - 0.2 | 默认或偏低 | 默认或偏低 | 目标是稳定，不追求花样 |
| 代码生成、配置生成 | 0 - 0.3 | 0.7 - 0.9 | 默认或 20 - 50 | 先保证一致性，再看是否需要变化 |
| 事实问答、资料总结 | 0.2 - 0.5 | 0.8 - 0.95 | 默认 | 温度低一点，重点靠上下文和引用约束 |
| 翻译、改写 | 0.3 - 0.7 | 0.8 - 0.95 | 默认 | 保留语义，允许措辞变化 |
| 日常聊天 | 0.5 - 0.9 | 0.9 - 0.95 | 默认或 40 - 50 | 需要自然度和一点变化 |
| 标题、口号、命名 | 0.8 - 1.2 | 0.9 - 0.98 | 40 - 100 | 多生成几个候选更重要 |
| 诗歌、故事、脑洞 | 0.9 以上 | 0.95 左右 | 50 以上 | 接受少量跑飞，靠人工挑选 |

如果你用的是 Anthropic Claude，temperature 上限按它的 API 文档是 `1.0`。如果你用的是 Google Gemini，Vertex AI 文档里 Gemini 2.0 Flash 系列的范围是 `0.0 - 2.0`。同一个数字在不同模型上体感也可能不一样。

别把表格当神谕。它只是一个起点。

## 一个简单决策流程

<div markdown="1" style="overflow-x:auto;padding:0.5rem 0 0.8rem;margin:1rem 0;">
<div markdown="1" style="min-width:1080px;">

~~~mermaid
flowchart LR
    A[开始调参] --> B{输出需要严格稳定吗?}
    B -->|是<br/>分类/抽取/代码/配置| C[低 temperature<br/>0 - 0.3]
    B -->|否| D{需要创意吗?}
    D -->|低<br/>总结/翻译/改写| E[中低 temperature<br/>0.3 - 0.6]
    D -->|中<br/>聊天/解释/写作辅助| F[中等 temperature<br/>0.5 - 0.9]
    D -->|高<br/>标题/故事/脑暴| G[高 temperature<br/>0.8 以上]
    C --> H{仍然重复?}
    E --> H
    F --> H
    G --> I{出现怪词或跑题?}
    H -->|是| J[轻微增加重复惩罚<br/>或收紧候选池]
    H -->|否| K[固定配置并记录]
    I -->|是| L[降低 temperature<br/>或收紧 top_p/top_k]
    I -->|否| K
    J --> K
    L --> K
~~~

</div>
</div>

调参时最容易犯的错，是只看单次输出。

采样本来就带随机性。你至少应该让同一个 Prompt 跑 3 到 5 次，再看稳定范围。做产品时更要准备一组测试集，覆盖短问答、长问答、边界输入、恶意输入和格式要求。

## 采样参数和幻觉是什么关系

高温更容易出现离谱内容，这个经验大体成立。

但反过来说，低温不会自动消灭幻觉。

幻觉来自很多地方：模型参数里的错误关联、上下文缺材料、检索结果有噪声、Prompt 诱导模型补全未知信息、输出时缺少校验。采样参数只影响「从候选里怎么选」。

举个例子。

你问一个模型某篇不存在的论文结论。低温时，它可能稳定地编出同一个错误答案。高温时，它可能编出三个不同版本。低温让错误更一致，高温让错误更分散。

所以事实类任务要靠组合拳：

- 降低 temperature；
- 明确要求引用来源；
- 给足上下文；
- 对关键事实做检索或工具校验；
- 让模型承认「资料不足」；
- 对输出做人工或程序检查。

采样参数能帮你压住风格，不能替你验证事实。

## 常见误区

??? warning "误区 1：温度越高，模型越聪明"

    温度高只代表输出更随机、更多样。它不会提高模型推理能力，也不会增加知识。
    
    代码、数学、事实核查这类任务里，高温经常带来麻烦。模型可能换一种看似很有创意的写法，然后把格式写坏。

??? warning "误区 2：temperature = 0 就一定完全可复现"

    很多 API 会尽量让低温输出稳定，但工程系统里还有并行计算、浮点精度、后端版本、模型更新、seed 支持方式等变量。
    
    Anthropic 文档明确说，即使 temperature 是 `0.0`，结果也不会完全确定。Google Vertex AI 文档也说 seed 不保证确定性。
    
    如果你在做自动化测试，别只靠 temperature。要固定模型版本、参数、Prompt、上下文、工具返回值，再记录 seed 和运行环境。

??? warning "误区 3：Top-p 越低越安全"

    Top-p 太低会让候选池很窄，输出可能变得机械。事实任务看起来更稳，长回答却容易套话。
    
    「安全」不等于「候选越少越好」。真正的安全来自任务边界、来源约束、权限控制和结果校验。

??? warning "误区 4：重复惩罚越大越好"

    重复惩罚拉太高，会伤害正常表达。专有名词、人名、产品名、代码变量名都可能需要重复。
    
    如果模型复读，先检查 Prompt 是否让它一直围绕同一个句式输出，再轻微调惩罚项。

??? warning "误区 5：默认参数适合所有任务"

    默认参数通常偏向通用聊天。通用聊天要自然，所以会留一定随机性。
    
    你做分类、抽取、代码生成、批量文档处理时，默认参数可能太散。你做标题、创意写作、脑暴时，默认参数又可能太保守。
    
    参数要跟任务走。

## 最小实验：同一个提示词跑三档温度

你可以拿常用模型做一个小实验。

提示词：

<pre><code>用一句话描述一只猫。</code></pre>
低温输出可能像这样：

> 猫是一种小型哺乳动物，常被人类饲养为宠物。

中温输出可能像这样：

> 猫是一种安静又敏捷的动物，喜欢在窗边晒太阳，也会突然冲向看不见的目标。

高温输出可能像这样：

> 猫把午后的光踩成碎片，然后假装这一切都和它无关。

低温像百科句。中温像正常描述。高温开始有文学感。

这三个答案都能用，取决于你想要什么。

## 实战调参记录表

调参别凭感觉。做一个小表，比脑补靠谱。

| 测试项 | Prompt | 参数 | 输出现象 | 下一步 |
| --- | --- | --- | --- | --- |
| 事实总结 | 总结一段新闻 | T=0.3 / top_p=0.9 | 稳，但措辞有点硬 | 保持 T，优化 Prompt |
| 标题生成 | 生成 10 个标题 | T=0.9 / top_p=0.95 | 有变化，2 个跑题 | 降到 T=0.8 |
| JSON 输出 | 提取字段 | T=0.1 | 格式稳定 | 固定配置 |
| 长文续写 | 续写故事 | T=1.0 / top_p=0.95 | 有创意但重复一个意象 | 加轻微重复惩罚 |

新手最好每次只改一个参数。改完记录结果。几轮之后，你会对模型的脾气有感觉。

## 练习题 / 小实验

??? question "练习 1：温度对比"

    选一个你常用的模型，用同一个提示词分别跑三次：
    
    <pre><code>请写一首关于秋天的四行短诗。</code></pre>
    
    分别设置低温、中温、高温。记录三件事：
    
    - 用词是否变了？
    - 意象是否变了？
    - 哪个版本更适合发布？

??? question "练习 2：事实任务"

    找一段真实新闻或产品公告，让模型总结 5 条要点。分别用低温和高温跑一次。
    
    观察：
    
    - 高温有没有改写得更漂亮？
    - 有没有新增原文没有的信息？
    - 低温有没有更忠实？

??? question "练习 3：创意任务"

    让模型生成 20 个栏目名。分别使用低温和高温。
    
    观察：
    
    - 低温是否更像模板？
    - 高温是否更有惊喜？
    - 有没有明显跑题的结果？

??? question "练习 4：复现测试"

    如果你使用的 API 支持 seed，固定同一个 seed、同一个 Prompt、同一个模型版本，连续跑 5 次。
    
    观察：
    
    - 输出是否完全一致？
    - 改变 temperature 后，结果是否变化？
    - 换模型版本后，seed 还能否复现？

## 小结

这章你只需要带走四句话：

- **Temperature** 调整概率分布的尖锐程度，低温稳，高温散。
- **Top-k** 固定保留前 k 个候选，简单直接。
- **Top-p** 按累计概率动态保留候选，开放式生成里很常用。
- **seed 和低温都不能保证绝对复现，事实正确还要靠上下文、检索和校验。**

采样参数控制的是输出时的选择方式。它能让模型更稳，也能让模型更有变化。

但它管不了一切。

下一章就进入最容易踩坑的地方：模型为什么会胡说。

## 下一步

<div markdown="1" style="border:1px solid var(--md-default-fg-color--lightest);border-left:4px solid var(--md-accent-fg-color);border-radius:0.85rem;padding:1rem 1.1rem;margin:0.9rem 0;background:linear-gradient(135deg,var(--md-code-bg-color),rgba(255,112,67,0.06));">

理解了温度与采样参数之后，下一站建议看：

<a href="../hallucination/" style="display:block;margin-top:0.75rem;padding:0.85rem 1rem;border-radius:0.65rem;background:var(--md-default-bg-color);text-decoration:none;border:1px solid var(--md-default-fg-color--lightest);">
  <strong>为什么模型会胡说 →</strong><br>
  <span style="color:var(--md-default-fg-color--light);font-size:0.92rem;">理解幻觉从哪里来，以及怎么降低它。</span>
</a>

</div>
