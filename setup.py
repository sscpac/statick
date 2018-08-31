"""
Setup.
"""


try:
    from setuptools import setup
except:  # pylint: disable=bare-except
    from distutils.core import setup  # pylint: disable=wrong-import-order

import statick_tool

setup(
    name='statick',
    version=statick_tool.__version__,
    packages=['statick_tool'],
    package_data={'statick_tool': ['rsc/*', 'rsc/.clang-format',
                                   'plugins/*.py', 'plugins/discovery/*',
                                   'plugins/tool/*']},
    scripts=['statick', 'statick_ws', 'statick_gauntlet']
)
