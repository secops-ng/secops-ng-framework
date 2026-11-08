"""Feed capture for the threat_intel_ingest playbook.

Backs the ``pull upstream feed`` step. The adapter polls the operator's TAXII
2.1 collection and hands over every response envelope of one scheduled poll;
this step checks the capture is whole and records its provenance. One
scheduled poll of one feed is one batch, keyed by ``batch_id`` =
SHA-256(feed_id | scheduled_for).

* **HTTPS, no inline credentials.** TAXII 2.1 section 1.6.6 makes HTTPS the
  transport for all communications, and the playbook injects credentials at
  runtime, never in the URL. A plain-HTTP URL or one carrying userinfo is
  refused.
* **The capture reaches the last page.** TAXII 2.1 section 3.7: an envelope
  sets ``more`` to true while more content is available, and an absent
  ``more`` means false. Every envelope but the last must say more; the last
  must not. A capture that stops early is refused, so a truncated poll never
  passes as a complete batch.
* **Every object is a STIX object.** Each carries a ``type`` and an ``id`` of
  the form ``<type>--<UUID>``. What the objects mean is the normalise step's
  concern; this step only refuses a response that is not STIX content.
* **The bundle digest ignores page order.** It is SHA-256 over the objects'
  canonical JSON, sorted, so the same content paged differently digests the
  same.

Every captured batch is a data point for the feed-coverage KPI, which counts
scheduled polls against those ingested.
"""

from __future__ import annotations

from urllib.parse import urlsplit

from ._common import STIX_ID, canonical, digest, items, pointer, zulu

__all__ = ["InvalidFeedCaptureError", "capture_feed_batch"]

_COVERAGE = "kpi.coverage_threat_intel_feed@v1"


class InvalidFeedCaptureError(ValueError):
    """The feed reference or the capture is malformed, or the capture is incomplete."""


def capture_feed_batch(feed_id: str, feed_url: str, scheduled_for: str, pages: list, pulled_at: str) -> dict:
    """Check one scheduled poll's capture is whole and record its provenance.

    Parameters
    ----------
    feed_id
        Stable identifier of the upstream feed.
    feed_url
        The TAXII collection (or STIX 2.1 endpoint) polled: an ``https`` URL
        without credentials.
    scheduled_for
        Zulu instant of the scheduled poll this capture answers.
    pages
        Every TAXII 2.1 envelope of the poll, in order: objects with keys from
        ``more``, ``next`` and ``objects``. A plain STIX 2.1 endpoint's
        bundle is passed as one envelope holding its objects.
    pulled_at
        Zulu instant the last page was received.
    """
    err = InvalidFeedCaptureError
    feed = pointer(feed_id, "feed_id", err)
    url = urlsplit(feed_url) if isinstance(feed_url, str) else None
    if url is None or url.scheme != "https" or not url.hostname:
        raise err(f"feed_url must be an https URL, got {feed_url!r}")
    if url.username is not None or url.password is not None:
        raise err("feed_url carries credentials; they are injected at runtime, never in the URL")
    scheduled = zulu(scheduled_for, "scheduled_for", err)
    if zulu(pulled_at, "pulled_at", err) < scheduled:
        raise err("pulled_at is before the scheduled poll")

    envelopes = items(pages, "pages", err)
    if not envelopes:
        raise err("pages must hold at least one envelope")
    objects = []
    for i, page in enumerate(envelopes):
        if not isinstance(page, dict) or not set(page) <= {"more", "next", "objects"}:
            raise err(f"pages[{i}] must be a TAXII envelope with keys from ['more', 'next', 'objects']")
        more = page.get("more", False)
        if not isinstance(more, bool):
            raise err(f"pages[{i}].more must be a boolean, got {more!r}")
        last = i == len(envelopes) - 1
        if last and more:
            raise err("the last envelope says more content is available: the capture stops before the last page")
        if not last and not more:
            raise err(f"pages[{i}] says no more content is available, yet further envelopes follow")
        for j, obj in enumerate(items(page.get("objects", []), f"pages[{i}].objects", err)):
            m = STIX_ID.match(obj.get("id", "")) if isinstance(obj, dict) and isinstance(obj.get("id"), str) else None
            if m is None or obj.get("type") != m.group(1):
                raise err(f"pages[{i}].objects[{j}] is not a STIX object with a type and a matching <type>--<UUID> id")
            objects.append(obj)

    return {
        "batch_id": digest(feed, scheduled_for),
        "feed_id": feed,
        "feed_url": feed_url,
        "scheduled_for": scheduled_for,
        "pulled_at": pulled_at,
        "page_count": len(envelopes),
        "object_count": len(objects),
        "bundle_digest": digest(*sorted(canonical(o) for o in objects)),
        "objects": objects,
        "metric_stamps": [_COVERAGE],
    }
