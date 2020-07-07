clean:
	rm -rf .tox
	rm -rf .venv
	find -name '*.pyc' -delete

test:
	tox

install:
	test -d venv || python3 -m venv .venv
	(
		.venv/bin/activate
		pip3 install .
	)
