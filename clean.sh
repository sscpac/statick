#!/bin/bash

rm -rf build/ dist/ htmlcov/ output-py* .pytest_cache statick.egg-info/ statick_output/* .tox/ *.log
find . -type d -name .mypy_cache -exec rm -rf {} \;
find . -type d -name __pycache__ -exec rm -rf {} \;
