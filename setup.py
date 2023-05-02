#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import find_packages, setup

with open("README.md", "r") as fh:
    long_description = fh.read()

install_requires = []
with open("requirements.txt", "r", encoding="utf-8") as f:
    install_requires = list(i.rstrip() for i in f.readlines())

tests_require = []
with open("requirements.dev.txt", "r", encoding="utf-8") as f:
    tests_require = list(i.rstrip() for i in f.readlines())

version = {}
with open("scalr/version.py") as fp:
    exec(fp.read(), version)

setup(
    name="scalr-ngine",
    version=version["__version__"],
    author="René Moser",
    author_email="mail@renemoser.net",
    license="MIT",
    description="Autoscaling for Clouds.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ngine-io/scalr",
    packages=find_packages(exclude=["test.*", "tests"]),
    classifiers=[
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Environment :: Web Environment",
    ],
    install_requires=install_requires,
    tests_require=tests_require,
    python_requires=">=3.10",
    entry_points={
        "console_scripts": [
            "scalr-ngine = scalr.app:main",
        ],
    },
)
