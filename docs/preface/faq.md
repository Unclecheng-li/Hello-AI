# 常见顾虑

<div markdown="1" style="position:relative;overflow:hidden;border:1px solid rgba(0,150,136,0.22);border-radius:1rem;padding:1.25rem 1.35rem;margin:0.8rem 0 1.5rem;background:linear-gradient(135deg,rgba(0,150,136,0.10),rgba(0,188,212,0.08) 48%,rgba(63,81,181,0.08));box-shadow:0 0.65rem 1.8rem rgba(0,0,0,0.10);">
<div style="position:absolute;right:-3.8rem;top:-4.2rem;width:12rem;height:12rem;border-radius:50%;background:radial-gradient(circle,rgba(0,150,136,0.20),rgba(0,150,136,0));"></div>
<div style="position:absolute;left:-4rem;bottom:-5rem;width:14rem;height:14rem;border-radius:50%;background:radial-gradient(circle,rgba(0,188,212,0.15),rgba(0,188,212,0));"></div>
<div style="position:relative;z-index:1;">
<span style="display:inline-block;padding:0.18rem 0.55rem;border-radius:999px;background:rgba(0,150,136,0.14);color:#00695c;font-size:0.78rem;font-weight:700;letter-spacing:0.02em;">前言 · 第 3 站</span>

学 AI 之前，大多数人心里都有几个坎。我当初也有，身边朋友也有。这里一个一个帮你迈过去，用的都是真话，不画饼。
</div>
</div>

---

## 学 AI 要先学完线代 / 概率论 / Python 全套吗？

<div markdown="1" style="border-left:3px solid rgba(0,150,136,0.45);padding:0.8rem 1rem;margin:0 0 1rem;background:rgba(0,150,136,0.04);border-radius:0 0.5rem 0.5rem 0;">
<strong>不用。</strong>
</div>

这个误解耽误了太多人。我有个朋友，两年前想学 AI，先买了一本线性代数的教材，翻了两周，放弃了。后来跟我说「可能我数学太差，不适合学这个」。我听了特别心疼。他根本不需要先把线代啃完。

用 AI 写应用，所需数学比你想的少太多。你用 ChatGPT 聊天，需要线代吗？你用 Prompt 让模型帮你整理文档，需要概率论吗？你用 Claude Code 搭一个小工具，需要微积分吗？都不需要。

确实，如果你想深入理解 Transformer 的注意力机制，或者自己训练一个模型，线性代数和概率论是绕不开的。但那是后面的事。先跑起来，遇到需要数学的地方再回头补，缺啥补啥比一次学完高效十倍。

如果你完全不会写代码，也别急。Chat 类产品（ChatGPT、Claude、Gemini）只需要你会打字。API 调用和 Build 阶段才需要写代码，但到那一步的时候，AI 本身就能帮你写大部分。去年 Vibe Coding 出来之后，很多人用大白话描述需求就能让 AI 生成代码，门槛真的降下来了。

---

## 等模型再迭代一轮我再学？

<div markdown="1" style="border-left:3px solid rgba(255,112,67,0.45);padding:0.8rem 1rem;margin:0 0 1rem;background:rgba(255,112,67,0.04);border-radius:0 0.5rem 0.5rem 0;">
<strong>等下去只会更落后。</strong>
</div>

这个想法我太熟悉了。我自己就等过。

2024 年的时候我想学 AI，当时觉得「GPT-5 快出了，等出来再学，免得学了过时」。结果 GPT-5 没等来，等来的是身边的人一个个都开始用 AI 了，我还停在原地。

底层 API 调用、Prompt、RAG、Agent 这层抽象已经稳定了两年多。

模型确实在变。去年的模型今年可能就不是最强的了。但「怎么跟模型说话」「怎么给模型接上外部资料」「怎么让模型自己干活」这些能力，换一个模型照样用。就像你学会了开车，换一辆车你还是会开。

每次有新模型出来，我看到的都是已经在用 AI 的人第一时间上手试，第一时间吃到红利。等的人永远在等。

---

## LangChain / LlamaIndex 必须二选一？

<div markdown="1" style="border-left:3px solid rgba(63,81,181,0.45);padding:0.8rem 1rem;margin:0 0 1rem;background:rgba(63,81,181,0.04);border-radius:0 0.5rem 0.5rem 0;">
<strong>先用原生 SDK 跑一遍。</strong>
</div>

