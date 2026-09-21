# Vendored: OASIS CACAO Security Playbooks v2.0 JSON schemas

Upstream: https://github.com/oasis-open/cacao-json-schemas (Apache-2.0, see
`LICENSE` alongside). Pinned at commit `72853294a18b7d42af84fe1cc410ac70b1366c3b`.

These are the official JSON Schema files published by the OASIS CACAO
Technical Committee's open repository. They are vendored unmodified so the
conformance gate (`python -m tools.cacao_conformance`) runs offline and
deterministically in CI, and so a schema change upstream is a reviewed diff
here rather than a silent CI flip.

The files declare JSON Schema Draft-07. Note that several of them use the
`unevaluatedProperties` keyword, which Draft-07 validators ignore; the
conformance tool validates under the declared dialect by default and can be
asked for the stricter 2020-12 reading with `--dialect 2020-12`.

## Refreshing

```bash
git clone --depth 1 https://github.com/oasis-open/cacao-json-schemas /tmp/cacao-json-schemas
rm -rf schemas/vendor/cacao-2.0/schemas
cp -R /tmp/cacao-json-schemas/schemas schemas/vendor/cacao-2.0/schemas
cp /tmp/cacao-json-schemas/LICENSE schemas/vendor/cacao-2.0/LICENSE
git -C /tmp/cacao-json-schemas rev-parse HEAD   # update the pin above
python -m tools.cacao_conformance                # re-baseline only if intended
```
