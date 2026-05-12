# Security Policy

SecOps-NG is a security framework. Responsible disclosure is taken
seriously.

## Reporting a vulnerability

Please email **security@secops-ng.example** with:

- A description of the issue and its impact.
- Steps to reproduce, or a proof of concept.
- Affected versions / commits.
- Any suggested mitigations.

Do **not** open a public GitHub issue for security reports.

If you require encrypted communication, request a PGP key in your first
message and we will respond with one before you share details.

## Our commitments

- We will acknowledge receipt within **3 business days**.
- We aim to provide an initial assessment within **10 business days**.
- We follow a **90-day coordinated disclosure** window from acknowledgement
  to public disclosure. Extensions are possible by mutual agreement when a
  fix requires coordinated action across downstream operators.
- We will credit reporters in release notes unless anonymity is requested.

## Scope

In scope:

- The `secops_ng` Python package and its public APIs.
- The workflow templates under `workflows/`.
- Build and packaging configuration in this repository.

Out of scope:

- Third-party dependencies (please report to those projects directly; we
  are happy to help triage).
- Self-hosted deployments operated by third parties.
- Theoretical issues with no demonstrable impact.

## Alignment with NIS2

SecOps-NG is intended to be deployed by entities subject to the EU NIS2
Directive. Where a vulnerability is likely to affect such operators'
incident-reporting obligations, we will prioritise coordinated disclosure
and provide written guidance suitable for inclusion in an incident report
to the relevant competent authority or CSIRT.
