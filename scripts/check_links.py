from __future__ import annotations

import posixpath
import re
from pathlib import Path
from urllib.parse import urljoin, urlsplit


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
BASICS = DOCS / "basics"
LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
HREF_RE = re.compile(r"href=[\"']([^\"']+)[\"']")
EXTERNAL_SCHEMES = {"http", "https", "mailto", "tel"}


def iter_markdown_files() -> list[Path]:
    return sorted(DOCS.rglob("*.md"))


def source_to_route(md: Path) -> str:
    rel = md.relative_to(DOCS).as_posix()
    if md.name == "index.md":
        parent = md.parent.relative_to(DOCS).as_posix()
        if parent == ".":
            return "/"
        return f"/{parent.strip('/')}/"
    return f"/{Path(rel).with_suffix('').as_posix().strip('/')}/"


def route_to_source(route: str) -> Path:
    clean = posixpath.normpath("/" + route.strip("/"))
    if clean == "/":
        return DOCS / "index.md"

    parts = clean.strip("/").split("/")
    directory_index = DOCS.joinpath(*parts, "index.md")
    if directory_index.exists():
        return directory_index

    return DOCS.joinpath(*parts).with_suffix(".md")


def resolve_local_target(md: Path, target: str) -> Path | None:
    parsed = urlsplit(target.strip())
    if parsed.scheme in EXTERNAL_SCHEMES or parsed.netloc:
        return None
    if not parsed.path or parsed.path.startswith("#"):
        return None

    path = parsed.path
    if path.endswith(".md"):
        if path.startswith("/"):
            return (DOCS / path.lstrip("/")).resolve()
        return (md.parent / path).resolve()

    if path.endswith("/") or path.startswith("/"):
        base_route = source_to_route(md)
        route = path if path.startswith("/") else urljoin(base_route, path)
        return route_to_source(route).resolve()

    return (md.parent / path).resolve()


def is_under(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def main() -> int:
    missing: list[str] = []
    markdown_page_links: list[str] = []

    for md in iter_markdown_files():
        text = md.read_text(encoding="utf-8")
        for target in LINK_RE.findall(text) + HREF_RE.findall(text):
            resolved = resolve_local_target(md, target)
            if resolved is None:
                continue
            clean_target = target.split("#", 1)[0].split("?", 1)[0]
            if is_under(md, BASICS) and clean_target.endswith(".md") and is_under(resolved, DOCS):
                markdown_page_links.append(f"{md.relative_to(ROOT)} -> {target}")
            if not resolved.exists():
                missing.append(f"{md.relative_to(ROOT)} -> {target}")

    if markdown_page_links:
        print("Markdown page links in docs/basics should use directory-style URLs:")
        for item in markdown_page_links:
            print(item)
        return 1

    if missing:
        for item in missing:
            print(item)
        return 1

    print("Link check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
