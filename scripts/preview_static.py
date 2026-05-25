from __future__ import annotations

import argparse
import http.server
import socketserver
import subprocess
import sys
from functools import partial
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SITE_DIR = ROOT / "site"


def build_site() -> None:
    subprocess.run(
        [sys.executable, "-m", "mkdocs", "build", "--strict"],
        cwd=ROOT,
        check=True,
    )


def serve_site(port: int) -> None:
    handler = partial(http.server.SimpleHTTPRequestHandler, directory=SITE_DIR)
    with socketserver.TCPServer(("127.0.0.1", port), handler) as httpd:
        print(f"Serving built site at http://127.0.0.1:{port}/")
        print("Press Ctrl+C to stop.")
        httpd.serve_forever()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build the MkDocs site first, then preview the generated static site."
    )
    parser.add_argument("--port", type=int, default=8001)
    args = parser.parse_args()

    build_site()
    serve_site(args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
