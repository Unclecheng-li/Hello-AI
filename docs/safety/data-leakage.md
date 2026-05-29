---
tags:
  - Safety
---

# 数据泄露

> 你发给模型的每一句话、每一个文件，都可能成为不可撤回的数据泄露。知道什么该发、什么不该发，是使用 AI 的基本功。

## 这章解决什么问题

你在 AI 对话工具里粘贴了一段代码，里面不小心带了一行 AWS Secret Key。几秒后，这个 Key 已经不在你的控制范围内了——它可能被记录在 OpenAI、Anthropic 或 Google 的服务器日志里，被用于模型训练，甚至被其他人通过未来的数据泄露提取出来。

这不是恐吓，这是真实发生过的事。2023 年，三星员工在使用 ChatGPT 处理内部源代码时，将公司机密信息粘贴到对话中，导致数据暴露给第三方服务提供商。

数据泄露（Data Leakage）在 AI 场景下指的是：**敏感信息通过输入或输出通道，被模型服务端获取、存储或二次利用**。它和传统网络安全的"数据泄露"最大区别在于：LLM 的输入输出通道天然就是一个潜在的泄露出口，你每次发送消息都在做一次数据传输。

## 核心场景：数据从哪里泄露出去

### 场景 1：输入泄露（Input Leakage）

最常见的数据泄露方式。用户或开发者把敏感信息放在了 Prompt、文件或代码上下文中，然后发送给模型服务端。

典型的敏感信息包括：

- **API Key / Secret / Token**：AWS Secret Key、GitHub Personal Access Token、数据库密码
- **个人身份信息（PII, Personally Identifiable Information）**：姓名、身份证号、电话、地址、医疗记录
- **企业内部信息**：未公开的业务数据、源代码、客户名单、财务数据
- **法律/合规敏感信息**：NDA（Non-Disclosure Agreement，保密协议）覆盖的内容、受 GDPR（General Data Protection Regulation，欧盟通用数据保护条例）保护的欧盟用户数据

### 场景 2：输出泄露（Output Leakage）

模型生成的回答中，意外包含了本不该出现的信息。这通常发生在：

- **训练数据记忆（Training Data Memorization）**：模型可能在训练时"记住"了训练集中的某些敏感文本，并在推理时原样输出。例如有研究发现，GPT-2 可以被诱导输出训练数据中的电子邮件地址和电话号码
- **上下文泄露**：在多轮对话或 RAG（检索增强生成）场景中，模型可能把之前对话中的信息带到了当前回答里

### 场景 3：第三方模型服务的数据使用

这是很多开发者容易忽略的部分。你把数据发给一个 API，不代表这个 API 背后的公司一定会保护它。

截至 2026 年 5 月，主要模型 API 提供商的数据政策：

| 提供商 | API 数据是否用于训练 | 备注 |
|--------|---------------------|------|
| OpenAI | 否（API），是（ChatGPT） | API 数据 30 天后删除；可选零数据保留 (ZDR) |
| Anthropic | 否（API） | API 数据 30 天后删除；可选 ZDR；支持 HIPAA |
| Google (Vertex AI) | 否（企业版） | 需签订 Cloud DPA 数据处理协议 |
| 百度文心 (千帆) | 否（平台数据集不用于训练） | 企业版数据隔离；用户数据集专属不共享 |
| 阿里通义千问 (百炼) | 取决于服务条款 | 匿名化后可能用于改进；企业版可联系禁用 |

!!! warning "注意"

    数据政策会随时更新。使用任何 API 之前，**必须阅读当前的最新服务条款和数据使用协议**，不能依赖本章的摘要。

## 最小防护：你可以立刻做的事

### 第一步：输入审查（Scrub Before You Send）

在发送给模型之前，自动或手动扫描 Prompt 中的敏感信息。

