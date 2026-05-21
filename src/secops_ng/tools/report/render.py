"""WeasyPrint-based PDF rendering for the SecOps-NG vulnscan report."""

from __future__ import annotations

import base64
import hashlib
import json
import os
from dataclasses import asdict
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

from secops_ng.tools.report.model import ReportContext

_PKG_DIR = Path(__file__).resolve().parent
_TEMPLATE_DIR = _PKG_DIR / "templates"
_ASSETS_DIR = _PKG_DIR / "assets"


def _severity_class(sev: str) -> str:
    return f"sev-{sev.lower()}"


def _build_env() -> Environment:
    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATE_DIR)),
        autoescape=select_autoescape(["html"]),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["sev_class"] = _severity_class
    return env


def render_html(ctx: ReportContext) -> str:
    """Render the report HTML for the given context.

    Splitting HTML and PDF helps tests run without the WeasyPrint native
    deps and lets a designer preview the report in a browser.
    """
    env = _build_env()
    template = env.get_template("report.html.j2")

    # Embed CSS + cover SVG so the output is a single self-contained HTML
    # file (and so WeasyPrint doesn't need a base_url at render time).
    css_text = (_ASSETS_DIR / "styles.css").read_text(encoding="utf-8")
    cover_svg = (_ASSETS_DIR / "cover.svg").read_text(encoding="utf-8")

    return template.render(
        ctx=ctx,
        css_text=css_text,
        cover_svg=cover_svg,
    )


def render_pdf(ctx: ReportContext, out_path: str | os.PathLike[str]) -> Path:
    """Render the report context to a PDF at ``out_path``.

    Imported lazily so the rest of the module is usable in environments
    without WeasyPrint's native deps installed (CI smoke tests).
    """
    from weasyprint import HTML  # noqa: PLC0415

    html = render_html(ctx)
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    HTML(string=html, base_url=str(_PKG_DIR)).write_pdf(out)
    return out


# ---------------------------------------------------------------------- #
# small helpers used by both renderer and CLI
# ---------------------------------------------------------------------- #
def context_to_json(ctx: ReportContext) -> str:
    """Serialise a context to JSON (round-trips via ``ReportContext.from_dict``)."""
    return json.dumps(_to_jsonable(ctx), indent=2, sort_keys=True)


def _to_jsonable(obj: Any) -> Any:
    if hasattr(obj, "__dataclass_fields__"):
        return {k: _to_jsonable(v) for k, v in asdict(obj).items()}
    if isinstance(obj, list):
        return [_to_jsonable(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _to_jsonable(v) for k, v in obj.items()}
    return obj


def hash_run(ctx: ReportContext) -> str:
    """Deterministic hash of the report inputs, recorded in the appendix."""
    blob = context_to_json(ctx).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def asset_data_uri(name: str) -> str:
    """Return a data: URI for an asset (used to keep templates portable)."""
    path = _ASSETS_DIR / name
    data = path.read_bytes()
    mime = "image/svg+xml" if name.endswith(".svg") else "application/octet-stream"
    b64 = base64.b64encode(data).decode("ascii")
    return f"data:{mime};base64,{b64}"
