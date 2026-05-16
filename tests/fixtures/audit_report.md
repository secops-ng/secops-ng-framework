# Sovereign Posture Audit

## Summary

- Workloads evaluated: 3
- Sovereign: 1
- Partial: 1
- Non-sovereign: 1

## Verdicts

### workload-a

- Kind: service
- Declared provider: nebul
- Region: eu-nl-1
- Data classification: restricted
- Verdict: Sovereign
- Reason: eu-hosted-eu-owned

### workload-b

- Kind: object_store
- Declared provider: ovh
- Region: eu-fr-gra
- Data classification: internal
- Verdict: Partial
- Reason: eu-hosted-non-eu-control-plane

### workload-c

- Kind: database
- Declared provider: aws
- Region: us-east-1
- Data classification: confidential
- Verdict: Non-sovereign
- Reason: non-eu-jurisdiction
