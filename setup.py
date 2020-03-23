"""Setup."""


try:
    from setuptools import setup  # NOLINT
except:  # pylint: disable=bare-except # noqa: E722 # NOLINT
    from distutils.core import setup  # pylint: disable=wrong-import-order

import statick_tool

with open('README.md') as f:
    LONG_DESCRIPTION = f.read()

TEST_DEPS = [
    'backports.tempfile',
    'pylint-django',
    'pytest',
    'mock',
    'tox',
]

EXTRAS = {
    'test': TEST_DEPS,
}

setup(
    name='statick',
    description='Making code quality easier.',
    author='SSC Pacific',
    version=statick_tool.__version__,
    packages=['statick_tool'],
    package_data={'statick_tool': ['rsc/*.*', 'rsc/.clang-format',
                                   'rsc/plugin_mapping/*',
                                   'plugins/*.py', 'plugins/discovery/*',
                                   'plugins/tool/*', 'plugins/reporting/*']},
    scripts=['statick', 'statick_ws'],
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
    install_requires=['bandit', 'cmakelint', 'cpplint', 'deprecated',
                      'flawfinder', 'lizard', 'pycodestyle', 'pydocstyle',
                      'pyflakes', 'pylint', 'PyYAML', 'xmltodict', 'yamllint',
                      'yapsy'],
    tests_require=TEST_DEPS,
    extras_require=EXTRAS,
    url='https://github.com/sscpac/statick',
    classifiers=[
        "License :: CC0 1.0 Universal (CC0 1.0) Public Domain Dedication",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Software Development :: Testing",
    ],
)
