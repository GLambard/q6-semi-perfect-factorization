#!/usr/bin/env python3
"""Run a command unchanged while freezing its combined output and exit status."""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", required=True, type=Path)
    parser.add_argument("--status", required=True, type=Path)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if not args.command:
        parser.error("a command is required after the logging options")

    args.log.parent.mkdir(parents=True, exist_ok=True)
    started = datetime.now(timezone.utc)
    start_clock = time.perf_counter()
    header = {
        "event": "start",
        "utc": started.isoformat(),
        "command": args.command,
        "python": sys.version,
        "platform": platform.platform(),
    }

    with args.log.open("x", encoding="utf-8") as stream:
        first_line = json.dumps(header, sort_keys=True)
        print(first_line, flush=True)
        stream.write(first_line + "\n")
        stream.flush()

        process = subprocess.Popen(
            args.command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        assert process.stdout is not None
        for line in process.stdout:
            print(line, end="", flush=True)
            stream.write(line)
            stream.flush()
        return_code = process.wait()

        finished = datetime.now(timezone.utc)
        footer = {
            "event": "finish",
            "utc": finished.isoformat(),
            "elapsed_seconds": time.perf_counter() - start_clock,
            "exit_status": return_code,
        }
        last_line = json.dumps(footer, sort_keys=True)
        print(last_line, flush=True)
        stream.write(last_line + "\n")

    args.status.write_text(str(return_code) + "\n", encoding="utf-8")
    return return_code


if __name__ == "__main__":
    raise SystemExit(main())
