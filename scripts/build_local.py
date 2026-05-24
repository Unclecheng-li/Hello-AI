from __future__ import annotations

import subprocess
import sys


def main() -> int:
    command = [sys.executable, "-m", "mkdocs", "build", "--strict"]
    return subprocess.call(command)


if __name__ == "__main__":
    raise SystemExit(main())
