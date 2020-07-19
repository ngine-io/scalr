clean:
	rm -rf *.egg-info
	rm -rf *.dist-info
	rm -rf dist
	rm -rf build

build: clean
	python3 setup.py sdist bdist_wheel

test-release:
	twine upload --repository testpypi dist/*

release:
	twine upload dist/*

docs-publish:
	mkdocs gh-deploy

test:
	tox
