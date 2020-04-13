#!/bin/bash

rm -rf build/ dist/ output-py* .pytest_cache statick.egg-info/ statick_output/* .tox/
find . -type d -name .mypy_cache | xargs rm -rf
find . -type d -name __pycache__ | xargs rm -rf
