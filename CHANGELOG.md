# Changelog

All notable changes to the SecOps-NG framework are recorded here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and the project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- DORA component-definition: Art.5 governance + Art.6 ICT risk framework (SKELETON layer, 0.2.0-pre).
- DORA component-definition: Art.7 systems + Art.8 identification + Art.10 detection + Art.11 response/recovery (CORE layer, 0.2.0).
- DORA component-definition: Art.12 backup/restore + Art.13 post-incident learning + Art.14 crisis communication (EXTEND layer, 0.2.1); README lists full DORA article roster.
- CRA component-definition: Annex I §1 essential cybersecurity requirements (secure-by-default configuration, access control, confidentiality, integrity, availability, attack-surface limitation, logging and monitoring, and security-update capability) (CORE layer, 0.2.0); new source YAML `content/mappings/cra/annex-i-1-essential-cybersecurity.yaml` covers the secure-by-design and secure-by-default product properties.
- CRA component-definition: Article 13 manufacturer obligations (risk assessment (Art.13(2)–(3)), component due diligence (Art.13(4)), vulnerability-handling process (Art.13(6)), security-update dissemination (Art.13(8)), and single point of contact (Art.13(12))) (CORE layer, 0.2.1); new source YAML `content/mappings/cra/article-13.yaml` covers the manufacturer-side obligations that wrap the Annex I §1/§2 product properties.
