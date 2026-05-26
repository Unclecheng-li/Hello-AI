from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import struct
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote

import yaml

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
DESIGN = ROOT / "DESIGN.md"
MKDOCS = ROOT / "mkdocs.yml"

MAX_VERTICAL_MERMAID_CHAIN_NODES = 10
MAX_MERMAID_NODES = 20
MAX_MERMAID_EDGES = 24
MAX_MERMAID_SUBGRAPHS = 5
MAX_MERMAID_LABEL_CHARS = 50
MAX_LINE_CHARS = 120
MAX_IMAGE_BYTES = 2_000_000
MAX_RASTER_WIDTH = 2560
MAX_RASTER_HEIGHT = 1440
MAX_MERMAID_RENDER_WIDTH = 3200.0
MAX_MERMAID_TALL_RATIO = 1.5
MAX_MERMAID_WIDE_RATIO = 8.0
MERMAID_COMPACT_RULES = {
    "mermaid/aspect-ratio-tall",
    "mermaid/aspect-ratio-wide",
    "mermaid/render-too-wide",
    "mermaid/vertical-flow-long",
    "mermaid/details-wrapper",
    "mermaid/node-count-high",
    "mermaid/edge-count-high",
    "mermaid/subgraph-count-high",
}

IMAGE_ROOTS = (DOCS / "assets" / "images", DOCS / "assets" / "mermaid")
ALLOWED_RASTER_EXTS = {".png", ".jpg", ".jpeg", ".webp"}
ALLOWED_IMAGE_EXTS = ALLOWED_RASTER_EXTS | {".svg", ".gif"}
VOID_HTML_TAGS = {
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
}
CHECKED_HTML_TAGS = {
    "a",
    "abbr",
    "b",
    "center",
    "code",
    "del",
    "details",
    "div",
    "em",
    "i",
    "ins",
    "kbd",
    "mark",
    "small",
    "span",
    "strong",
    "sub",
    "summary",
    "sup",
    "u",
}

FENCE_RE = re.compile(r"^(```|~~~)\s*([^`]*)\s*$")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
LINK_RE = re.compile(r"(?<!!)\[([^\]]*)\]\(([^)]+)\)")
IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
HTML_SRC_RE = re.compile(r"src=[\"']([^\"']+)[\"']")
HTML_TAG_RE = re.compile(r"<\s*(/?)\s*([A-Za-z][A-Za-z0-9:-]*)([^<>]*?)(/?)\s*>")
TABLE_SEPARATOR_RE = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$")
MERMAID_ARROW_RE = re.compile(r"-->|---|-.->|==>")
MERMAID_NODE_ID_RE = re.compile(r"^\s*([A-Za-z][A-Za-z0-9_]*)")
DISABLE_RE = re.compile(
    r"<!--\s*(hello-ai-lint-disable(?:-next-line)?)\s+([^:>]+)(?::\s*([^>]*?))?\s*-->",
)
RULE_RE = re.compile(r"^\d+\.\s+`([^`]+/[a-z0-9-]+)`：")
CJK_RE = re.compile(r"[\u3400-\u9fff]")
SVG_OPEN_RE = re.compile(r"<svg\b[^>]*>", re.IGNORECASE)
SVG_ATTR_RE = re.compile(r"([A-Za-z_:][-A-Za-z0-9_:.]*)\s*=\s*(['\"])(.*?)\2", re.DOTALL)
PYTHON_HINT_RE = re.compile(r"^\s*(from\s+\S+\s+import|import\s+\S+|def\s+\w+\(|class\s+\w+|print\()", re.MULTILINE)
SHELL_HINT_RE = re.compile(
    r"^\s*(?:\$ |cd\s+|git\s+|python(?:3)?\s+|pip\s+|uv\s+|npm\s+|pnpm\s+|bun\s+|mkdocs\s+|mmdc\s+|curl\s+|wget\s+|docker\s+|omx\s+)",
    re.MULTILINE,
)


class MkDocsLoader(yaml.SafeLoader):
    pass


def ignore_python_name(loader: MkDocsLoader, suffix: str, node: yaml.Node) -> str:
    return suffix


MkDocsLoader.add_multi_constructor(
    "tag:yaml.org,2002:python/name:",
    ignore_python_name,
)


@dataclass(frozen=True)
class Finding:
    rule: str
    path: Path
    line: int
    message: str
    suggestion: str


@dataclass(frozen=True)
class CodeBlock:
    language: str
    body: str
    start_line: int
    end_line: int


@dataclass(frozen=True)
class SvgInfo:
    has_viewbox: bool
    width: float | None
    height: float | None
    has_accessible_name: bool


