"""Playbooks namespace.

Portable CACAO playbooks live in hyphen-named directories on disk
(``content/playbooks/vuln_intake/``) so the on-disk layout matches the
project's contributor-facing naming conventions. Python cannot import
through hyphens, so we register an underscore-aliased package per
workflow whose ``__path__`` rewires to the hyphen directory. Per-target
CORE bodies then import via
``from content.playbooks.vuln_intake.primitives import ...`` and the
resolver lands in ``content/playbooks/vuln_intake/primitives/`` on disk.

This file deliberately does *not* enumerate the aliases — each workflow
ships its own ``vuln_intake/`` (or analogous) sibling package that owns
its own ``__path__`` rewrite. Adding workflows here would couple every
workflow's primitive landing PR through a single file and break the
``parallel-safe`` decomposition documented in the F-WF-01 gap inventory.
"""

from __future__ import annotations
