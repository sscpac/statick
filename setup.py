"""Setup."""


try:
    from setuptools import setup
except:  # pylint: disable=bare-except # noqa: E722 # NOLINT
    from distutils.core import setup  # pylint: disable=wrong-import-order

import statick_tool

with open('README.md') as f:
    long_description = f.read()  # pylint: disable=invalid-name

setup(
    author='SSC Pacific',
    name='statick',
    description='Tool for running static analysis tools against packages of code.',
    version=statick_tool.__version__,
    packages=['statick_tool'],
    package_data={'statick_tool': ['rsc/*', 'rsc/.clang-format', 'rsc/plugin_mapping/*',
                                   'plugins/*.py', 'plugins/discovery/*',
                                   'plugins/tool/*', 'plugins/reporting/*']},
    scripts=['statick', 'statick_ws', 'statick_gauntlet'],
    long_description=long_description,
    long_description_content_type='text/markdown',
    install_requires=['bandit', 'cmakelint', 'lizard', 'pycodestyle',
                      'pydocstyle', 'pyflakes', 'pylint', 'PyYAML',
                      'xmltodict', 'yamllint', 'yapsy'],
    url='https://github.com/sscpac/statick',
    classifiers=[
        "License :: CC0 1.0 Universal (CC0 1.0) Public Domain Dedication",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Software Development :: Testing",
    ],
)