@dataclass
class DisableState:
    file_rules: dict[str, tuple[int, bool]]
    next_line_rules: dict[int, dict[str, tuple[int, bool]]]
    findings: list[Finding]


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def line_for_offset(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def markdown_files() -> list[Path]:
    return sorted(DOCS.rglob("*.md"))


def scoped_paths(path: Path) -> tuple[list[Path] | None, bool]:
    if not path:
        return None, False
    if not path.exists():
        return [], False

    files: list[Path] = []
    includes_mkdocs = False
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        raw_line = raw_line.strip()
        if not raw_line:
            continue
        candidate = (ROOT / raw_line).resolve(strict=False)
        if candidate == MKDOCS:
            includes_mkdocs = True
            continue
        try:
            in_docs = candidate.is_relative_to(DOCS)
        except AttributeError:
            in_docs = DOCS in candidate.parents or candidate == DOCS
        if in_docs and candidate.suffix == ".md" and candidate.exists():
            files.append(candidate)

    return sorted(set(files)), includes_mkdocs


def known_rules() -> set[str]:
    if not DESIGN.exists():
        return set()
    rules: set[str] = set()
    for line in DESIGN.read_text(encoding="utf-8").splitlines():
        match = RULE_RE.match(line)
        if match:
            rules.add(match.group(1))
    return rules


def load_config() -> dict[str, object]:
    return yaml.load(MKDOCS.read_text(encoding="utf-8"), Loader=MkDocsLoader)


def allowed_tags(config: dict[str, object]) -> set[str]:
    tags: set[str] = set()
    plugins = config.get("plugins", [])
    if not isinstance(plugins, list):
        return tags
    for plugin in plugins:
        if isinstance(plugin, dict) and "material/tags" in plugin:
            options = plugin.get("material/tags") or {}
            if isinstance(options, dict):
                raw_tags = options.get("tags_allowed", [])
                if isinstance(raw_tags, list):
                    tags.update(str(tag) for tag in raw_tags)
    return tags


def nav_paths(config: dict[str, object]) -> list[Path]:
    paths: list[Path] = []

    def walk(items: object) -> None:
        if isinstance(items, str):
            paths.append(Path(items))
            return
        if isinstance(items, list):
            for item in items:
                walk(item)
            return
        if isinstance(items, dict):
            for value in items.values():
                walk(value)

    walk(config.get("nav", []))
    return paths


def fenced_line_numbers(text: str) -> set[int]:
    lines = text.splitlines()
    in_fence = False
    fence = ""
    blocked: set[int] = set()
    for index, line in enumerate(lines, start=1):
        match = FENCE_RE.match(line)
        if match and not in_fence:
            in_fence = True
            fence = match.group(1)
            blocked.add(index)
            continue
        if in_fence:
            blocked.add(index)
            if line.startswith(fence):
                in_fence = False
                fence = ""
    return blocked


def code_blocks(text: str) -> list[CodeBlock]:
    lines = text.splitlines()
    blocks: list[CodeBlock] = []
    in_fence = False
    fence = ""
    language = ""
    start = 0
    body: list[str] = []

    for index, line in enumerate(lines, start=1):
        match = FENCE_RE.match(line)
        if match and not in_fence:
            in_fence = True
            fence = match.group(1)
            raw_language = match.group(2).strip()
            language = raw_language.split()[0] if raw_language else ""
            start = index
            body = []
            continue
        if in_fence and line.startswith(fence):
            blocks.append(CodeBlock(language=language, body="\n".join(body), start_line=start, end_line=index))
            in_fence = False
            fence = ""
            continue
        if in_fence:
            body.append(line)

    if in_fence:
        blocks.append(CodeBlock(language=language, body="\n".join(body), start_line=start, end_line=len(lines)))
    return blocks


def infer_code_language(body: str) -> str:
    stripped = body.strip()
    if not stripped:
        return "text"
    if stripped[0] in "[{":
        try:
            json.loads(stripped)
        except json.JSONDecodeError:
            pass
        else:
            return "json"
    if PYTHON_HINT_RE.search(body):
        return "python"
    if SHELL_HINT_RE.search(body):
        return "bash"
    return "text"


def has_allowed_hard_break(line: str) -> bool:
    return bool(line.strip()) and line.endswith("  ") and not line.endswith("   ")


def line_length_exempt(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return True
    if CJK_RE.search(line):
        return True
    if stripped.startswith(("http://", "https://")):
        return True
    if IMAGE_RE.search(line) or LINK_RE.search(line):
        return True
    if stripped.startswith("<") and ">" in stripped:
        return True
    return False


def apply_safe_fixes(path: Path) -> bool:
    original = path.read_text(encoding="utf-8")
    lines = original.splitlines()
    blocked = fenced_line_numbers(original)

    fixed_lines: list[str] = []
    for line_no, line in enumerate(lines, start=1):
        fixed = line
        if line_no not in blocked:
            leading = re.match(r"^[\t ]+", fixed)
            if leading and "\t" in leading.group(0):
                expanded = leading.group(0).replace("\t", "    ")
                fixed = f"{expanded}{fixed[len(leading.group(0)):]}"
            if not has_allowed_hard_break(fixed):
                fixed = fixed.rstrip(" \t")
        fixed_lines.append(fixed)

    text = "\n".join(fixed_lines)
    if text:
        text += "\n"

    lines = text.splitlines()
    for block in code_blocks(text):
        if block.language:
            continue
        index = block.start_line - 1
        if index < 0 or index >= len(lines):
            continue
        match = FENCE_RE.match(lines[index])
        if not match:
            continue
        lines[index] = f"{match.group(1)}{infer_code_language(block.body)}"

    fixed_text = "\n".join(lines)
    if fixed_text:
        fixed_text += "\n"

    if fixed_text != original:
        path.write_text(fixed_text, encoding="utf-8")
        return True
    return False


def parse_frontmatter(path: Path, text: str, allowed: set[str]) -> list[Finding]:
    findings: list[Finding] = []
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        return findings

    end = None
    for index, line in enumerate(lines[1:], start=2):
        if line == "---":
            end = index
            break
    if end is None:
        findings.append(
            Finding(
                "frontmatter/invalid-yaml",
                path,
                1,
                "frontmatter 没有闭合的 --- 分隔符。",
                "补全结束分隔符，或删除不完整的 frontmatter。",
            )
        )
        return findings

    raw = "\n".join(lines[1 : end - 1])
    try:
        data = yaml.safe_load(raw) or {}
    except yaml.YAMLError as exc:
        findings.append(
            Finding(
                "frontmatter/invalid-yaml",
                path,
                1,
                f"frontmatter YAML 无法解析：{exc.__class__.__name__}。",
                "修正 YAML 缩进、冒号和列表格式。",
            )
        )
        return findings

    if not isinstance(data, dict):
        return findings

    if "tags" not in data:
        return findings

    tags = data["tags"]
    if not isinstance(tags, list):
        findings.append(
            Finding(
                "frontmatter/tags-not-list",
                path,
                1,
                "frontmatter.tags 不是列表。",
                "改成 tags: 下的 YAML 列表。",
            )
        )
        return findings

    seen: set[str] = set()
    for tag in tags:
        tag_text = str(tag)
        if tag_text in seen:
            findings.append(
                Finding(
                    "frontmatter/duplicate-tag",
                    path,
                    1,
                    f"重复 tag：{tag_text}。",
                    "删除重复 tag。",
                )
            )
        seen.add(tag_text)
        if allowed and tag_text not in allowed:
            findings.append(
                Finding(
                    "frontmatter/unknown-tag",
                    path,
                    1,
                    f"未知 tag：{tag_text}。",
                    "使用 mkdocs.yml 的 material/tags.tags_allowed 中的 tag，或先更新白名单。",
                )
            )
    return findings


def normalized_heading(text: str) -> str:
    text = re.sub(r"\s+#+\s*$", "", text).strip()
    return re.sub(r"\s+", " ", text)


def anchor_for_heading(text: str) -> str:
    text = normalized_heading(text).lower()
    text = re.sub(r"[`*_~\[\](){}.!?,:;，。！？、：；（）【】《》\"']", "", text)
    text = re.sub(r"\s+", "-", text)
    return text.strip("-")


def collect_anchors(path: Path) -> set[str]:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return set()
    blocked = fenced_line_numbers(text)
    anchors: set[str] = set()
    for line_no, line in enumerate(text.splitlines(), start=1):
        if line_no in blocked:
            continue
        match = HEADING_RE.match(line)
        if match:
            anchors.add(anchor_for_heading(match.group(2)))
    return anchors


def lint_headings(path: Path, text: str) -> list[Finding]:
    findings: list[Finding] = []
    blocked = fenced_line_numbers(text)
    h1_lines: list[int] = []
    previous_level = 0
    headings: dict[str, int] = {}

    for line_no, line in enumerate(text.splitlines(), start=1):
        if line_no in blocked:
            continue
        match = HEADING_RE.match(line)
        if not match:
            continue
        level = len(match.group(1))
        title = normalized_heading(match.group(2))
        if level == 1:
            h1_lines.append(line_no)
        if previous_level and level > previous_level + 1:
            findings.append(
                Finding(
                    "markdown/heading-jump",
                    path,
                    line_no,
                    f"标题从 H{previous_level} 跳到 H{level}。",
                    "按层级补上中间标题，或把当前标题降回相邻层级。",
                )
            )
        previous_level = level
        if title in headings:
            findings.append(
                Finding(
                    "markdown/duplicate-heading",
                    path,
                    line_no,
                    f"重复标题：{title}。",
                    "改成更具体的标题，避免生成重复锚点。",
                )
            )
        else:
            headings[title] = line_no

    if not h1_lines:
        findings.append(
            Finding(
                "markdown/missing-h1",
                path,
                1,
                "页面没有一级标题。",
                "在页面开头添加一个 # 标题。",
            )
        )
    elif len(h1_lines) > 1:
        for line_no in h1_lines[1:]:
            findings.append(
                Finding(
                    "markdown/multiple-h1",
                    path,
                    line_no,
                    "同一页面出现多个一级标题。",
                    "保留一个页面级 H1，其余改为 H2 或更低层级。",
                )
            )
    return findings


def clean_target(raw_target: str) -> str:
    target = raw_target.strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1].strip()
    return target.split()[0] if target else target


def is_external(target: str) -> bool:
    return target.startswith(("http://", "https://", "mailto:", "tel:"))


def is_relative_to(path: Path, root: Path) -> bool:
    try:
        return path.is_relative_to(root)
    except AttributeError:
        return root in path.parents or path == root


def format_bytes(size: int) -> str:
    if size >= 1_000_000:
        return f"{size / 1_000_000:.1f} MB"
    if size >= 1_000:
        return f"{size / 1_000:.1f} KB"
    return f"{size} B"


def parse_svg_attrs(svg_text: str) -> dict[str, str]:
    match = SVG_OPEN_RE.search(svg_text)
    if not match:
        return {}
    return {name.lower(): value for name, _quote, value in SVG_ATTR_RE.findall(match.group(0))}


def parse_dimension(value: str | None) -> float | None:
    if not value:
        return None
    if "%" in value:
        return None
    match = re.match(r"\s*([0-9]+(?:\.[0-9]+)?)(?:px)?\s*$", value)
    return float(match.group(1)) if match else None


def parse_viewbox(value: str | None) -> tuple[float, float] | None:
    if not value:
        return None
    parts = re.split(r"[\s,]+", value.strip())
    if len(parts) != 4:
        return None
    try:
        width = float(parts[2])
        height = float(parts[3])
    except ValueError:
        return None
    if width <= 0 or height <= 0:
        return None
    return width, height


def svg_info(svg_text: str) -> SvgInfo:
    attrs = parse_svg_attrs(svg_text)
    viewbox = parse_viewbox(attrs.get("viewbox"))
    if viewbox:
        width, height = viewbox
    else:
        width = parse_dimension(attrs.get("width"))
        height = parse_dimension(attrs.get("height"))
    has_accessible_name = bool(
        attrs.get("aria-label", "").strip()
        or attrs.get("aria-labelledby", "").strip()
        or re.search(r"<title\b[^>]*>\s*[^<\s][^<]*</title>", svg_text, flags=re.IGNORECASE | re.DOTALL)
    )
    return SvgInfo(has_viewbox=viewbox is not None, width=width, height=height, has_accessible_name=has_accessible_name)


def png_dimensions(data: bytes) -> tuple[int, int] | None:
    if len(data) >= 24 and data.startswith(b"\x89PNG\r\n\x1a\n"):
        return struct.unpack(">II", data[16:24])
    return None


def gif_dimensions(data: bytes) -> tuple[int, int] | None:
    if len(data) >= 10 and data[:6] in (b"GIF87a", b"GIF89a"):
        return struct.unpack("<HH", data[6:10])
    return None


def jpeg_dimensions(data: bytes) -> tuple[int, int] | None:
    if len(data) < 4 or not data.startswith(b"\xff\xd8"):
        return None
    index = 2
    while index + 9 < len(data):
        if data[index] != 0xFF:
            index += 1
            continue
        marker = data[index + 1]
        index += 2
        while marker == 0xFF and index < len(data):
            marker = data[index]
            index += 1
        if marker in {0xD8, 0xD9}:
            continue
        if index + 2 > len(data):
            return None
        length = struct.unpack(">H", data[index : index + 2])[0]
        if length < 2 or index + length > len(data):
            return None
        if marker in {
            0xC0,
            0xC1,
            0xC2,
            0xC3,
            0xC5,
            0xC6,
            0xC7,
            0xC9,
            0xCA,
            0xCB,
            0xCD,
            0xCE,
            0xCF,
        }:
            height = struct.unpack(">H", data[index + 3 : index + 5])[0]
            width = struct.unpack(">H", data[index + 5 : index + 7])[0]
            return width, height
        index += length
    return None


def webp_dimensions(data: bytes) -> tuple[int, int] | None:
    if len(data) < 30 or data[:4] != b"RIFF" or data[8:12] != b"WEBP":
        return None
    chunk = data[12:16]
    if chunk == b"VP8X" and len(data) >= 30:
        width = 1 + int.from_bytes(data[24:27], "little")
        height = 1 + int.from_bytes(data[27:30], "little")
        return width, height
    if chunk == b"VP8 " and len(data) >= 30:
        start = data.find(b"\x9d\x01\x2a", 20)
        if start != -1 and start + 7 <= len(data):
            width = struct.unpack("<H", data[start + 3 : start + 5])[0] & 0x3FFF
            height = struct.unpack("<H", data[start + 5 : start + 7])[0] & 0x3FFF
            return width, height
    if chunk == b"VP8L" and len(data) >= 25 and data[20] == 0x2F:
        bits = int.from_bytes(data[21:25], "little")
        width = (bits & 0x3FFF) + 1
        height = ((bits >> 14) & 0x3FFF) + 1
        return width, height
    return None


def raster_dimensions(path: Path) -> tuple[int, int] | None:
    data = path.read_bytes()
    ext = path.suffix.lower()
    if ext == ".png":
        return png_dimensions(data)
    if ext in {".jpg", ".jpeg"}:
        return jpeg_dimensions(data)
    if ext == ".gif":
        return gif_dimensions(data)
    if ext == ".webp":
        return webp_dimensions(data)
    return None


def mermaid_render_config() -> dict[str, object]:
    return {
        "htmlLabels": False,
        "flowchart": {"htmlLabels": False},
        "class": {"htmlLabels": False},
    }


def mermaid_puppeteer_config() -> dict[str, object]:
    args = [
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--disable-dev-shm-usage",
    ]
    if os.getenv("CI") or os.getenv("GITHUB_ACTIONS"):
        args.extend(["--single-process", "--no-zygote"])

    config: dict[str, object] = {"args": args}
    chrome_path = (
        shutil.which("google-chrome")
        or shutil.which("chromium-browser")
        or shutil.which("chromium")
    )
    if chrome_path:
        config["executablePath"] = chrome_path
    return config


def resolve_local(path: Path, target: str) -> tuple[Path | None, str]:
    target = clean_target(target)
    plain = target.split("?", 1)[0]
    file_part, _, anchor = plain.partition("#")
    file_part = unquote(file_part)
    if not file_part:
        return path, anchor
    candidate = (DOCS / file_part.lstrip("/")) if file_part.startswith("/") else (path.parent / file_part)
    resolved = candidate.resolve(strict=False)
    try:
        if not resolved.is_relative_to(ROOT):
            return None, anchor
    except AttributeError:
        if ROOT not in resolved.parents and resolved != ROOT:
            return None, anchor
    return resolved, anchor


def lint_links(path: Path, text: str) -> list[Finding]:
    findings: list[Finding] = []
    blocked = fenced_line_numbers(text)
    anchor_cache: dict[Path, set[str]] = {}

    for match in LINK_RE.finditer(text):
        line_no = line_for_offset(text, match.start())
        if line_no in blocked:
            continue
        link_text = match.group(1).strip()
        target = clean_target(match.group(2))
        if not link_text:
            findings.append(
                Finding("markdown/empty-link-text", path, line_no, "链接文本为空。", "补充可读的链接文本。")
            )
        if not target:
            findings.append(
                Finding("markdown/empty-link-target", path, line_no, "链接目标为空。", "补充链接目标或删除空链接。")
            )
            continue
        if is_external(target):
            continue
        resolved, anchor = resolve_local(path, target)
        if resolved is None:
            findings.append(
                Finding(
                    "asset/unsafe-relative-path",
                    path,
                    line_no,
                    f"链接路径逃出仓库：{target}。",
                    "改用仓库内的相对路径。",
                )
            )
            continue
        if resolved != path and not resolved.exists():
            findings.append(
                Finding(
                    "markdown/local-link-missing-file",
                    path,
                    line_no,
                    f"本地链接目标不存在：{target}。",
                    "修正路径，或先补充目标文件。",
                )
            )
            continue
        if anchor and resolved.suffix == ".md":
            anchors = anchor_cache.setdefault(resolved, collect_anchors(resolved))
            if anchor not in anchors:
                findings.append(
                    Finding(
                        "markdown/local-link-missing-anchor",
                        path,
                        line_no,
                        f"链接锚点不存在：#{anchor}。",
                        "检查目标页面标题，或修正锚点。",
                    )
                )
    return findings


def lint_local_image(path: Path, line_no: int, resolved: Path) -> list[Finding]:
    findings: list[Finding] = []
    ext = resolved.suffix.lower()

    if not any(is_relative_to(resolved, root) for root in IMAGE_ROOTS):
        findings.append(
            Finding(
                "image/path-convention",
                path,
                line_no,
                f"图片不在 docs/assets/images/ 或 docs/assets/mermaid/ 下：{rel(resolved)}。",
                "移动到 docs/assets/images/<章节>/，或确认是否应引用 Mermaid 生成目录。",
            )
        )

    if resolved.stat().st_size > MAX_IMAGE_BYTES:
        findings.append(
            Finding(
                "image/file-too-large",
                path,
                line_no,
                f"图片文件过大：{format_bytes(resolved.stat().st_size)}。",
                f"压缩图片，或控制在 {format_bytes(MAX_IMAGE_BYTES)} 以内。",
            )
        )

    if ext not in ALLOWED_IMAGE_EXTS:
        findings.append(
            Finding(
                "image/raster-ext-unsupported",
                path,
                line_no,
                f"图片格式不在允许列表内：{ext or '(无扩展名)'}。",
                "优先使用 PNG、JPEG、WebP 或 SVG。",
            )
        )
        return findings

    if ext == ".gif":
        findings.append(
            Finding(
                "image/animated-gif",
                path,
                line_no,
                "正文引用了 GIF 动图。",
                "优先改为静态图、短视频链接，或拆成多张静态图。",
            )
        )

    if ext == ".svg":
        svg = resolved.read_text(encoding="utf-8", errors="replace")
        info = svg_info(svg)
        if not info.has_viewbox:
            findings.append(
                Finding(
                    "image/svg-missing-viewbox",
                    path,
                    line_no,
                    f"SVG 缺少 viewBox：{rel(resolved)}。",
                    "补充 viewBox，保证响应式缩放稳定。",
                )
            )
        if not info.has_accessible_name:
            findings.append(
                Finding(
                    "image/svg-empty-title-or-label",
                    path,
                    line_no,
                    f"SVG 缺少 title、aria-label 或 aria-labelledby：{rel(resolved)}。",
                    "补充可访问名称，或确认该图是否应作为装饰图处理。",
                )
            )
        return findings

    dimensions = raster_dimensions(resolved)
    if dimensions:
        width, height = dimensions
        if width > MAX_RASTER_WIDTH:
            findings.append(
                Finding(
                    "image/raster-too-wide",
                    path,
                    line_no,
                    f"位图宽度为 {width}px，超过阈值 {MAX_RASTER_WIDTH}px。",
                    "缩小导出尺寸，或改用 SVG / Mermaid。",
                )
            )
        if height > MAX_RASTER_HEIGHT:
            findings.append(
                Finding(
                    "image/raster-too-tall",
                    path,
                    line_no,
                    f"位图高度为 {height}px，超过阈值 {MAX_RASTER_HEIGHT}px。",
                    "拆分长图，或缩小导出尺寸。",
                )
            )
    return findings


def lint_images(path: Path, text: str) -> list[Finding]:
    findings: list[Finding] = []
    blocked = fenced_line_numbers(text)

    for match in IMAGE_RE.finditer(text):
        line_no = line_for_offset(text, match.start())
        if line_no in blocked:
            continue
        alt = match.group(1).strip()
        target = clean_target(match.group(2))
        if not alt:
            findings.append(Finding("image/empty-alt", path, line_no, "图片 alt 文本为空。", "补充能说明图片内容的 alt 文本。"))
        if target.startswith(("http://", "https://")):
            findings.append(
                Finding("image/external-image", path, line_no, "图片直接引用外部 URL。", "下载到仓库内并使用本地相对路径，避免外链失效。")
            )
            continue
        if target.startswith("data:"):
            findings.append(Finding("image/data-uri", path, line_no, "图片使用 data URI。", "改成仓库内图片文件。"))
            continue
        resolved, _anchor = resolve_local(path, target)
        if resolved is None:
            findings.append(Finding("asset/unsafe-relative-path", path, line_no, f"图片路径逃出仓库：{target}。", "改用仓库内的相对路径。"))
            continue
        if not resolved.exists():
            findings.append(Finding("asset/local-image-missing", path, line_no, f"本地图片不存在：{target}。", "修正路径，或先补充图片文件。"))
            continue
        if not re.fullmatch(r"[a-z0-9][a-z0-9_-]*\.(png|jpe?g|webp|svg|gif)", resolved.name):
            findings.append(
                Finding("image/name-convention", path, line_no, f"图片文件名不符合小写短横线/下划线规范：{resolved.name}。", "改成小写英文、数字、- 或 _ 命名。")
            )
        findings.extend(lint_local_image(path, line_no, resolved))

    for match in HTML_SRC_RE.finditer(text):
        line_no = line_for_offset(text, match.start())
        if line_no in blocked:
            continue
        target = clean_target(match.group(1))
        if target.startswith(("http://", "https://")):
            findings.append(
                Finding("image/external-image", path, line_no, "HTML src 直接引用外部 URL。", "下载到仓库内并使用本地相对路径，避免外链失效。")
            )
            continue
        if target.startswith("data:"):
            findings.append(Finding("image/data-uri", path, line_no, "HTML src 使用 data URI。", "改成仓库内图片文件。"))
            continue
        resolved, _anchor = resolve_local(path, target)
        if resolved is None:
            findings.append(Finding("asset/unsafe-relative-path", path, line_no, f"HTML src 路径逃出仓库：{target}。", "改用仓库内的相对路径。"))
        elif not resolved.exists():
            findings.append(Finding("asset/local-src-missing", path, line_no, f"HTML src 目标不存在：{target}。", "修正路径，或先补充资源文件。"))
        elif resolved.suffix.lower() in ALLOWED_IMAGE_EXTS:
            findings.extend(lint_local_image(path, line_no, resolved))
    return findings


def mermaid_node_count(body: str) -> int:
    candidates = set(re.findall(r"(?:^|\s)([A-Za-z][A-Za-z0-9_]*)\s*(?:\[|\{|\(|--|==|-.|$)", body, flags=re.MULTILINE))
    return len({candidate for candidate in candidates if candidate not in {"flowchart", "graph", "subgraph", "end"}})


def mermaid_endpoint(segment: str) -> str | None:
    segment = re.sub(r"\|[^|]*\|\s*$", "", segment).strip()
    segment = re.sub(r"^\|[^|]*\|\s*", "", segment).strip()
    match = MERMAID_NODE_ID_RE.match(segment)
    if not match:
        return None
    node = match.group(1)
    if node in {"flowchart", "graph", "subgraph", "end", "direction"}:
        return None
    return node


def mermaid_longest_chain_nodes(body: str) -> int:
    graph: dict[str, set[str]] = {}
    nodes: set[str] = set()
    for raw_line in body.splitlines():
        line = raw_line.split("%%", 1)[0].strip()
        if not line or not MERMAID_ARROW_RE.search(line):
            continue
        parts = MERMAID_ARROW_RE.split(line)
        endpoints = [mermaid_endpoint(part) for part in parts]
        endpoints = [endpoint for endpoint in endpoints if endpoint]
        if len(endpoints) < 2:
            continue
        nodes.update(endpoints)
        for left, right in zip(endpoints, endpoints[1:]):
            graph.setdefault(left, set()).add(right)

    def walk(node: str, seen: set[str]) -> int:
        children = [child for child in graph.get(node, set()) if child not in seen]
        if not children:
            return 1
        return 1 + max(walk(child, seen | {child}) for child in children)

    return max((walk(node, {node}) for node in nodes), default=0)


def render_mermaid_svg(body: str) -> tuple[bool, str, str | None]:
    mmdc = shutil.which("mmdc")
    if not mmdc:
        return True, "", None

    with tempfile.TemporaryDirectory(prefix="hello-ai-mermaid-") as tmp:
        tmpdir = Path(tmp)
        input_path = tmpdir / "diagram.mmd"
        output_path = tmpdir / "diagram.svg"
        config_path = tmpdir / "mermaid.json"
        puppeteer_config_path = tmpdir / "puppeteer.json"
        input_path.write_text(body + "\n", encoding="utf-8")
        config_path.write_text(json.dumps(mermaid_render_config(), ensure_ascii=False), encoding="utf-8")
        puppeteer_config_path.write_text(
            json.dumps(mermaid_puppeteer_config(), ensure_ascii=False),
            encoding="utf-8",
        )
        try:
            result = subprocess.run(
                [
                    mmdc,
                    "-i",
                    str(input_path),
                    "-o",
                    str(output_path),
                    "-c",
                    str(config_path),
                    "-p",
                    str(puppeteer_config_path),
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
                timeout=60,
            )
        except subprocess.TimeoutExpired:
            return False, "mmdc 渲染超时。", None
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "mmdc 返回非零状态。").strip().splitlines()
            return False, detail[0] if detail else "mmdc 返回非零状态。", None
        if not output_path.exists() or output_path.stat().st_size == 0:
            return True, "mmdc 没有生成 SVG 文件。", ""
        return True, "", output_path.read_text(encoding="utf-8", errors="replace")


def lint_mermaid_svg(path: Path, block: CodeBlock, svg_text: str | None, render_message: str) -> list[Finding]:
    findings: list[Finding] = []
    if svg_text is None:
        return findings
    if svg_text == "":
        findings.append(
            Finding(
                "mermaid/render-output-missing",
                path,
                block.start_line,
                render_message or "Mermaid 编译后没有生成 SVG。",
                "检查 mmdc 输出路径和图表语法。",
            )
        )
        return findings

    info = svg_info(svg_text)
    if not info.has_viewbox:
        findings.append(
            Finding(
                "mermaid/svg-missing-viewbox",
                path,
                block.start_line,
                "Mermaid 生成的 SVG 缺少 viewBox。",
                "检查 mmdc 输出；缺少 viewBox 会影响响应式缩放。",
            )
        )
    if not info.width or not info.height:
        return findings

    width = info.width
    height = info.height
    if width > MAX_MERMAID_RENDER_WIDTH:
        findings.append(
            Finding(
                "mermaid/render-too-wide",
                path,
                block.start_line,
                f"Mermaid SVG 宽度为 {width:.0f}px，超过阈值 {MAX_MERMAID_RENDER_WIDTH:.0f}px。",
                "拆分宽图，或减少并列节点数量。",
            )
        )
    tall_ratio = height / width if width else 0
    wide_ratio = width / height if height else 0
    if tall_ratio > MAX_MERMAID_TALL_RATIO:
        findings.append(
            Finding(
                "mermaid/aspect-ratio-tall",
                path,
                block.start_line,
                f"Mermaid SVG 高宽比为 {tall_ratio:.2f}，超过阈值 {MAX_MERMAID_TALL_RATIO:.2f}。",
                "优先改为 flowchart LR，或拆成多张阶段图。",
            )
        )
    if wide_ratio > MAX_MERMAID_WIDE_RATIO:
        findings.append(
            Finding(
                "mermaid/aspect-ratio-wide",
                path,
                block.start_line,
                f"Mermaid SVG 宽高比为 {wide_ratio:.2f}，超过阈值 {MAX_MERMAID_WIDE_RATIO:.2f}。",
                "减少横向并列节点，或拆成多张图。",
            )
        )
    return findings


def lint_mermaid(path: Path, blocks: list[CodeBlock], text: str) -> list[Finding]:
    findings: list[Finding] = []
    lines = text.splitlines()
    for block in blocks:
        if block.language.lower() != "mermaid":
            continue
        body = block.body.strip()
        if not body:
            findings.append(Finding("mermaid/codeblock-empty", path, block.start_line, "Mermaid 代码块为空。", "删除空代码块或补充图表内容。"))
            continue
        edge_count = len(re.findall(r"-->|---|-.->|==>", body))
        node_count = mermaid_node_count(body)
        subgraph_count = len(re.findall(r"^\s*subgraph\b", body, flags=re.MULTILINE))
        first_line = next((line.strip() for line in body.splitlines() if line.strip()), "")
        is_vertical_flow = bool(re.match(r"^(flowchart|graph)\s+(TD|TB)\b", first_line))
        longest_chain_nodes = mermaid_longest_chain_nodes(body) if is_vertical_flow else 0

        if is_vertical_flow and longest_chain_nodes >= MAX_VERTICAL_MERMAID_CHAIN_NODES:
            findings.append(
                Finding(
                    "mermaid/vertical-flow-long",
                    path,
                    block.start_line,
                    f"纵向 Mermaid 流程最长链路约为 {longest_chain_nodes} 个节点，容易形成跨屏长图。",
                    "优先改为 flowchart LR，或拆成多张小图。",
                )
            )
            before = "\n".join(lines[max(0, block.start_line - 8) : block.start_line - 1])
            after = "\n".join(lines[block.end_line : min(len(lines), block.end_line + 8)])
            if "<details" not in before or "</details>" not in after:
                findings.append(
                    Finding(
                        "mermaid/details-wrapper",
                        path,
                        block.start_line,
                        "超阈值 Mermaid 图没有放在 details 折叠块中。",
                        "如果暂时不能拆图，可用 details 折叠兜底。",
                    )
                )
        if node_count > MAX_MERMAID_NODES:
            findings.append(Finding("mermaid/node-count-high", path, block.start_line, f"Mermaid 节点数约为 {node_count}。", "拆分图表，或只保留主干流程。"))
        if edge_count > MAX_MERMAID_EDGES:
            findings.append(Finding("mermaid/edge-count-high", path, block.start_line, f"Mermaid 连线数为 {edge_count}。", "减少交叉关系，或拆成阶段图。"))
        if subgraph_count > MAX_MERMAID_SUBGRAPHS:
            findings.append(Finding("mermaid/subgraph-count-high", path, block.start_line, f"Mermaid subgraph 数为 {subgraph_count}。", "拆成多张图，减少单图分组数量。"))

        depth = 0
        for offset, line in enumerate(body.splitlines(), start=block.start_line + 1):
            if re.match(r"^\s*subgraph\b", line):
                depth += 1
                if depth > 1:
                    findings.append(Finding("mermaid/subgraph-nested", path, offset, "Mermaid 出现嵌套 subgraph。", "避免嵌套 subgraph，改成多图或平级分组。"))
            elif re.match(r"^\s*end\s*$", line):
                depth = max(0, depth - 1)

        for label_match in re.finditer(r"[\[{(]([^\]})]+)[\]})]", body):
            label = label_match.group(1).strip()
            if len(label) > MAX_MERMAID_LABEL_CHARS:
                line_no = block.start_line + body.count("\n", 0, label_match.start()) + 1
                findings.append(
                    Finding(
                        "mermaid/node-label-too-long",
                        path,
                        line_no,
                        f"Mermaid 节点标签过长：{len(label)} 个字符。",
                        "缩短节点文案，把解释移到正文。",
                    )
                )

        render_ok, render_message, svg_text = render_mermaid_svg(body)
        if not render_ok:
            findings.append(
                Finding(
                    "mermaid/compile-failed",
                    path,
                    block.start_line,
                    f"Mermaid 无法被 mmdc 编译：{render_message}",
                    "修正 Mermaid 语法，或本地先用 mmdc 复现。",
                )
            )
        else:
            findings.extend(lint_mermaid_svg(path, block, svg_text, render_message))
    return findings


def lint_basic_format(path: Path, text: str, blocks: list[CodeBlock]) -> list[Finding]:
    findings: list[Finding] = []
    blocked = fenced_line_numbers(text)
    if not text.strip():
        findings.append(Finding("structure/empty-markdown-file", path, 1, "Markdown 文件为空。", "删除空文件，或补充正文内容。"))
    if text and not text.endswith("\n"):
        findings.append(Finding("markdown/no-final-newline", path, len(text.splitlines()), "文件末尾没有换行。", "在文件末尾补一个换行。"))
    for line_no, line in enumerate(text.splitlines(), start=1):
        if line_no not in blocked and line.rstrip(" \t") != line and not has_allowed_hard_break(line):
            findings.append(Finding("markdown/trailing-whitespace", path, line_no, "行尾存在多余空白。", "删除行尾空格；确需 Markdown 强制换行时保留两个空格。"))
        leading = re.match(r"^[\t ]+", line)
        if line_no not in blocked and leading and "\t" in leading.group(0):
            findings.append(Finding("markdown/tabs-indent", path, line_no, "缩进中出现 tab。", "改为空格缩进。"))
        if (
            line_no not in blocked
            and len(line) > MAX_LINE_CHARS
            and not line_length_exempt(line)
        ):
            findings.append(
                Finding(
                    "format/line-too-long",
                    path,
                    line_no,
                    f"单行长度为 {len(line)}，超过阈值 {MAX_LINE_CHARS}。",
                    "拆行；中文正文行可按规则配置跳过。",
                )
            )

    for block in blocks:
        if not block.language:
            findings.append(Finding("markdown/fenced-code-missing-language", path, block.start_line, "围栏代码块没有声明语言。", "在开头写明语言，例如 ```bash、```python 或 ```text。"))

    table_rows: list[tuple[int, int]] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        if "|" in line and not line.lstrip().startswith("<!--"):
            columns = [cell for cell in line.strip().strip("|").split("|")]
            table_rows.append((line_no, len(columns)))
        else:
            if len(table_rows) >= 3:
                findings.extend(table_mismatch_findings(path, table_rows))
            table_rows = []
    if len(table_rows) >= 3:
        findings.extend(table_mismatch_findings(path, table_rows))
    findings.extend(lint_list_indents(path, text, blocked))
    findings.extend(lint_html_tags(path, text, blocked))
    return findings


def table_mismatch_findings(path: Path, rows: list[tuple[int, int]]) -> list[Finding]:
    lines = path.read_text(encoding="utf-8").splitlines()
    has_separator = any(TABLE_SEPARATOR_RE.match(lines[line_no - 1]) for line_no, _count in rows)
    if not has_separator:
        return []
    expected = rows[0][1]
    findings: list[Finding] = []
    for line_no, count in rows[1:]:
        if count != expected:
            findings.append(
                Finding(
                    "format/table-column-mismatch",
                    path,
                    line_no,
                    f"Markdown 表格列数为 {count}，与表头 {expected} 不一致。",
                    "补齐或删除多余单元格。",
                )
            )
    return findings


def lint_list_indents(path: Path, text: str, blocked: set[int]) -> list[Finding]:
    findings: list[Finding] = []
    current: list[tuple[int, int]] = []
    list_re = re.compile(r"^( *)(?:[-*+]|\d+[.)])\s+")

    def flush() -> None:
        if len(current) < 2:
            return
        indents = sorted({indent for _line_no, indent in current})
        if len(indents) < 3:
            return
        deltas = [right - left for left, right in zip(indents, indents[1:]) if right > left]
        if not deltas:
            return
        expected = deltas[0]
        if all(delta == expected for delta in deltas):
            return
        bad_indent = indents[1 + next(index for index, delta in enumerate(deltas) if delta != expected)]
        bad_line = next(line_no for line_no, indent in current if indent == bad_indent)
        findings.append(
            Finding(
                "format/list-indent-inconsistent",
                path,
                bad_line,
                "同一列表块的缩进宽度不一致。",
                "统一使用 2 或 4 个空格作为同一列表块的缩进步长。",
            )
        )

    for line_no, line in enumerate(text.splitlines(), start=1):
        if line_no in blocked:
            continue
        match = list_re.match(line)
        if match:
            current.append((line_no, len(match.group(1))))
        elif not line.strip():
            flush()
            current = []
        elif current and not line.startswith(" "):
            flush()
            current = []
    flush()
    return findings


def lint_html_tags(path: Path, text: str, blocked: set[int]) -> list[Finding]:
    findings: list[Finding] = []
    stack: list[tuple[str, int]] = []

    for line_no, line in enumerate(text.splitlines(), start=1):
        if line_no in blocked:
            continue
        for match in HTML_TAG_RE.finditer(line):
            raw = match.group(0)
            if raw.startswith(("<!--", "<!", "<?")):
                continue
            closing = bool(match.group(1))
            tag = match.group(2).lower()
            trailing = match.group(4)
            if tag in VOID_HTML_TAGS or tag not in CHECKED_HTML_TAGS:
                continue
            if closing:
                for index in range(len(stack) - 1, -1, -1):
                    if stack[index][0] == tag:
                        del stack[index:]
                        break
                else:
                    findings.append(
                        Finding(
                            "format/html-tag-unclosed",
                            path,
                            line_no,
                            f"HTML 关闭标签没有匹配的开始标签：</{tag}>。",
                            "补齐开始标签，或删除多余关闭标签。",
                        )
                    )
            elif trailing != "/" and not raw.endswith("/>"):
                stack.append((tag, line_no))

    for tag, line_no in stack:
        findings.append(
            Finding(
                "format/html-tag-unclosed",
                path,
                line_no,
                f"HTML 标签没有闭合：<{tag}>。",
                f"补充 </{tag}>，或改用 Markdown 原生语法。",
            )
        )
    return findings


def parse_disables(path: Path, text: str, rules: set[str]) -> DisableState:
    state = DisableState(file_rules={}, next_line_rules={}, findings=[])
    for match in DISABLE_RE.finditer(text):
        line_no = line_for_offset(text, match.start())
        kind = match.group(1)
        rule_names = match.group(2).split()
        reason = (match.group(3) or "").strip()
        for rule in rule_names:
            if rule not in rules:
                state.findings.append(
                    Finding("lint/unknown-disable-rule", path, line_no, f"跳过注释引用了未知规则：{rule}。", "检查规则名是否写错，或先在 DESIGN.md 中登记。")
                )
                continue
            if not reason:
                state.findings.append(
                    Finding("lint/disable-missing-reason", path, line_no, f"跳过 {rule} 时没有填写原因。", "在冒号后写明跳过理由。")
                )
            if kind.endswith("next-line"):
                state.next_line_rules.setdefault(line_no + 1, {})[rule] = (line_no, False)
            else:
                state.file_rules[rule] = (line_no, False)
    return state


def apply_disables(path: Path, findings: list[Finding], state: DisableState) -> list[Finding]:
    filtered: list[Finding] = []
    for finding in findings:
        if finding.rule.startswith("lint/"):
            filtered.append(finding)
            continue
        suppressed = False
        if finding.rule in state.file_rules:
            line_no, _used = state.file_rules[finding.rule]
            state.file_rules[finding.rule] = (line_no, True)
            suppressed = True
        line_rules = state.next_line_rules.get(finding.line, {})
        if finding.rule in line_rules:
            line_no, _used = line_rules[finding.rule]
            line_rules[finding.rule] = (line_no, True)
            suppressed = True
        if not suppressed:
            filtered.append(finding)

    for rule, (line_no, used) in state.file_rules.items():
        if not used:
            filtered.append(Finding("lint/unused-disable", path, line_no, f"跳过注释没有实际跳过任何 {rule} 警告。", "删除无效跳过注释，或修正规则名/位置。"))
    for line_rules in state.next_line_rules.values():
        for rule, (line_no, used) in line_rules.items():
            if not used:
                filtered.append(Finding("lint/unused-disable", path, line_no, f"跳过注释没有实际跳过任何 {rule} 警告。", "删除无效跳过注释，或修正规则名/位置。"))
    return filtered


def lint_file(path: Path, allowed: set[str], rules: set[str]) -> list[Finding]:
    text = path.read_text(encoding="utf-8")
    blocks = code_blocks(text)
    disables = parse_disables(path, text, rules)
    findings: list[Finding] = []
    findings.extend(parse_frontmatter(path, text, allowed))
    findings.extend(lint_basic_format(path, text, blocks))
    findings.extend(lint_headings(path, text))
    findings.extend(lint_links(path, text))
    findings.extend(lint_images(path, text))
    findings.extend(lint_mermaid(path, blocks, text))
    findings.extend(disables.findings)
    return apply_disables(path, findings, disables)


def lint_structure(
    config: dict[str, object],
    files: list[Path] | None,
    include_nav_global: bool,
) -> list[Finding]:
    findings: list[Finding] = []
    nav = nav_paths(config)
    docs_paths = {path.relative_to(DOCS) for path in markdown_files()}
    seen: dict[Path, int] = {}

    if files is None:
        scoped_docs = docs_paths
        include_nav_global = True
    else:
        scoped_docs = {path.relative_to(DOCS) for path in files if path.is_relative_to(DOCS)}

    if include_nav_global:
        for nav_path in nav:
            seen[nav_path] = seen.get(nav_path, 0) + 1
            resolved_nav = (DOCS / nav_path).resolve(strict=False)
            if not is_relative_to(resolved_nav, DOCS):
                findings.append(
                    Finding(
                        "structure/docs-outside-nav-root",
                        ROOT / "mkdocs.yml",
                        1,
                        f"nav 指向 docs/ 目录外的 Markdown：{nav_path.as_posix()}。",
                        "正式正文页面应放在 docs/ 目录内，并使用相对 docs/ 的 nav 路径。",
                    )
                )
                continue
            if nav_path not in docs_paths:
                findings.append(
                    Finding(
                        "structure/nav-missing-file",
                        ROOT / "mkdocs.yml",
                        1,
                        f"nav 引用了不存在的文件：{nav_path.as_posix()}。",
                        "修正 mkdocs.yml 的 nav 路径，或补充目标页面。",
                    )
                )
        for nav_path, count in seen.items():
            if count > 1:
                findings.append(
                    Finding(
                        "structure/nav-duplicate-file",
                        ROOT / "mkdocs.yml",
                        1,
                        f"nav 中重复出现文件：{nav_path.as_posix()}。",
                        "只保留一个导航入口，或确认是否需要拆成不同页面。",
                    )
                )

    for doc_path in sorted(scoped_docs - set(nav)):
        findings.append(
            Finding(
                "structure/nav-orphan-file",
                DOCS / doc_path,
                1,
                "页面没有出现在 mkdocs.yml 的 nav 中。",
                "把页面加入 nav，或确认它不应作为正式正文页面。",
            )
        )
    return findings


def sort_findings(findings: list[Finding]) -> list[Finding]:
    return sorted(findings, key=lambda item: (rel(item.path), item.line, item.rule, item.message))


def compact_findings(findings: list[Finding]) -> list[Finding]:
    grouped: dict[tuple[Path, int], list[Finding]] = {}
    passthrough: list[Finding] = []
    primary_mermaid_rules = {
        "mermaid/render-too-wide",
        "mermaid/vertical-flow-long",
        "mermaid/node-count-high",
        "mermaid/edge-count-high",
        "mermaid/subgraph-count-high",
    }

    for finding in findings:
        if finding.rule in MERMAID_COMPACT_RULES:
            grouped.setdefault((finding.path, finding.line), []).append(finding)
        else:
            passthrough.append(finding)

    compacted: list[Finding] = passthrough[:]
    for (path, line), group in grouped.items():
        if not any(finding.rule in primary_mermaid_rules for finding in group):
            continue
        if len(group) == 1:
            compacted.extend(group)
            continue

        rules = ", ".join(finding.rule for finding in group)
        messages = "；".join(finding.message.rstrip("。") for finding in group)
        suggestions = []
        for finding in group:
            suggestion = finding.suggestion.rstrip("。")
            if suggestion not in suggestions:
                suggestions.append(suggestion)

        compacted.append(
            Finding(
                rules,
                path,
                line,
                f"Mermaid 图同时命中 {len(group)} 条布局/复杂度规则：{messages}。",
                "；".join(suggestions) + "。",
            )
        )

    return sort_findings(compacted)


def annotation_escape(value: str) -> str:
    return value.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def markdown_escape(value: str) -> str:
    return value.replace("|", "\\|").replace("<", "&lt;").replace(">", "&gt;").replace("\n", " ")


def rule_hit_count(findings: list[Finding]) -> int:
    return sum(len(finding.rule.split(", ")) for finding in findings)


def write_report(path: Path, findings: list[Finding]) -> None:
    status = "pass" if not findings else "warnings-found"
    lines = [
        "# Hello-AI Docs Lint Report",
        "",
        "CI-only warning report generated by `scripts/docs_lint_report.py`.",
        "",
        f"Status: {status}",
        f"Warning groups: {len(findings)}",
        f"Rule hits: {rule_hit_count(findings)}",
        "",
    ]
    if findings:
        lines.extend(["| Path | Line | Rule(s) | Warning | Suggestion |", "| --- | ---: | --- | --- | --- |"])
        for finding in findings:
            lines.append(
                f"| `{rel(finding.path)}` | {finding.line} | `{finding.rule}` | {markdown_escape(finding.message)} | {markdown_escape(finding.suggestion)} |"
            )
    else:
        lines.append("No warnings.")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a warning-only lint report for Hello-AI docs.")
    parser.add_argument("--github-annotations", action="store_true", help="emit GitHub Actions warning annotations")
    parser.add_argument("--output", type=Path, default=ROOT / "docs-lint-report.md", help="markdown report path")
    parser.add_argument(
        "--paths-from",
        type=Path,
        help="file containing changed paths; only existing docs/**/*.md files are linted, with mkdocs.yml enabling nav-wide checks",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="apply safe Markdown fixes before reporting: trailing whitespace, final newline, non-fenced leading tabs, and missing fence languages",
    )
    args = parser.parse_args()

    config = load_config()
    rules = known_rules()
    tags = allowed_tags(config)
    files, include_nav_global = scoped_paths(args.paths_from) if args.paths_from else (None, True)
    target_files = files if files is not None else markdown_files()
    if args.fix:
        fixed = [path for path in target_files if apply_safe_fixes(path)]
        print(f"Applied safe fixes to {len(fixed)} file(s).")
        for path in fixed:
            print(f"- {rel(path)}")

    findings: list[Finding] = []
    findings.extend(lint_structure(config, files, include_nav_global))
    for path in target_files:
        findings.extend(lint_file(path, tags, rules))
    findings = compact_findings(sort_findings(findings))

    for finding in findings:
        message = f"{finding.message} 建议：{finding.suggestion}"
        print(f"{rel(finding.path)}:{finding.line}: warning {finding.rule}: {message}")
        if args.github_annotations:
            print(
                "::warning "
                f"file={annotation_escape(rel(finding.path))},"
                f"line={finding.line},"
                f"title={annotation_escape(finding.rule)}::"
                f"{annotation_escape(message)}"
            )
    if not findings:
        print("Docs lint report: no warnings.")
    else:
        print(f"Docs lint report: {len(findings)} warning group(s), {rule_hit_count(findings)} rule hit(s).")

    output = args.output if args.output.is_absolute() else ROOT / args.output
    write_report(output, findings)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
