# 文档 Lint 规则

1. `structure/nav-missing-file`：`mkdocs.yml` 的 `nav` 引用了不存在的 `docs/` 内 Markdown 文件。
2. `structure/nav-orphan-file`：`docs/**/*.md` 存在，但没有出现在 `mkdocs.yml` 的 `nav` 中。
3. `structure/nav-duplicate-file`：同一个 Markdown 文件在 `nav` 中出现超过一次。
4. `structure/docs-outside-nav-root`：正文 Markdown 不在 `docs/` 目录下。
5. `structure/empty-markdown-file`：Markdown 文件去掉空白后为空。
6. `frontmatter/invalid-yaml`：文件以 frontmatter 开头，但 YAML 无法解析。
7. `frontmatter/tags-not-list`：frontmatter 中的 `tags` 不是列表。
8. `frontmatter/unknown-tag`：frontmatter 中的 tag 不在 `mkdocs.yml` 的 `material/tags.tags_allowed` 中。
9. `frontmatter/duplicate-tag`：同一页面 frontmatter 中出现重复 tag。
10. `markdown/missing-h1`：页面没有一级标题 `#`。
11. `markdown/multiple-h1`：同一页面出现多个一级标题。
12. `markdown/heading-jump`：标题层级跳跃超过 1 级，例如从 `##` 直接到 `####`。
13. `markdown/duplicate-heading`：同一页面出现完全相同的标题文本。
14. `markdown/empty-link-text`：Markdown 链接文本为空，例如 `[](target.md)`。
15. `markdown/empty-link-target`：Markdown 链接目标为空，例如 `[text]()`。
16. `markdown/local-link-missing-file`：本地 Markdown 链接指向不存在的文件。
17. `markdown/local-link-missing-anchor`：本地 Markdown 链接包含锚点，但目标文件中找不到对应标题锚点。
18. `markdown/fenced-code-missing-language`：围栏代码块没有声明语言。
19. `markdown/trailing-whitespace`：行尾存在多余空格；Markdown 强制换行的两个空格可单独允许。
20. `markdown/no-final-newline`：文件末尾没有换行符。
21. `markdown/tabs-indent`：缩进中出现 tab 字符。
22. `asset/local-image-missing`：Markdown 图片或 HTML `src` 指向的本地图片不存在。
23. `asset/local-src-missing`：HTML `src` 指向的本地资源不存在。
24. `asset/unsafe-relative-path`：本地资源路径解析后逃出仓库根目录。
25. `image/empty-alt`：Markdown 图片 alt 文本为空，例如 `![](x.png)`。
26. `image/external-image`：Markdown 图片或 HTML `src` 使用 `http://` 或 `https://` 外链图片。
27. `image/data-uri`：图片使用 `data:` 内联资源。
28. `image/path-convention`：正文引用的本地图片不在 `docs/assets/images/` 或 `docs/assets/mermaid/` 下。
29. `image/name-convention`：图片文件名不符合小写英文、数字、连字符和点号规则。
30. `image/file-too-large`：单张图片文件大小超过设定阈值。
31. `image/raster-too-wide`：PNG/JPEG/WebP/GIF 宽度超过设定阈值。
32. `image/raster-too-tall`：PNG/JPEG/WebP/GIF 高度超过设定阈值。
33. `image/raster-ext-unsupported`：正文引用的位图格式不在允许列表内。
34. `image/svg-missing-viewbox`：SVG 文件缺少 `viewBox`。
35. `image/svg-empty-title-or-label`：SVG 缺少 `title`、`aria-label` 或等价可访问名称。
36. `image/animated-gif`：正文引用 GIF 动图。
37. `mermaid/codeblock-empty`：Mermaid 代码块内容为空。
38. `mermaid/compile-failed`：Mermaid 代码块无法被 `mmdc` 编译。
39. `mermaid/render-output-missing`：Mermaid 编译后没有生成 SVG。
40. `mermaid/svg-missing-viewbox`：Mermaid 生成的 SVG 缺少 `viewBox`。
41. `mermaid/aspect-ratio-tall`：Mermaid 生成 SVG 的高宽比超过设定阈值。
42. `mermaid/aspect-ratio-wide`：Mermaid 生成 SVG 的宽高比超过设定阈值。
43. `mermaid/render-too-wide`：Mermaid 生成 SVG 的宽度超过设定阈值。
44. `mermaid/vertical-flow-long`：`flowchart TD`、`flowchart TB`、`graph TD` 或 `graph TB` 的最长链路节点数超过设定阈值。
45. `mermaid/node-count-high`：单个 Mermaid 图的节点数超过设定阈值。
46. `mermaid/edge-count-high`：单个 Mermaid 图的连线数超过设定阈值。
47. `mermaid/node-label-too-long`：Mermaid 节点标签字符数超过设定阈值。
48. `mermaid/subgraph-count-high`：单个 Mermaid 图的 `subgraph` 数量超过设定阈值。
49. `mermaid/subgraph-nested`：Mermaid 出现嵌套 `subgraph`。
50. `mermaid/details-wrapper`：超阈值 Mermaid 图没有包在 `<details>` 中；该规则只提示，不代表推荐长图。
51. `format/line-too-long`：单行长度超过设定阈值；中文正文行可配置为跳过。
52. `format/list-indent-inconsistent`：同一列表块缩进宽度不一致。
53. `format/table-column-mismatch`：Markdown 表格行列数不一致。
54. `format/html-tag-unclosed`：允许检查的内联 HTML 标签没有闭合。
55. `lint/unknown-disable-rule`：跳过注释中引用了不存在的规则名。
56. `lint/unused-disable`：跳过注释没有实际跳过任何警告。
57. `lint/disable-missing-reason`：跳过注释没有填写原因。
58. 下一行跳过格式：`<!-- hello-ai-lint-disable-next-line rule/name: reason -->`。
59. 文件级跳过格式：`<!-- hello-ai-lint-disable rule/name: reason -->`。
60. 同一条跳过注释可以包含多个规则名，规则名用空格分隔。
61. 跳过注释只影响文档 lint 警告，不影响 `mkdocs build --strict` 这类构建错误。
62. 文档 lint 默认输出 warning，不因 warning 返回失败状态。
63. 文档 lint 报告必须包含文件路径、行号、规则名、说明和建议。
64. CI 中的文档 lint 也默认只输出报告，不阻塞 PR。
65. 构建完整性检查不属于 warning-only lint；导航缺失、坏链、缺资源和严格构建失败可以继续阻塞。
