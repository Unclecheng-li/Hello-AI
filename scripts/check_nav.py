from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


class MkDocsLoader(yaml.SafeLoader):
    pass


def ignore_python_name(loader: MkDocsLoader, suffix: str, node: yaml.Node) -> str:
    return suffix


MkDocsLoader.add_multi_constructor(
    "tag:yaml.org,2002:python/name:",
    ignore_python_name,
)


def iter_nav_paths(items: list[object]) -> set[Path]:
    paths: set[Path] = set()
    for item in items:
        if isinstance(item, str):
            paths.add(Path(item))
        elif isinstance(item, dict):
            for value in item.values():
                if isinstance(value, str):
                    paths.add(Path(value))
                elif isinstance(value, list):
                    paths.update(iter_nav_paths(value))
    return paths


def main() -> int:
    config = yaml.load((ROOT / "mkdocs.yml").read_text(encoding="utf-8"), Loader=MkDocsLoader)
    nav_paths = iter_nav_paths(config.get("nav", []))
    docs_paths = {path.relative_to(DOCS) for path in DOCS.rglob("*.md")}

    missing_files = sorted(nav_paths - docs_paths)
    missing_nav = sorted(docs_paths - nav_paths)

    if missing_files:
        print("Navigation points to missing files:")
        for path in missing_files:
            print(f"- {path.as_posix()}")

    if missing_nav:
        print("Markdown files missing from navigation:")
        for path in missing_nav:
            print(f"- {path.as_posix()}")

    if missing_files or missing_nav:
        return 1

    print("Navigation check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
