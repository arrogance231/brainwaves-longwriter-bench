.PHONY: audit inspect test lint fixtures smoke benchmark plots

audit:
	./scripts/inspect_system.sh

inspect:
	python3 scripts/inspect_model.py --model-dir "$${MODEL_DIR:-/models/Qwen3.8-27B-Brainwaves}" --output reports/model.json

test:
	python3 -m unittest discover -s tests -v

lint:
	python3 -m py_compile benchmarks/**/*.py evaluation/*.py performance/*.py scripts/*.py
	bash -n scripts/*.sh serving/**/*.sh

fixtures:
	python3 benchmarks/arro_longwriter/generate_fixtures.py --validate

smoke:
	./scripts/smoke_test.sh

benchmark:
	./scripts/benchmark_all.sh

plots:
	python3 scripts/generate_plots.py
