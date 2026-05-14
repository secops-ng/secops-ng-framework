# SecOps-NG framework — make targets

.PHONY: roadmap test

roadmap:
	python scripts/render_roadmap.py

test:
	pytest -q
