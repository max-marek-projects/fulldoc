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

req:
	uv sync

req-dev:
	uv sync --extra lint,doc

SPHINXBUILD   = sphinx-build
SOURCEDIR     = docs
BUILDDIR      = _build

html:
	uv run $(SPHINXBUILD) -b html $(SOURCEDIR) $(BUILDDIR)/html

clean:
	rm -rf $(BUILDDIR)
