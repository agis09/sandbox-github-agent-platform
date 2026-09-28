"""Sample CLI application for the agent-platform sandbox fixture.

A deliberately small, self-contained tool used as target content for
plan / execute / publish flows: the agent plans a change, executes it,
and the resulting patch is published as a Draft PR against this repo.
"""

from __future__ import annotations

import argparse
import json
import sys

VERSION = "0.1.0"


def greet(name: str) -> str:
    return f"Hello, {name}!"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="sandbox-app", description=__doc__)
    parser.add_argument("--name", default="world", help="name to greet")
    parser.add_argument("--json", action="store_true", help="print output as JSON")
    args = parser.parse_args(argv)

    message = greet(args.name)
    if args.json:
        print(json.dumps({"app": "sandbox-app", "version": VERSION, "message": message}))
    else:
        print(message)
    return 0


if __name__ == "__main__":
    sys.exit(main())
