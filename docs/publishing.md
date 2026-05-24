# 发布流程

Hello-AI 采用仓库为真源的发布方式。

## 当前链路

1. 仓库提交 Markdown
2. GitHub Actions 构建站点
3. 产物发布到 GitHub Pages
4. 未来同步到自有服务器主站

## 自有服务器预留

仓库已预留 `server-deploy` job。默认不执行；当服务器、密钥和 Nginx 目录准备好后，可设置 `ENABLE_SERVER_DEPLOY=true` 再接入 SSH/rsync/原子切换流程。

## 发布原则

- 仓库是唯一内容源
- 页面只读，不在站点上反向改正文
- 每次发布都能回滚到上一版
