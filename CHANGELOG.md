# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

## Unreleased
### Added:

### Fixed:

### Removed:

## v0.2.15 - 2019-12-26
### Added:
  - Changed build and deploy Travis stages from Python 2.7 to Python 3.5.
  - Unit tests for file dicovery now cover the case where the `file` command is not available.

### Fixed:
  - Bug found when using tool under Ubuntu 18.04 where the diff calculated for clang-format desired and actual
    configurations would produce empty lines.
    This caused the tool to throw an exception.
    Fixed by checking that there is diff output before trying to read it.
  - The uncrustify unit test now works on Ubuntu Bionic.
  - Several pylint issues related to unnecessary elif and else after break/continue/raise lines were cleaned up.

### Removed:

## v0.2.14 - 2019-11-21
### Added:
  - Support for Python 3.8 (build and unit tests on Travis).
  - Updated unit tests for main Statick module.

### Fixed:
  - Install patterns updated to prevent picking up the `plugin_mapping` directory multiple times. (@kkredit)
  - Handle more varied output from pyflakes tool.

### Removed:
  - Removed support for previously deprecated pep8 and pep257 tools.
    The pycodestyle and pydocstyle tools provide the same functionality, only the tool name needs to change in the configuration file.

## v0.2.13 - 2019-09-22
### Added:
  - Python 3.8-dev is now part of the test matrix for Travis jobs.

## v0.2.12 - 2019-09-08
### Fixed:
  - Reverted method used by clang-format tool plugin to obtain output.
    New way worked locally but failed on Travis CI jobs.

## v0.2.11 - 2019-09-08
### Added:
  - cpplint added to requirements.txt
  - Updated and new unit tests for:
      - cpplint tool plugin
      - xmllint tool plugin
      - yamllint tool plugin
      - catkin_lint tool plugin
      - make tool plugin
      - clang-format tool plugin
      - pylint tool plugin
      - lizard tool plugin
      - pyflakes tool plugin
      - cmakelint tool plugin
      - uncrustify tool plugin
      - CCCC tool plugin
      - pycodestyle tool plugin
      - perlcritic tool plugin
      - CMake discovery plugin
      - config module
      - discovery module
      - exceptions module

### Removed:
  - Gauntlet tool removed due to perceived lack of use in community.

## v0.2.10 - 2019-05-27
### Added:
  - Improved documentation on how to create third-party plugins that can be released to PyPI.
  - Support for custom files for defining configuration and exceptions.

### Fixed:
  - Added additional error checking prior to opening and reading configuration files.

## v0.2.9 - 2019-04-30
### Added:
  - Started keeping a Changelog (@creffett)
  - Configuration support for tex tools (chktex and lacheck plugins in separate repository)

### Fixed:
  - Fix backtrace when Statick is run with a nonexistent file as a profile (@creffett)
