from __future__ import annotations

import argparse
import functools
import http.server
import json
import os
import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LAST_SERVER = ROOT / ".last_server.json"


class NoCacheHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        super().end_headers()

    def log_message(self, format: str, *args: object) -> None:
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {self.address_string()} {format % args}")


def port_available(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.25)
        return sock.connect_ex((host, port)) != 0


def choose_port(host: str, preferred: int) -> int:
    for port in range(preferred, preferred + 50):
        if port_available(host, port):
            return port
    raise RuntimeError(f"no free port found from {preferred} to {preferred + 49}")


def validate() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "validate_game.py")],
        cwd=str(ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    print(result.stdout.strip())
    if result.returncode != 0:
        raise RuntimeError("validation failed")


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve the Wanxiang Galgame locally.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    parser.add_argument("--open", action="store_true", help="open the browser after startup")
    parser.add_argument("--no-validate", action="store_true", help="skip preflight validation")
    args = parser.parse_args()

    if not args.no_validate:
        validate()

    port = choose_port(args.host, args.port)
    url = f"http://localhost:{port}/"
    LAST_SERVER.write_text(
        json.dumps(
            {
                "url": url,
                "host": args.host,
                "port": port,
                "pid": os.getpid(),
                "startedAt": time.strftime("%Y-%m-%dT%H:%M:%S"),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    handler = functools.partial(NoCacheHandler, directory=str(ROOT))
    server = http.server.ThreadingHTTPServer((args.host, port), handler)
    print(f"Serving Wanxiang Galgame at {url}")
    print(f"Project: {ROOT}")
    print("Press Ctrl+C to stop.")
    if args.open:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
