#!/bin/bash

# get version from pyproject.toml
version=$(grep "version" pyproject.toml | cut -d '"' -f 2)

# build package
rm -rf .venv/
rm -rf dist/
python -m build

# install package in virtual environment
python -m venv .venv
source .venv/bin/activate
python -m pip install dist/gitreporter-$version-py3-none-any.whl
