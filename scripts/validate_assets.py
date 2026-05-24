from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
IMAGE_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
HTML_SRC_RE = re.compile(r'src="([^"]+)"')


def main() -> int:
    missing: list[str] = []
    for path in DOCS.rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        refs = IMAGE_RE.findall(text) + HTML_SRC_RE.findall(text)
        for ref in refs:
            ref = ref.split("#", 1)[0].split("?", 1)[0]
            if not ref or ref.startswith(("http://", "https://", "data:")):
                continue
            if ref.startswith("/"):
                candidate = (DOCS / ref.lstrip("/")).resolve()
            else:
                candidate = (path.parent / ref).resolve()
            if not candidate.exists():
                missing.append(f"{path.relative_to(ROOT)} -> {ref}")
    if missing:
        for item in missing:
            print(item)
        return 1
    print("Asset reference scan completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
