from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MERMAID_CACHE_DIR = ROOT / "docs" / "assets" / "mermaid"
MERMAID_CACHE_MARKER = MERMAID_CACHE_DIR / ".cache-key"


def current_cache_key() -> str:
    digest = hashlib.sha256()
    for relative_path in ("mkdocs.yml", "requirements.txt"):
        path = ROOT / relative_path
        if path.exists():
            digest.update(path.read_bytes())

    try:
        result = subprocess.run(
            ["mmdc", "--version"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
        digest.update(result.stdout.encode("utf-8"))
        digest.update(result.stderr.encode("utf-8"))
    except Exception:
        digest.update(b"mmdc-version-unavailable")

    return digest.hexdigest()


def cache_is_valid(cache_key: str) -> bool:
    try:
        return MERMAID_CACHE_MARKER.read_text(encoding="utf-8").strip() == cache_key
    except FileNotFoundError:
        return False


def patch_mermaid_renderer(use_cache: bool) -> None:
    from mkdocs_mermaid_to_svg.mermaid_block import MermaidBlock

    original_generate_image = MermaidBlock.generate_image

    def generate_image_cached(
        self: MermaidBlock,
        output_path: str,
        image_generator: object,
        config: dict[str, object],
        page_file: str | None = None,
    ) -> bool:
        path = Path(output_path)
        if use_cache and path.exists() and path.stat().st_size > 0:
            print(f"INFO    -  Reusing cached Mermaid SVG: {path.name}")
            return True
        return bool(
            original_generate_image(self, output_path, image_generator, config, page_file)
        )

    MermaidBlock.generate_image = generate_image_cached


def run_mkdocs_build(verbose: bool) -> None:
    from mkdocs.__main__ import cli

    args = ["build", "--strict"]
    if verbose:
        args.append("--verbose")
    cli(args=args, prog_name="mkdocs", standalone_mode=False)


def write_cache_marker(cache_key: str) -> None:
    MERMAID_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    MERMAID_CACHE_MARKER.write_text(f"{cache_key}\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build MkDocs while reusing already-rendered Mermaid SVGs."
    )
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    cache_key = current_cache_key()
    patch_mermaid_renderer(use_cache=cache_is_valid(cache_key))
    run_mkdocs_build(verbose=args.verbose)
    write_cache_marker(cache_key)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
