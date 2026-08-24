PYTHON_VERSIONS ?= 3.10 3.11 3.12 3.13 3.14

.PHONY: clean build lint format test test-all lock upgrade docs docs-publish test-release release

clean:
	rm -rf *.egg-info dist build .venvs coverage.xml .coverage
	find . -name '__pycache__' -prune -exec rm -rf {} +

build: clean
	uv build

lint:
	uv run --only-group dev ruff check .
	uv run --only-group dev ruff format --check .

format:
	uv run --only-group dev ruff check --fix .
	uv run --only-group dev ruff format .

# Tests on the current interpreter
test:
	uv run --group dev pytest --cov --cov-report=term-missing

# Tests on every supported interpreter, each in its own environment
test-all:
	@for v in $(PYTHON_VERSIONS); do \
		echo "===== Python $$v ====="; \
		UV_PROJECT_ENVIRONMENT=.venvs/$$v uv run --locked --python $$v --group dev pytest -q || exit 1; \
	done

lock:
	uv lock

upgrade:
	uv lock --upgrade

docs:
	uv run --only-group docs mkdocs serve

docs-publish:
	uv run --only-group docs mkdocs gh-deploy

test-release: build
	uv publish --publish-url https://test.pypi.org/legacy/

release: build
	uv publish
