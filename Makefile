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
