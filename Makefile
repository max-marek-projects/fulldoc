WORKDIR = .

style:
	isort $(WORKDIR)
	black $(WORKDIR)
	flake8 $(WORKDIR)
	mypy $(WORKDIR)

readme:
	pip install . -U
	fulldoc
