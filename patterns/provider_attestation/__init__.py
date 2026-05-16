"""Periodic provider-attestation pattern.

Periodically re-verifies that a declared sovereign provider still meets the
criteria recorded against it, persists one attestation record per cycle, and
emits a structured regression event when a criterion that previously passed
starts failing.
"""
