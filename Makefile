PYTHON ?= python3

.PHONY: install data offline check

install:
	$(PYTHON) -m pip install -r requirements.txt

data:
	$(PYTHON) scripts/run_pipeline.py

offline:
	$(PYTHON) scripts/run_pipeline.py --offline

check:
	$(PYTHON) scripts/check_outputs.py