我见过太多人了，花了一整天对比 LangChain 和 LlamaIndex 哪个好，看了 20 篇评测文章，最后选了一个，装上，发现还是不会用。因为底层原理没搞懂，框架只给你加了一层抽象，出了问题你都不知道往哪查。

你会发现框架只省了几行代码，代价却是一整个黑盒。等你用原生 SDK 跑通了一个小项目，再回去看框架，就知道它帮你省了什么、又给你加了什么负担。

先动手，再选工具。顺序反了，你会在工具选择上浪费大量时间。

---

## 微调比 RAG 高级？

<div markdown="1" style="border-left:3px solid rgba(233,30,99,0.45);padding:0.8rem 1rem;margin:0 0 1rem;background:rgba(233,30,99,0.04);border-radius:0 0.5rem 0.5rem 0;">
<strong>先把 Prompt 和 RAG 做好再考虑微调。</strong>
</div>

90% 的场景下，先把 Prompt 和 RAG 做好再考虑微调。省时省钱效果还更好。

我有个朋友，公司要做一个内部知识库问答系统。他上来就要微调，花了两周准备数据、选模型、调参数，最后效果还不如直接用 RAG 接上公司文档。RAG 那套他半天就搭好了。

微调有用，但它解决的是「让模型本身变得更懂某个领域」。RAG 解决的是「让模型能查到你给它的资料」。它们解决的问题不一样。先把基础做好，再考虑要不要微调。

---

## 我不是程序员，能学？

<div markdown="1" style="border-left:3px solid rgba(0,150,136,0.45);padding:0.8rem 1rem;margin:0 0 1rem;background:rgba(0,150,136,0.04);border-radius:0 0.5rem 0.5rem 0;">
<strong>能。</strong>
</div>

这个问题我被问过不下十次。每次我都回答得很快，因为答案真的很简单。

Chat 类产品直接对话就行，不需要写代码。你只需要知道怎么提问、怎么看输出、怎么判断回答靠不靠谱。这些 AI 基础章节都会讲。

API 调用和 Build 阶段才需要写代码，但有 AI 帮忙，门槛比你想象的低很多。Vibe Coding 出来之后，有产品经理用 Claude Code 半小时搭了一个内部工具，以前这事至少得找程序员排两天队。

学 AI 这件事，核心能力是「知道怎么跟 AI 说话」和「知道什么时候该信它、什么时候该查」。这两种能力跟你会不会写代码没关系。

---

## 免费能学？

<div markdown="1" style="border-left:3px solid rgba(63,81,181,0.45);padding:0.8rem 1rem;margin:0 0 1rem;background:rgba(63,81,181,0.04);border-radius:0 0.5rem 0.5rem 0;">
<strong>能。最大投入是时间，不是钱。</strong>
</div>

大部分 AI 平台都有免费额度。ChatGPT、Claude、Gemini 的免费版就够你练完基础章节。Google AI Studio 有免费层级，学生还能申请 Gemini Advanced 的教育优惠。开源模型在自己机器上跑完全免费。

Hello-AI 本身也免费。不搞付费墙，不搞「高级内容解锁」。

每天花一两个小时，两三周就能走完基础章节。这个成本比任何培训班都低。

---

## 学完会不会被 AI 取代？

<div markdown="1" style="border-left:3px solid rgba(233,30,99,0.45);padding:0.8rem 1rem;margin:0 0 1rem;background:rgba(233,30,99,0.04);border-radius:0 0.5rem 0.5rem 0;">
<strong>AI 取代的从来不是「用 AI 的人」。</strong>
</div>

学完你拿到的是判断力。知道什么时候该信模型、什么时候该查、什么时候该自己动手。这种能力在 AI 时代反而更值钱。

普华永道的报告说得很清楚。AI 相关岗位数量增长了 38%，AI 高暴露度行业薪酬增速是低暴露度行业的两倍。AI 在取代一些重复性工作的同时，也在创造大量新的岗位。关键是你站在哪一边。

我自己的感受是，会用锤子的人比不会用的人更有竞争力，但锤子不会自己造房子。你得知道什么时候用锤子、什么时候用螺丝刀、什么时候什么都别用，直接用手。

这种判断力没法速成，但可以一步一步攒出来。Hello-AI 每一章都在帮你攒这个。

---

## 还是不确定从哪开始？

没关系。大多数人都这样。

[去看学习路线 →](roadmap.md){ .md-button .md-button--primary }
[直接去 AI 基础](../basics/what-is-ai.md){ .md-button }
