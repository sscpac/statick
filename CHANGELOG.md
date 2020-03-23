# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)

## Unreleased

### Added

### Fixed

### Removed

## v0.3.7 - 2020-03-23

### Added

- Formatted all code using black.
  Added Github Action to ensure future commits are consistent with black formatting.
- Added a tool plugin for [black](https://github.com/psf/black).
- Added a tool plugin for [mypy](http://mypy-lang.org/).

## v0.3.6 - 2020-03-18

### Fixed

- A bug in how type hints were applied caused issues with Python 3.5, which is the
  default on Ubuntu 16.04-based operating systems.
  Switching to comment-style type hints for variables made Statick work with Python 3.5 again.
  Thanks to @kogut for discovering the issue.

## v0.3.5 - 2020-03-18

### Added

- Using type hints as introduced in Python 3.5 and improved in Python 3.6.
  Type hints are described in [PEP 438](https://www.python.org/dev/peps/pep-0483/)
  and [PEP 484](https://www.python.org/dev/peps/pep-0484/).
  They provide static typing for methods and variables.
  The use of mypy is encouraged to look for errors in expected types.
- Using [statick-md](https://github.com/sscpac/statick-md) plugin to check Markdown files.

### Fixed

### Removed

- No longer supporting pypy3 due to issues with type hints and mypy.

## v0.3.4 - 2020-02-26

### Added

- Using fewer CMake targets during build.

### Fixed

- Open issues filename with utf-8 encoding to avoid UnicodeDecodeError exception.
- CMake and Spotbugs plugins no longer write output logs if output directory is not specified.

### Removed

## v0.3.3 - 2020-02-19

### Added

- Github workflows for Actions.
  These are just starting but they may replace Travis CI in the future.
- Made 3.8 the default version for CI testing.

### Fixed

- Added needed `install_requires` entries in setup.py to allow Statick to work out of the box (in the pip sense).
- The `statick_ws` command now supports running without an output directory.
- The xmllint unit tests will be skipped if xmllint executable is not available.
  This can happen when apt dependencies are not going to be installed.

### Removed

- Python 3.5 is no longer supported.
  It is not getting updates any longer, and is not available on Github Actions.

## v0.3.2 - 2020-02-18

### Added

- Ability for Jenkins Warning NG reporting plugin to handle severity as int or string type. (@axydes)

### Fixed

### Removed

## v0.3.1 - 2020-02-06

### Added

- Reporting plugin for the
  [Jenkins Warnings Next Generation](https://wiki.jenkins.io/display/JENKINS/Warnings+Next+Generation+Plugin)
  plugin. (@axydes)
  - Updated Jenkinsfile template to reflect usage of new plugin.
- Renamed file writing reporting plugin to write Jenkins warnings reporting plugin. (@axydes)
- More helpful, explicit error messages from the clang-format tool plugin.

### Fixed

- Not writing log files if no output directory is specified.
- The make tool plugin will now cause Statick to exit with error condition if the tool does not run successfully.

### Removed

## v0.3.0 - 2020-01-31

Note that a breaking change was made to how the output directory is specified for writing results to a file.
The default changed from always writing output files to only writing output files when the `--output-directory`
argument is specified.
The previous way to run Statick was:

```shell
statick my-project statick-output
```

With this update you can run with output files:

```shell
statick my-project --output-directory statick-output
```

or without output files:

```shell
statick my-project
```

### Added

- Skipping integration tests for tool plugins where the tool is not available via pip.
- Statick works better on Ubuntu 18.04. (@kogut)

### Fixed

- Clang-format tool now supports multiple language specifications in the configuration file.
  The fix also allowed for increased unit test coverage of the tool. (@xydesa)

### Removed

- Support for Python 2.7, Python 3.4, and pypy.
- Required argument for `output_directory`.
  It is now an optional argument `output-directory` as described above.

## v0.2.15 - 2019-12-26

### Added

- Changed build and deploy Travis stages from Python 2.7 to Python 3.5.
- Unit tests for file dicovery now cover the case where the `file` command is not available.

### Fixed

- Bug found when using tool under Ubuntu 18.04 where the diff calculated for clang-format desired and actual
  configurations would produce empty lines.
  This caused the tool to throw an exception.
  Fixed by checking that there is diff output before trying to read it.
- The uncrustify unit test now works on Ubuntu Bionic.
- Several pylint issues related to unnecessary elif and else after break/continue/raise lines were cleaned up.

### Removed

## v0.2.14 - 2019-11-21

### Added

- Support for Python 3.8 (build and unit tests on Travis).
- Updated unit tests for main Statick module.

### Fixed

- Install patterns updated to prevent picking up the `plugin_mapping` directory multiple times. (@kkredit)
- Handle more varied output from pyflakes tool.

### Removed

- Removed support for previously deprecated pep8 and pep257 tools.
  The pycodestyle and pydocstyle tools provide the same functionality, only the tool name needs to change in the
  configuration file.

## v0.2.13 - 2019-09-22

### Added

- Python 3.8-dev is now part of the test matrix for Travis jobs.

## v0.2.12 - 2019-09-08

### Fixed

- Reverted method used by clang-format tool plugin to obtain output.
  New way worked locally but failed on Travis CI jobs.

## v0.2.11 - 2019-09-08

### Added

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

### Removed

- Gauntlet tool removed due to perceived lack of use in community.

## v0.2.10 - 2019-05-27

### Added

- Improved documentation on how to create third-party plugins that can be released to PyPI.
- Support for custom files for defining configuration and exceptions.

### Fixed

- Added additional error checking prior to opening and reading configuration files.

## v0.2.9 - 2019-04-30

### Added

- Started keeping a Changelog (@creffett)
- Configuration support for tex tools (chktex and lacheck plugins in separate repository)

### Fixed

- Fix backtrace when Statick is run with a nonexistent file as a profile (@creffett)
