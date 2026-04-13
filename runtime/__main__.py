"""CLI entry for local runtime diagnostics."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from .diagnostics import build_live_diagnostic, render_live_diagnostic
from .env_loader import load_dotenv


def main(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv[1:]
    repo_root = Path(argv[0]).expanduser() if argv else Path.cwd()
    load_dotenv(repo_root)
    report = build_live_diagnostic(repo_root)
    if "--json" in argv:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(render_live_diagnostic(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
