from __future__ import annotations

import subprocess
import sys


CHECKS = [
    [sys.executable, "scripts/check_nav.py"],
    [sys.executable, "scripts/check_links.py"],
    [sys.executable, "scripts/validate_assets.py"],
]


def main() -> int:
    for command in CHECKS:
        subprocess.run(command, check=True)
    subprocess.run([sys.executable, "-m", "mkdocs", "build", "--strict"], check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
