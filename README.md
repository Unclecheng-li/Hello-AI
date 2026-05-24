<div align="center">

# Hello-AI

> 面向中文学习者的 AI / LLM 入门知识库：从概念、Prompt、工具使用，到 RAG、Agent、应用开发、评测与安全。

[![MkDocs](https://img.shields.io/badge/Docs-MkDocs_Material-black)](https://squidfunk.github.io/mkdocs-material/)
[![GitHub Pages](https://img.shields.io/badge/Deploy-GitHub_Pages-blue)](https://unclecheng-li.github.io/Hello-AI/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Bootstrapping-orange)](#项目状态)

**网站链接**：https://hello-ai.seekstar.ai  
**备用链接**：https://unclecheng-li.github.io/Hello-AI/

[在线阅读](https://hello-ai.seekstar.ai) · [学习路线](docs/preface/roadmap.md) · [本地预览](#本地预览) · [项目结构](#项目结构)

</div>

---

## 关于 Hello-AI

AI 工具越来越多，大模型概念越来越密，但真正的新手常常卡在第一步：

- 不知道 AI、机器学习、深度学习、LLM 之间到底是什么关系；
- 会用聊天工具，但不知道 Prompt 为什么有时稳定、有时失控；
- 听过 RAG、Agent、Function Calling，却分不清它们解决什么问题；
- 想做一个 AI 应用，但不知道 API、部署、评测和安全边界怎么串起来；
- 信息来源太散，教程深浅不一，学完一堆名词却仍然没有路线感。

**Hello-AI** 想解决的不是“再堆一份资料合集”，而是做一条面向中文学习者的 AI / LLM 入门路径：用尽量清楚的语言，把基础概念、工具实践、工程搭建和安全意识串成一个能从头走到尾的知识站。

项目参考了 Hello-CTF 这类开源入门教程的组织方式：仓库即内容源，Markdown 编写，MkDocs 构建，GitHub Pages 自动发布。

---

## 项目定位

Hello-AI 面向三类读者：

| 读者 | 典型问题 | Hello-AI 提供什么 |
| --- | --- | --- |
| AI 小白 | “我想入门，但不知道先学什么” | 从概念到工具的顺序化学习路径 |
| 内容创作者 / 运营 / 产品 | “我想把 AI 用到工作里” | Prompt、工具选择、工作流和常见任务模板 |
| 初级开发者 | “我想做一个 AI 应用” | API、RAG、Agent、评测、部署和安全基础 |

它不是论文综述，也不是模型排行榜，更不是只面向算法工程师的深度教材。它更像一本“AI 入门地图”：先帮读者建立方向感，再逐步把关键概念讲透。

---

## 内容模块

当前站点规划为以下主线：

| 模块 | 内容重点 |
| --- | --- |
| 前言 | 新手起步、学习路线、阅读方式 |
| AI 基础 | AI、机器学习、深度学习、LLM、Token、Embedding、上下文窗口、幻觉 |
| Prompt | Prompt 基础结构、模板、稳定输出、常见任务、失败案例 |
| AI 工具使用 | Chat 产品、模型选择、API 入门、工具调用、本地模型与在线模型 |
| RAG | 文档切分、向量化、检索、重排、生成与故障排查 |
| Agent 智能体 | Agent 与 Workflow、工具调用、任务拆解、反思循环、失败模式 |
| AI Build 实战 | API 接入、最小 AI 应用、本地模型、部署、Docker 基础 |
| AI Evals | 主观与客观指标、幻觉评测、输出质量判断、简单评测方法 |
| AI 与大模型安全 | 数据泄露、提示注入、越权调用、使用边界与合规提示 |
| 实验 | Prompt 改写、RAG 基础、Agent 拆解等可操作练习 |
| 相关资源 | 模型平台、API 平台、RAG / Agent 框架、评测工具、书单与文章 |

---

## 学习路线

建议按下面的顺序阅读：

```text
前言与路线
  -> AI 基础
  -> Prompt
  -> AI 工具使用
  -> RAG
  -> Agent
  -> AI Build 实战
  -> AI Evals
  -> AI 与大模型安全
  -> 实验与资源
```

如果你只是想“先用起来”，可以先读：

```text
新手起步 -> Prompt 基础 -> Chat 类产品怎么用 -> 如何选择模型 -> Prompt 常见失败案例
```

如果你想“做一个 AI 应用”，可以先读：

```text
什么是 LLM -> API 入门 -> 函数调用与工具调用 -> RAG 总览 -> 最小 AI 应用 -> 简单评测
```

如果你关注“AI 安全与可靠性”，可以先读：

```text
为什么模型会胡说 -> 幻觉评测 -> 数据泄露 -> 提示注入 -> 越权调用 -> 使用边界与合规提示
```

---

## 项目状态

Hello-AI 当前处于初始化建设阶段：

- 已完成 MkDocs Material 站点骨架；
- 已完成基础导航结构；
- 已配置 GitHub Pages 自动构建与发布；
- 已建立本地构建检查脚本；
- 正在逐步补齐各章节正文内容。

现阶段重点不是追求“大而全”，而是先保证结构清晰、路径成立、每个章节都能回答一个明确的新手问题。

---

## 本地预览

### 1. 克隆仓库

```bash
git clone https://github.com/Unclecheng-li/Hello-AI.git
cd Hello-AI
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 启动预览

```bash
mkdocs serve
```

然后访问：

```text
http://127.0.0.1:8000/
```

---

## 本地检查

项目提供了本地构建检查脚本：

```bash
python scripts/build_local.py
```

检查内容包括：

- MkDocs 导航引用是否正确；
- 文档内部链接是否可解析；
- 静态资源引用是否存在；
- MkDocs 严格构建是否通过。

如果只是执行 MkDocs 构建，也可以运行：

```bash
mkdocs build --strict
```

---

## 项目结构

```text
Hello-AI/
├── .github/
│   └── workflows/
│       └── deploy.yml          # GitHub Pages 自动构建与发布
├── assets/                     # 项目级图片与附件
├── docs/                       # 站点正文内容
│   ├── index.md                # 首页
│   ├── preface/                # 前言与学习路线
│   ├── basics/                 # AI / LLM 基础
│   ├── prompt/                 # Prompt 工程入门
│   ├── tools/                  # AI 工具使用
│   ├── rag/                    # RAG 入门
│   ├── agent/                  # Agent 智能体
│   ├── build/                  # AI 应用开发实战
│   ├── eval/                   # AI 评测
│   ├── safety/                 # AI 与大模型安全
│   ├── lab/                    # 实验练习
│   └── resources/              # 相关资源
├── overrides/                  # MkDocs Material 主题覆盖
├── scripts/                    # 本地检查与构建脚本
├── mkdocs.yml                  # MkDocs 配置与导航
├── requirements.txt            # Python 依赖
├── LICENSE                     # 开源许可证
└── README.md                   # 项目说明
```

> `archive/`、`research/`、`.workbuddy/` 等目录用于本地资料沉淀或工作流记录，不作为站点正式内容发布。

---

## 发布方式

Hello-AI 当前采用 GitHub Pages 单发布策略：

```text
提交到 main 分支
  -> GitHub Actions 触发构建
  -> 安装 MkDocs 依赖
  -> 执行严格构建
  -> 发布到 GitHub Pages
```

核心原则：

- GitHub 仓库是唯一内容源；
- 所有正式页面都放在 `docs/` 下；
- `mkdocs.yml` 负责站点导航；
- GitHub Actions 负责自动构建；
- GitHub Pages 负责公开访问。

---

## 编写约定

为了让文档对新手更友好，正文内容建议遵循以下约定：

1. **先讲问题，再讲概念**：不要一上来堆定义，先说明这个概念解决什么困惑。
2. **少用黑话，必要时解释黑话**：首次出现的术语尽量给出简短解释。
3. **优先给路径，不只给资料**：告诉读者先学什么、后学什么、学到什么程度即可。
4. **示例要能运行或能复现**：Prompt、API、RAG、Agent 示例尽量避免只停留在口号。
5. **安全边界要写清楚**：涉及 API Key、数据上传、模型输出、自动化调用时，要提醒风险。
6. **避免制造焦虑**：Hello-AI 的目标是降低入门门槛，不是用概念堆叠劝退新手。

---

## 技术栈

| 类型 | 方案 |
| --- | --- |
| 文档格式 | Markdown |
| 站点生成 | MkDocs |
| 主题 | MkDocs Material |
| 扩展 | pymdown-extensions |
| 搜索 | MkDocs Material 内置搜索 |
| 构建检查 | Python 脚本 + MkDocs strict build |
| 自动发布 | GitHub Actions |
| 托管 | GitHub Pages |

---

## 许可证

本项目使用 [MIT License](LICENSE)。

---

<div align="center">

**Hello-AI — 给中文 AI 初学者的一条清晰入口路径。**

</div>
