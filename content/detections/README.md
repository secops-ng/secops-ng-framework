# content/detections/

We *reference* Sigma rules. We do not maintain a detection-rule fork.

Each file here is a YAML pointer record:

```yaml
sigma_ref: SigmaHQ/rules:rules/windows/process_creation/proc_creation_win_susp_rundll32.yml
purpose: Surface suspicious rundll32 invocations during phishing triage.
used_by:
  - content/playbooks/phishing-triage/
notes: ...
```

Curation only — no rule logic lives in this tree.