```python
import re

# 一个极简的敏感信息检测函数
def detect_sensitive(text: str) -> list[str]:
    warnings = []
    # AWS Access Key 格式：AKIA 开头 + 16 位字符
    if re.search(r'AKIA[0-9A-Z]{16}', text):
        warnings.append("检测到可能的 AWS Access Key")
    # 疑似 API Key：32 位以上字母数字组合，周围有 key/secret 标识
    if re.search(r'(?i)(key|secret|token)[\'":\s=]+[A-Za-z0-9_\-]{20,}', text):
        warnings.append("检测到可能的密钥或 Token")
    # 中国大陆手机号
    if re.search(r'1[3-9]\d{9}', text):
        warnings.append("检测到可能的手机号")
    return warnings

# 使用示例
user_input = "我的 AWS Key 是 AKIAIOSFODNN7EXAMPLE"
for w in detect_sensitive(user_input):
    print(f"⚠ {w}")
```

这只是一个最小示例。生产环境可以考虑用 [Microsoft Presidio](https://microsoft.github.io/presidio/) 或类似工具做结构化敏感信息检测。

### 第二步：理解你用的服务的数据政策

使用任何 AI 服务之前，确认以下问题：

1. 数据是否会被用于模型训练？
2. 数据存储多久后被删除？
3. 数据传输是否加密（TLS, Transport Layer Security，传输层安全协议）？
4. 数据是否跨境传输？（从中国大陆发送数据到海外 API 需评估合规要求）
5. 是否有数据隔离承诺（你的数据不会和其他客户的数据混在一起）？

### 第三步：最小化原则（Data Minimization）

只发送模型完成任务**真正需要**的信息。

- 如果模型只需要"这个订单的配送地址"，不要发完整的订单 JSON
- 如果模型只需要"判断这段文字的情绪"，不要附带用户姓名
- 在生产系统中，使用**数据脱敏（Data Masking）**或**字段过滤**，在发送前移除敏感字段

## 常见误区

!!! failure "误区 1：大厂产品数据肯定安全"
    2023 年三星数据泄露事件恰恰发生在使用主流 AI 产品的过程中。安全取决于你的使用方式，而不是产品品牌。

!!! failure "误区 2：删掉聊天记录就没事了"
    删除本地对话记录不会删除已经在服务端存储的数据。数据和模型 API 一旦完成传输，你无法单方面撤回。

!!! failure "误区 3：只是代码，没什么敏感信息"
    代码中可能包含硬编码的密钥、内部 IP 地址、数据库连接串、注释中的密码。很多数据泄露发生在"我没注意到里面带了敏感信息"的情况下。

!!! failure "误区 4：用企业版就彻底安全了"
    企业版通常有更好的数据保护条款（数据不用于训练、存储时间更短），但不等于完全豁免。企业版仍然需要面对输入泄露、输出泄露和人为操作失误的风险。

## 延伸阅读

- [OWASP LLM Top 10 — Data Leakage](https://genai.owasp.org/llmrisk/llm022025-sensitive-information-disclosure/) — OWASP 大模型安全分类中的数据泄露风险
- [三星 ChatGPT 数据泄露事件分析 (2023)](https://www.digitimes.com/news/a20230406PD208/samsung-electronics-chatgpt-data-leak.html) — 实际案例分析
- [Microsoft Presidio](https://microsoft.github.io/presidio/) — 开源敏感信息检测工具
- [OpenAI Data Usage Policy](https://openai.com/enterprise-privacy/) — OpenAI 企业数据隐私说明
- [Google Cloud Data Processing Addendum](https://cloud.google.com/terms/data-processing-addendum) — Google Cloud 数据处理协议

## 练习题

??? question "练习 1：实战检查"
    打开你最常用的 AI 聊天工具，回顾最近 3 条消息。列出里面包含了哪些可能敏感的信息（姓名、公司名、项目代号、API Key 等）。如果一条都没有，想想为什么——是真的没有，还是你没注意到？

??? question "练习 2：数据政策对比"
    选择一个海外模型 API（如 OpenAI）和一个国内 API（如通义千问、文心），查阅它们当前的数据使用政策，对比以下三点：数据是否可用于训练、存储期限、是否支持删除请求。

??? question "练习 3：脱敏实验"
    写一个简单的 Python 函数，输入一个包含姓名、电话和邮箱地址的文本，输出脱敏后的版本（如"张三"→"张**"，"13800138000"→"138****8000"）。
