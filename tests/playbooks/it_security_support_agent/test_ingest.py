"""Unit tests for the ingest-support-request primitive (F-WF-12 PRIM)."""

from __future__ import annotations

import pytest

from content.playbooks.it_security_support_agent.primitives import (
    InvalidSupportRequestError,
    ingest_support_request,
)


_GOOD_REQUEST = {
    "request_kind": "actionable",
    "requester_handle": "helpdesk-rota",
    "declared_symptom": "vpn connection drops every five minutes",
    "received_at": "2026-06-01T12:00:00Z",
}


class TestIngestSupportRequestHappyPath:
    def test_canonical_envelope_shape(self) -> None:
        out = ingest_support_request(_GOOD_REQUEST, "ticket/abc-1")
        assert out == {
            "request_kind": "actionable",
            "requester_handle": "helpdesk-rota",
            "declared_symptom": "vpn connection drops every five minutes",
            "received_at": "2026-06-01T12:00:00Z",
            "support_request_ref": "ticket/abc-1",
        }

    @pytest.mark.parametrize(
        "kind", ["informational", "actionable", "incident-shaped"]
    )
    def test_all_request_kinds_accepted(self, kind: str) -> None:
        out = ingest_support_request(
            {**_GOOD_REQUEST, "request_kind": kind}, "ticket/abc-2"
        )
        assert out["request_kind"] == kind

    def test_role_shaped_email_handle(self) -> None:
        out = ingest_support_request(
            {**_GOOD_REQUEST, "requester_handle": "soc-rota@example.eu"},
            "ticket/x.1",
        )
        assert out["requester_handle"] == "soc-rota@example.eu"

    def test_unicode_canonicalisation(self) -> None:
        # NFKC fold + strip
        out = ingest_support_request(
            {
                **_GOOD_REQUEST,
                "declared_symptom": "  ﬁle access denied  ",
            },
            "ticket/abc-3",
        )
        assert out["declared_symptom"] == "file access denied"

    def test_determinism_same_input_same_output(self) -> None:
        a = ingest_support_request(_GOOD_REQUEST, "ticket/abc-1")
        b = ingest_support_request(_GOOD_REQUEST, "ticket/abc-1")
        assert a == b


class TestIngestSupportRequestRejections:
    def test_non_dict_raw_request(self) -> None:
        with pytest.raises(InvalidSupportRequestError, match="object"):
            ingest_support_request("not-a-dict", "ticket/abc-1")  # type: ignore[arg-type]

    def test_unknown_request_kind(self) -> None:
        with pytest.raises(InvalidSupportRequestError, match="request_kind"):
            ingest_support_request(
                {**_GOOD_REQUEST, "request_kind": "emergency"},
                "ticket/abc-1",
            )

    def test_empty_request_kind(self) -> None:
        with pytest.raises(InvalidSupportRequestError):
            ingest_support_request(
                {**_GOOD_REQUEST, "request_kind": "  "},
                "ticket/abc-1",
            )

    @pytest.mark.parametrize(
        "bad_handle",
        [
            "First Last",  # personal name (space)
            "user@",  # malformed
            "-leading-dash",  # leading non-alpha
            "1leading-digit",
            "x" * 201,  # length cap
            "with spaces",
        ],
    )
    def test_rejects_non_role_shaped_handles(self, bad_handle: str) -> None:
        with pytest.raises(InvalidSupportRequestError):
            ingest_support_request(
                {**_GOOD_REQUEST, "requester_handle": bad_handle},
                "ticket/abc-1",
            )

    def test_rejects_control_chars_in_symptom(self) -> None:
        with pytest.raises(
            InvalidSupportRequestError, match="control characters"
        ):
            ingest_support_request(
                {
                    **_GOOD_REQUEST,
                    "declared_symptom": "line1\nline2",
                },
                "ticket/abc-1",
            )

    def test_rejects_symptom_over_400_chars(self) -> None:
        with pytest.raises(InvalidSupportRequestError, match="<= 400"):
            ingest_support_request(
                {**_GOOD_REQUEST, "declared_symptom": "x" * 401},
                "ticket/abc-1",
            )

    @pytest.mark.parametrize(
        "bad_iso",
        [
            "2026-06-01 12:00:00",  # missing T / Z
            "2026-06-01T12:00:00",  # missing Z
            "2026-06-01T12:00:00.123Z",  # subsecond
            "2026-06-01T12:00:00+00:00",  # offset form
            "not-a-date",
        ],
    )
    def test_rejects_non_iso_z_received_at(self, bad_iso: str) -> None:
        with pytest.raises(InvalidSupportRequestError, match="ISO-8601"):
            ingest_support_request(
                {**_GOOD_REQUEST, "received_at": bad_iso},
                "ticket/abc-1",
            )

    def test_rejects_empty_support_request_ref(self) -> None:
        with pytest.raises(InvalidSupportRequestError):
            ingest_support_request(_GOOD_REQUEST, "   ")

    def test_rejects_bad_shape_support_request_ref(self) -> None:
        with pytest.raises(
            InvalidSupportRequestError, match="opaque-pointer"
        ):
            ingest_support_request(_GOOD_REQUEST, "has spaces")

    def test_rejects_non_string_request_kind(self) -> None:
        with pytest.raises(InvalidSupportRequestError):
            ingest_support_request(
                {**_GOOD_REQUEST, "request_kind": 7},
                "ticket/abc-1",
            )
