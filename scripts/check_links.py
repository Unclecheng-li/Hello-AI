from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def iter_markdown_files() -> list[Path]:
    return sorted(DOCS.rglob("*.md"))


def main() -> int:
    missing: list[str] = []

    for md in iter_markdown_files():
        text = md.read_text(encoding="utf-8")
        for target in LINK_RE.findall(text):
            target = target.split("#", 1)[0].split("?", 1)[0]
            if not target or target.startswith(("http://", "https://", "mailto:")):
                continue
            if target.startswith("/"):
                resolved = (DOCS / target.lstrip("/")).resolve()
            else:
                resolved = (md.parent / target).resolve()
            if not resolved.exists():
                missing.append(f"{md.relative_to(ROOT)} -> {target}")

    if missing:
        for item in missing:
            print(item)
        return 1

    print("Link check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
