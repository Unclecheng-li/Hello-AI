# Hello-AI

Hello-AI 是一个面向中文用户的 AI / LLM 学习入口平台，目标是把基础认知、Prompt、工具、RAG、Agent、Build、Eval 和 Safety 串成一条能走通的学习路径。

## 当前状态

项目已完成站点骨架、基础导航、GitHub Pages 发布和自动构建。

## 本地预览

```bash
pip install -r requirements.txt
mkdocs serve
```

然后访问 `http://127.0.0.1:8000/`。

## 目录说明

- `docs/`：正文内容
- `assets/`：图片与附件
- `overrides/`：主题覆盖
- `scripts/`：检查与构建脚本
- `.github/workflows/`：CI/CD

## 发布方式

- 仓库是唯一内容源
- GitHub Actions 负责构建
- GitHub Pages 负责公开镜像
- 后续可同步到自有服务器主站

## 贡献方式

欢迎通过 issue 和 PR 补充内容、修正文档和扩展案例。
