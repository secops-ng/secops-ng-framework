# tools/hygiene_linter/

Forward-public hygiene linter. Implementation landed via PR #31.
If this directory is empty after merge, the linter PR needs rebasing onto
this restructure.

## Vendored third-party text

Files under `schemas/vendor/` are third-party specification text kept verbatim
(for example the OASIS CACAO JSON schemas). The voice rules (`commercial.*`)
are not applied there, because the words are not ours to change; the
credential rules always are. The list of such paths lives in
`cli.py` (`_VOICE_EXEMPT_PATHS`).
