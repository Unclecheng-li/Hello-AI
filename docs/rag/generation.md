---
tags:
  - RAG
---

# 生成：LLM 基于资料组织答案

> 生成（Generation）是 RAG 的最后一步——把检索到的资料和用户问题拼成 Prompt，让 LLM 基于事实生成答案。

## 这章解决什么问题

假设你已经做好了所有前置工作：文档切分得漂亮、向量化精确、检索返回了最相关的 3 个片段。但如果 Prompt 写得不好，LLM 可能忽略资料、编造答案、或者回答得啰嗦没重点。

**生成阶段的任务是**：把资料、问题和指令精确地编排在一起，让 LLM 知道自己的角色、知道哪些是事实依据、知道什么情况下该说「不知道」。

## 核心概念

### RAG Prompt 的三大要素

一个标准的 RAG Prompt 包含三部分：

1. **指令（Instruction）**：告诉 LLM 它的角色和任务
2. **资料（Context）**：检索到的文档片段
3. **问题（Question）**：用户的原问题

基础模板示例：

```python
prompt_template = """
你是一个基于资料的客服助手。请用以下资料回答用户问题。

资料：
{context}

用户问题：{question}

要求：
- 只根据资料内容回答，不要自行编造
- 如果资料中没有足够信息，请说「我找不到相关信息」
- 如果可能，在回答末尾标注信息来源
- 保持回答简洁、专业
"""
```

### Prompt 设计的关键原则

**原则 1：资料比问题更重要**

研究表明，将资料放在问题之前，LLM 会更倾向于使用资料。反之，如果问题在前，LLM 可能更依赖自己的训练数据：

```python
# ✅ 推荐：资料在前
prompt = f"资料：{context}\n\n基于以上资料，回答：{question}"

# ❌ 不推荐：问题在前
prompt = f"问题：{question}\n\n另外，这里有参考资料：{context}"
```

**原则 2：明确拒绝编造的边界**

RAG 的一个核心目的是减少幻觉。但 LLM 的「续写」本能仍然存在。需要在 Prompt 里明确加一条边界：

```
- 如果资料中没有相关信息，请说「根据现有资料，我无法回答这个问题」
- 不要推测或编造资料中不存在的信息
```

**原则 3：控制回答格式**

不指定格式的话，同一个问题可能今天得到一个段落、明天拿到一个列表。常用的格式控制：

```
- 请用 Markdown 格式回答
- 对于多个要点，用有序列表组织
- 引用来源请用 [来源 X] 的格式标注
```

**原则 4：来源标注**

让 LLM 标注回答中每一部分信息的来源，可以提高可信度并方便用户验证：

```
- 在回答末尾添加：\n\n（来源：{source_1}、{source_2}）
- 引用具体信息时标注对应的文档编号
```

### 幻觉（Hallucination）在 RAG 中如何产生

即使有了 RAG，幻觉仍然可能发生。常见原因：

| 原因 | 表现 | 解决办法 |
|------|------|---------|
| 检索到的资料与问题不相关 | LLM 忽略资料凭记忆回答 | 改善检索/重排 |
| 资料正确但 LLM 没用它 | LLM 自己编了一个「更合理」的答案 | 强化 Prompt 中「只根据资料回答」的约束 |
| 资料中存在矛盾信息 | LLM 尝试调和矛盾，产生不准确描述 | 确保切分不产生矛盾片段 |
| 问题中包含 LLM 训练数据中的强关联 | LLM 用训练数据覆盖了资料信息 | 在 Prompt 中说「忽略你的训练数据，只使用以下资料」 |

### 事实性校验（Groundedness Checking）

在一些高风险场景（医疗、法律、金融），可以在生成后加一道校验步骤：

```python
check_prompt = f"""
请判断以下 LLM 回答是否完全基于提供的资料。用 Yes/No 回答，并说明理由。

资料：
{context}

LLM 回答：
{answer}

判断是否有内容在资料中没有依据：
"""
```

只有在校验通过时才向用户展示回答。这虽然增加了额外成本，但在关键场景中是值得的。

### 温度与生成参数

