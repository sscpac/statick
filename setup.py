"""Setup."""


from setuptools import setup  # NOLINT

import statick_tool

with open("README.md", encoding="utf8") as f:
    LONG_DESCRIPTION = f.read()

TEST_DEPS = [
    "backports.tempfile",
    "pylint-django",
    "pytest",
    "mock",
    "tox",
]

EXTRAS = {
    "test": TEST_DEPS,
}

setup(
    name="statick",
    description="Making code quality easier.",
    author="SSC Pacific",
    version=statick_tool.__version__,
    packages=["statick_tool"],
    package_data={
        "statick_tool": [
            "rsc/.*",
            "rsc/*",
            "rsc/plugin_mapping/*",
            "plugins/*.py",
            "plugins/discovery/*",
            "plugins/tool/*",
            "plugins/reporting/*",
        ]
    },
    scripts=["statick"],
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    install_requires=[
        "bandit",
        "black",
        "cmakelint",
        "cpplint",
        "deprecated",
        "flawfinder",
        "isort",
        "lizard",
        "pycodestyle",
        "pydocstyle",
        "pyflakes",
        "pylint",
        "PyYAML",
        "tabulate",
        "xmltodict",
        "yamllint",
        "yapsy",
    ],
    tests_require=TEST_DEPS,
    extras_require=EXTRAS,
    url="https://github.com/sscpac/statick",
    classifiers=[
        "License :: CC0 1.0 Universal (CC0 1.0) Public Domain Dedication",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Testing",
    ],
)
