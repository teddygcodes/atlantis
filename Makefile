.PHONY: dev setup run run-10 build clean test

# One-command bootstrap
setup:
	pip install -r requirements.txt --break-system-packages
	npm install

# Run dev server
dev:
	npm run dev

# Run engine (10-domain demo)
run-10:
	python3 __main__.py --demo-10-domains --force-clean

# Run engine (mock)
run-mock:
	python3 __main__.py --mock --force-clean

# Generate site data from latest engine run
site-data:
	python3 generate_site_data.py

# Full pipeline: run engine → generate site data → build
ship: run-10 site-data build

# Build frontend
build:
	npm run build

# Clean all output
clean:
	rm -rf output/ runs/ __pycache__/ .next/ .pytest_cache/
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# Run tests
test:
	python3 -m pytest tests/ -v