| 参数 | 推荐值 | 理由 |
|------|--------|------|
| `temperature` | 0.1~0.3 | 低温度减少幻觉，让 LLM 更忠实于资料 |
| `top_p` | 0.1~0.3 | 与低温度配合，进一步约束输出的随机性 |
| `max_tokens` | 视需要 | 限制回答长度，避免漫无边际 |
| `frequency_penalty` | 0 | RAG 本身已限制输入，不需要额外惩罚 |
| `presence_penalty` | 0 | 同上 |

!!! warning "不要用默认 temperature"
    很多 API 的默认 temperature 是 1.0。对于 RAG 场景，这个值偏高——LLM 会更「有创意」，但也更容易偏离资料。建议统一设为 0.3。

## 最小示例

完整的 RAG 生成流程，包含资料编排和校验：

```python
import openai

# ── 1. 检索到的资料 ──
context = """
RAG（Retrieval-Augmented Generation）是一种检索增强生成技术。
它由检索器、知识库和生成器三部分组成。
RAG 的优势在于可以引入外部知识，减少模型幻觉。
"""

question = "RAG 由哪些部分组成？"

# ── 2. 编排 Prompt ──
prompt = f"""
你是一个专业的 AI 知识助手。请严格根据以下资料回答问题。

{context}

用户问题：{question}

要求：
1. 只根据资料内容回答，不要添加资料中没有的信息
2. 如果资料不足以回答问题，请说「我找不到相关信息」
3. 回答要简洁、准确
"""

# ── 3. 生成 ──
response = openai.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": prompt}],
    temperature=0.3,
)

answer = response.choices[0].message.content
print(answer)

# ── 4. 事实性校验（可选）──
check = openai.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{
        "role": "user",
        "content": f"""判断以下回答是否完全基于资料。
资料：{context}
回答：{answer}
请用 Yes/No 回答。"""
    }],
    temperature=0,
)
print(f"事实性校验通过：{check.choices[0].message.content}")
```

## 常见误区

!!! failure "误区 1：所有 LLM 对同样的 Prompt 表现一样"
    不同模型在「忠实于资料」的能力上差异很大。小模型更容易忽略资料直接凭记忆回答。建议测试时对比至少 2~3 个模型的回答质量。

!!! failure "误区 2：Prompt 写一次就够了"
    RAG 的 Prompt 需要持续调整。当你更换知识库、LLM 或业务场景时，都需要重新评估 Prompt 的效果。

!!! failure "误区 3：temperature=0 就能完全消除幻觉"
    temperature=0 只是让输出确定，但不能保证输出正确。如果资料缺失或 Prompt 没有约束「必须以资料为准」，LLM 仍然可能自信地编造。

## 延伸阅读

- [为什么需要 RAG](why-rag.md) —— RAG 的动机和定位
- [RAG 常见问题](troubleshooting.md) —— 从「回答不好」反向排查故障
- [什么是 Prompt](../prompt/index.md) —— Prompt 工程的核心思想
- [结构化的 Prompt](../prompt/structure.md) —— 如何系统化设计 Prompt

## 练习题

??? question "练习 1：对比 Prompt 设计的效果"

    设计三个不同的 RAG Prompt 模板来回答同一个问题：

    - Prompt A：只有「请基于以下资料回答」这句话，没有其他约束
    - Prompt B：加了「只根据资料回答，不要编造」的约束
    - Prompt C：B 的基础上加了「标注来源」和「如果不知道就说不知道」

    用同一个资料和问题分别测试，对比三次回答的准确性和格式。

??? question "练习 2：设计你自己的 RAG Prompt"

    选择一个你熟悉的业务场景（如产品客服、学习助手、文档摘要），写出一个完整的 RAG Prompt 模板，包含：

    1. 系统指令（角色和任务）
    2. 资料占位符
    3. 问题占位符
    4. 输出格式要求
    5. 边界条件（什么情况拒绝回答）

    提交之前找一个人review你的模板，让对方判断：
    「在不看资料的情况下，只看你的 Prompt，能不能清楚地知道模型应该做什么、不该做什么？」
