WORKDIR = .
LIBRARY_FOLDER = $(WORKDIR)/docsrtings_parser

style:
	isort $(WORKDIR)
	black $(WORKDIR)
	flake8 $(WORKDIR)
	mypy $(WORKDIR)

readme:
	pip install .
	generate-readme --folder $(LIBRARY_FOLDER)
