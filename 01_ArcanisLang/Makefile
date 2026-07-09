.PHONY: test run clean example repl install

test:
	python -m tests.run_tests

run:
	python -m src.cli $(file)

repl:
	python -m src.cli

example:
	python -m src.cli examples/$(example)

install:
	pip install -e .

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; \
	find . -type f -name '*.pyc' -delete

hello:
	python -m src.cli examples/hello_world.arc

fizzbuzz:
	python -m src.cli examples/fizzbuzz.arc
