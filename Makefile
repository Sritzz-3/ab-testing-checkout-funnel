.PHONY: setup run test verify all
setup:
	python -m pip install -r requirements.txt
run:
	python -m src.run_pipeline
test:
	python -m pytest -q
verify: test run
	python -c "from pathlib import Path; required=['README.md','outputs/results.json','outputs/tables/design.csv','outputs/tables/balance.csv','outputs/tables/segments.csv','outputs/figures/conversion.png','outputs/figures/funnel.png','outputs/figures/power.png']; assert all(Path(x).exists() for x in required)"
	! grep -E '\{\{|TODO|TBD|populated after' README.md
all: run
