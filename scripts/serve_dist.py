from __future__ import annotations

import argparse
import http.server
import socketserver
from functools import partial
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description="Serve generated simulations over local HTTP.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    handler = partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT))
    with socketserver.TCPServer((args.host, args.port), handler) as server:
        print(f"http://{args.host}:{args.port}/dist/surface-revolution.html")
        server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
