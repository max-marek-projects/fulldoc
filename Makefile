WORKDIR = .

lint:
	uv run ruff check $(WORKDIR)
	uv run mypy $(WORKDIR)
	uv run fulldoc

lint-fix:
	uv run ruff format $(WORKDIR)
	uv run ruff check --fix $(WORKDIR)
	uv run mypy $(WORKDIR)
	uv run fulldoc
