# Paved-road commands (kickoff prompt §A/§L, handbook ch12/ch21).
# Adapted to this repo's top-level package layout + local Docker demo.
.DEFAULT_GOAL := help
.PHONY: help bootstrap up down test test-cov lint fmt secretscan audit eval-smoke eval eval-full pdf

help: ## List targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	  awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-14s\033[0m %s\n",$$1,$$2}'

bootstrap: ## Install deps + pre-commit hooks
	pip install -r requirements.txt -r requirements-dev.txt
	pre-commit install

up: ## Local stack (Neo4j + mock + API) — the real runtime
	./run_enterprise_demo.sh

down: ## Stop local stack
	./restart-all.sh || true

test: ## Unit + contract tests
	pytest tests/ -q

test-cov: ## Tests with coverage (CI gate)
	pytest tests/ -q --cov=. --cov-report=term-missing --cov-report=xml

lint: ## Ruff lint
	ruff check .

fmt: ## Ruff format
	ruff format .

secretscan: ## Detect committed secrets (pre-commit hook set)
	pre-commit run --all-files detect-secrets || true

audit: ## Dependency vulnerability scan (supply chain, ch13)
	pip-audit -r requirements.txt || true

eval-smoke: ## Fast eval gate (safety always; golden if Neo4j up)
	python evals/run_eval.py --suite smoke

eval eval-full: ## Full eval + safety release gate (report to eval-report.json)
	python evals/run_eval.py --suite full --report eval-report.json

pdf: ## Rebuild the LLMOps handbook PDFs
	cd docs/llmops-handbook/.pdf-build && node render.mjs
