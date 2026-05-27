"""Allow ``python -m tools.hygiene_linter``."""

from __future__ import annotations

import sys

from tools.hygiene_linter.cli import main

if __name__ == "__main__":
    sys.exit(main())
