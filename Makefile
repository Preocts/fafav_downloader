.PHONY: update-deps init update install clean clean-pyc clean-build clean-test tests

update-deps:
	pip-compile --upgrade --generate-hashes
	pip-compile --upgrade --generate-hashes --output-file dev-requirements.txt dev-requirements.in

install:
	pip install --upgrade pip setuptools wheel
	pip install --upgrade -r requirements.txt
	pip install --editable .

dev-install:
	pip install --upgrade -r dev-requirements.txt

init:
	pip install pip-tools
	rm -rf .tox

update: init update-deps install

# Run all cleaning steps
clean: clean-build clean-pyc clean-test

clean-pyc: ## Remove python artifacts.
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-build: ## Remove build artifacts.
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -fr {} +

clean-test: ## Remove test artifacts
	rm -fr .tox/
	rm -f .coverage
	rm -fr htmlcov/
	find . -name '.pytest_cache' -exec rm -fr {} +

blacken: ## Run Black against code
	black --line-length 79 ./src/fafavs
	black --line-length 79 ./tests

tests: ## Run all tests found in the /tests directory.
	coverage run -m pytest tests/
	coverage report --include "*/fafavs/*" --show-missing
