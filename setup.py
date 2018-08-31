"""Setup."""


try:
    from setuptools import setup
except:  # pylint: disable=bare-except
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
    package_data={'statick_tool': ['rsc/*', 'rsc/.clang-format',
                                   'plugins/*.py', 'plugins/discovery/*',
                                   'plugins/tool/*']},
    scripts=['statick', 'statick_ws', 'statick_gauntlet'],
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/sscpac/statick'
)
