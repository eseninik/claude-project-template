"""Report a concise snapshot of the Codex runtime environment."""

from __future__ import annotations

import logging
import os
from pathlib import Path
import shutil
import sys


logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


def main() -> int:
    logger.info("codex_env_check.main.entry", extra={"params": {}})
    path_entries = [entry for entry in os.environ.get("PATH", "").split(os.pathsep) if entry]
    facts = {
        "python_version": sys.version.split()[0],
        "cwd": str(Path.cwd().resolve()),
        "codex_on_path": str(shutil.which("codex") is not None).lower(),
        "path_entries": str(len(path_entries)),
    }
    sys.stdout.write("".join(f"{key}: {value}\n" for key, value in facts.items()))
    logger.info("codex_env_check.main.exit", extra={"result": facts})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
