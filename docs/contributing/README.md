# Contributing

Operational walkthroughs for common contribution shapes. Start at
`../../CONTRIBUTING.md` for repo-wide mechanics (DCO, review flow,
public-bar hygiene); the files here go one level deeper on specific
tasks.

- [`first-contribution.md`](first-contribution.md) — end-to-end walkthrough
  for a first-time contributor (fork, branch, tests, linter, PR).
- [`playbook-authoring.md`](playbook-authoring.md) — writing a new
  CACAO v2 playbook: directory scaffold, required fields, the
  `mappings.yaml` overlay, orphan-CI, and running the hygiene linter.
- [`compiler-walkthrough.md`](compiler-walkthrough.md) — adding a
  compiled example under `examples/{n8n,temporal,langgraph}/` for an
  existing playbook.
- [`hygiene-linter.md`](hygiene-linter.md) — the forward-public
  hygiene linter: what it checks and how to escalate a false-positive.
- [`byte-parity-testing.md`](byte-parity-testing.md) — the golden-file
  discipline that anchors every compiled example.

Community-driven compile targets live in
`../../compilers/community/` and each carry their own README.
