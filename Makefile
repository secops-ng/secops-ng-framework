# SecOps-NG framework — make targets

.PHONY: roadmap-status test

roadmap-status:
	python scripts/render_roadmap.py

test:
	pytest -q
