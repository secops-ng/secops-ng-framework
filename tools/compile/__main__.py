"""Allow ``python -m tools.compile``."""

from __future__ import annotations

import sys

from tools.compile.cli import main

if __name__ == "__main__":
    sys.exit(main())
