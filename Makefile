.PHONY: format test

TESTED_FILES = go_fish.py


all: test

format:
	black *.py

test:
	pytest --doctest-modules \
	       --cov=. \
	       --cov-report term-missing \
	       --flake8 \
	       --pep8 \
	       $(TESTED_FILES)
