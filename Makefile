.PHONY: install
install:
	uv sync

.PHONY: clean
clean:
	rm -rf dist/
	find . -name '__pycache__' -exec rm -fr {} +

.PHONY: typecheck
typecheck:
	uv run pyright

.PHONY: lint
lint:
	-uv run ruff check --fix
	-uv run ruff format

.PHONY: test
test:
	uv run pytest
