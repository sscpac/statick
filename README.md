# Statick

![Unit Tests](https://github.com/sscpac/statick/workflows/Statick/badge.svg)
[![Codecov](https://codecov.io/gh/sscpac/statick/branch/master/graphs/badge.svg)](https://codecov.io/gh/sscpac/statick/)
[![PyPI version](https://badge.fury.io/py/statick.svg)](https://badge.fury.io/py/statick)
![Python Versions](https://img.shields.io/pypi/pyversions/statick.svg)
![License](https://img.shields.io/pypi/l/statick.svg)
[![Doc](https://readthedocs.org/projects/statick/badge/?version=latest)](https://statick.readthedocs.io/en/latest/?badge=latest)
[![Checked with mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/)
![Daily Downloads](https://img.shields.io/pypi/dd/statick.svg)
![Weekly Downloads](https://img.shields.io/pypi/dw/statick.svg)
![Monthly Downloads](https://img.shields.io/pypi/dm/statick.svg)

Statick makes running static analysis and linting tools easier for all your projects.
Each static analysis tool has strengths and weaknesses.
Best practices recommend running multiple tools to get the best results.
Statick has plugins that interface with a large number of static analysis and linting tools,
allowing you to run a single tool to get all the results at once.

Many tools are known for generating a large number of fasle positives so Statick provides multiple ways to add
exceptions to suppress false positives.
The types of warnings to generate is highly dependent on your specific project, and Statick makes it easy to run each
tool with custom flags to tailor the tools for the issues you care about.
Once the results are ready, Statick provides multiple output formats.
The results can be printed to the screen, or sent to a continuous integration tool like Jenkins.

Statick is a plugin-based tool with an explicit goal to support external, optionally proprietary, tools and reporting mechanisms.

## Table of Contents

* [Installation](#installation)
* [Basic Usage](#basic-usage)
* [Concepts](#contents)
  * [Discovery](#discovery)
  * [Tools](#tools)
  * [Reporting](#reporting)
* [Basic Configuration](#basic-configuration)
  * [Levels](#levels)
  * [Profiles](#profiles)
  * [Exceptions](#exceptions)
* [Advanced Installation](#advanced-installation)
* [Customization](#customization)
  * [User Paths](#user-paths)
  * [Custom Profile](#custom-profile)
  * [Custom Configuration](#custom-configuration)
  * [Custom Cppcheck Configuration](#custom-cppcheck-configuration)
* [Custom Plugins](#custom-plugins)
* [Examples](#examples)
* [Troubleshooting](#troubleshooting)
  * [Make plugin](#make-plugin)
* [Contributing](#contributing)
  * [Tests](#tests)
  * [Mypy](#mypy)
  * [Formatting](#formatting)
* [Original Author](#original-author)

## Installation

Statick requires Python 3.5+ to run, but can be used to analyze Python2 projects, among many other languages.

The recommended install method is

```shell
python3 -m pip install statick
```

You will also need to install any tools you want to use.
Some tools are installed with Statick if you install via pip.
Other tools can be installed using a method supported by your operating system.
For example, on Ubuntu Linux if you want to use the `clang-tidy` _tool_ plugin you can install the tool with apt.

```shell
apt install clang-tidy
```

## Basic Usage

```shell
statick <path of package> --output-directory <output path>
```

This will run the default level and print the results to the console.

## Concepts

Early Statick development and use was targeted towards [Robot Operating System](https://www.ros.org/) (ROS),
with results to be displayed on Jenkins.
Both ROS and Jenkins have a concept of software components as _packages_.
Statick will explicitly look for ROS packages and treat each of them as an individual unit, especially with the
command `statick_ws`.

At the same time Statick is ROS agnostic and can be used against many different programming languages.
The term _package_ is still used to designate a directory with source code.

When Statick is invoked there are three major steps involved:

* _Discover_ source code files in each _package_ and determine what programming language the files are written in.
* Run all configured _tools_ against source files that the individual _tool_ can analyze to find issues.
* _Report_ the results.

The default behavior for Statick is to return an exit code of success unless Statick has an internal error.
It can be useful to have Statick return an exit code indicating an error if any issues are found.
That behavior can be enabled by passing in the `--check` flag.
For example, if you are running Statick as part of a continuous integration pipeline and you want the job to fail on
any Statick warnings you can do that by using the `--check` flag.

### Discovery

_Discovery_ plugins search through the package path to determine if each file is of a specific type.
The type of each file is determined by the file extension and, if the operating system supports it, the output of the
`file` command.

### Tools

_Tool_ plugins are the interface between a static analysis or linting tool and Statick.
Each _tool_ plugin provides the types of files it can analyze, then the output of the _discovery_ plugins is used to
determine the specific files that should be analyzed by each tool.

The _tool_ plugin can also specify any other tools that are required to run before the current tool can act.
For example, `cppcheck` depends on the output of the `make` tool.

The _tool_ plugin then scans each package by invoking the binary associated with the tool.
The output of the scan is parsed to generate the list of issues discovered by Statick.

### Reporting

_Reporting_ plugins output the issues found by the _tool_ plugins.
The currently supported _reporting_ plugins are to print the output to a console and to write an _XML_ file that
can be parsed by Jenkins.

When using the Jenkins _reporting_ plugin, the issues show up formatted and searchable via the
[Jenkins Warnings NG](https://plugins.jenkins.io/warnings-ng/) plugin.
A plot can be added to Jenkins showing the number of Statick warnings over time or per build.
The Statick `--check` flag can be used to cause steps in a Jenkins job to fail if issues are found.
Alternatively, Jenkins can be configured with quality gates to fail if a threshold on the number of issues found is exceeded.

An example [Jenkinsfile](templates/Jenkinsfile) is provided to show how Statick can be used with Jenkins pipelines.

## Basic Configuration

### Levels

Statick has _levels_ of configuration to support testing each _package_ in the desired manner.
Some projects only care about static analysis at a minimal level and do not care about linting for style at all.
Other projects want all the bells and whistles that static analysis and linting have to offer.
That's okay with Statick -- just make a level to match your project needs.

Each _level_ specifies which plugins to run, and which flags to use for each plugin.
If your project only has Python files then your level only needs to run the Python _discovery_ plugin.
If you only want to run _tool_ plugins for _pylint_ and _pyflakes_, a level is how you configure Statick to look for
issues using only those tools.
If you are not using Jenkins then you can specify that you only want the _reporting_ plugin to run that prints issues
to a console.

Each _level_ can be stand-alone or it can _inherit_ from a separate level.
This allows users to gradually build up _levels_ to apply to various packages.
All _packages_ can start by being required to pass a _threshold_ level.
An _objective_ level can build on the _threshold_ level with more tools or more strict flags for each tool.
A gradual transition of packages from _threshold_ to _objective_ can be undertaken.
Flags from the inherited level can be overridden by listing the same tool under the level's `tools` key with a new set
of flags.

### Profiles

_Profiles_ govern how each package will be analyzed by mapping _packages_ to _levels_.
A default _level_ is specified, then any packages that should be run at a non-default _level_ can be listed.

Multiple profiles can exist, and you can specify which one to use with the `--profile` argument.
For example, you can have a `profile_objective.yaml` with stricter levels to run for packages.
Pass this profile to Statick.

```yaml
default: threshold

packages:
  my_package: objective

  my_really_good_package: ultimate
```

The `default` key lists the _level_ to run if no specific level listed for a package.

The `packages` key lists _packages_ and override levels to run for those packages.

### Exceptions

_Exceptions_ are used to ignore false positive warnings or warnings that will not be corrected.
This is a very important part of Statick, as many _tools_ are notorious for generating false positive warnings,
and sometimes source code in a project is not allowed to be modified for various reasons.
Statick allows _exceptions_ to be specified in three different ways:

* Placing `NOLINT` on the line of source code generating the warning.
* Using individual _tool_ methods for ignoring warnings (such as adding `# pylint: disable=<warning>`in Python source code).
* Via an `excpetions.yaml` file.

```yaml
global:
  exceptions:
    file:
      # System headers
      - tools: all
        globs: ["/usr/*"]
      # Auto-generated headers
      - tools: all
        globs: ["*/devel/include/*"]
    message_regex:
      # This is triggered by std::isnan for some reason
      - tools: [clang-tidy]
        regex: "implicit cast 'typename __gnu_cxx.*__type' -> bool"

packages:
  my_package:
    exceptions:
      message_regex:
        - tools: [clang-tidy]
          regex: "header guard does not follow preferred style"
      file:
        - tools: [cppcheck, clang-tidy]
        - globs: ["include/my_package/some_header.h"]

ignore_packages:
  - some_third_party_package
  - some_other_third_party_package
```

There are two types of exceptions that can be used in `exceptions.yaml`.

`file` exceptions ignore all warnings generated by a pattern of files.
The `tools` key can either be `all` to suppress warnings from all tools or a list of specific tools.
The `globs` key is a list of globs of files to ignore.
The glob could also be a specific filename.
For an _exception_ to be applied to a specific issue, it is required that the issue contain an absolute path to the filename.
The path for the issue is set in the _tool_ plugin that generates the issues.

`message_regex` exceptions ignore warnings based on a regular expression match against an error message.
The `tools` key can either be `all` to suppress warnings from all tools or a list of specific tools.
The `regex` key is a regular expression to match against messages.
Information about the regex syntax used by Python can be found [here](https://docs.python.org/2/library/re.html).
The site <https://regex101.com/> can be very helpful when trying to generate regular expressions to match the warnings
you are trying to create an _exception_ for.

_Exceptions_ can either be global or package specific.
To make them global, place them under a key named `global` at the root of the yaml file.
To make them package spefific, place them in a key named after the package under a key named `packages` at the root
level of the yaml.

The `ignore_packages` key is a list of package names that should be skipped when running Statick.

## Advanced Installation

To install Statick from source on your system and make it part of your `$PATH`:

```shell
sudo python3 setup.py install
```

## Customization

### User Paths

_User paths_ are passed into Statick with the `--user-paths` flag.
This is where you can place custom plugins or custom configurations.

The basic structure of a user path directory is

    user_path_root
     |- plugins
     |- rsc

User-defined plugins are stored in the `plugins` directory.
Configuration files used by the plugins are stored in the `rsc` directory.

It is possible to use a comma-separated chain of _user paths_ with Statick.
Statick will look up files in the order of the paths passed to it.
Files from paths earlier in the list will override files from paths later in the list.

    my_org_config
     |- rsc
         |- config.yaml
         |- exceptions.yaml

    my_project_config
     |- rsc
         | - exceptions.yaml

To run Statick with this set of configurations, you would do

```shell
statick src/my_pkg --user-paths my_project_config,my_org_config
```

In this example, Statick would use the `config.yaml` from `my_org_config` and the `exceptions.yaml` from `my_project_config`.

### Custom Profile

To run Statick with a custom _profile_ use

```shell
statick src/my_pkg --user-paths my_project_config --profile custom-profile.yaml
```

### Custom Configuration

To run Statick with a custom _configuration_ containing custom _levels_, use `custom-config.yaml` with custom levels
defined and `custom-profile.yaml` that calls out the use of the custom _levels_ for your _packages_.

```shell
statick src/my_pkg --user-paths my_project_config --profile custom-profile.yaml --config custom-config.yaml
```

### Custom Cppcheck Configuration

Some _tools_ support the use of a custom version.
This is useful when the type of output changes between _tool_ versions and you want to stick with a single version.
The most common scenario when this happens is when you are analyzing your source code on multiple operating systems,
each of which has a different default version for the _tool_.
_Cppcheck_ is a _tool_ like this.

To install a custom version of _Cppcheck_ you can do the following.

```shell
git clone --branch 1.81 https://github.com/danmar/cppcheck.git
cd cppcheck
make SRCDIR=build CFGDIR=/usr/share/cppcheck/ HAVE_RULES=yes
sudo make install SRCDIR=build CFGDIR=/usr/share/cppcheck/ HAVE_RULES=yes
```

## Custom Plugins

If you have the need to support any type of _discovery_, _tool_, or _reporting_ plugin that does not come built-in
with Statick then you can write a custom plugin.

Plugins consist of both a Python file and a `yapsy` file.
For a description of how yapsy works, check out the [yapsy documentation](http://yapsy.sourceforge.net/).

A _user path_ with some custom plugins may look like

    my_custom_config
      setup.py
      |- plugins
         |- my_discovery_plugin
            |- my_discovery_plugin.py
            |- my_discovery_plugin.yapsy
         |- my_tool_plugins
            |- my_tool_plugin.py
            |- my_tool_plugin.yapsy
            |- my_other_tool_plugin.py
            |- my_other_tool_plugin.yapsy
      |- rsc
         |- config.yaml
         |- exceptions.yaml

For the actual implementation of a plugin, it is recommended to copy a suitable default plugin provided by Statick and
modify as needed.

For the contents of `setup.py`, it is recommended to copy a working external plugin.
Some examples are [statick-fortify](https://github.com/soartech/statick-fortify) and [statick-tex](https://github.com/tdenewiler/statick-tex).
Those plugins are set up in such a way that they work with Statick when released on PyPI.

## Examples

Examples are provided in the [examples](examples) directory.
You can see how to run Statick against a [ROS package](examples/navigation), a pure [CMake package](examples/sbpl),
and a pure [Python package](examples/werkzeug).

## Troubleshooting

### Make plugin

If you are running statick against a ROS package and get an error that there is no rule to make target `clean`,
and that the package is not CMake, it usually means that you did not specify a single package.
Instead, this is what happens when you tell statick to analyze a ROS workspace and do not use `statick_ws`.

```shell
Running cmake discovery plugin...
  Package is not cmake.
cmake discovery plugin done.
.
.
.
Running make tool plugin...
make: *** No rule to make target 'clean'.  Stop.
Make failed! Returncode = 2
Exception output:
make tool plugin failed
```

## Contributing

### Tests

Statick supports testing through the [tox](https://tox.readthedocs.io/en/latest) framework.
Tox is used to run tests against multiple versions of python and supports running other tools, such as flake8, as part
of the testing process.
To run tox, use the following commands from a git checkout of `statick`:

```shell
python3 -m pip install tox
tox
```

This will run the test suites in Python virtual environments for each Python version.
If your system does not have one of the Python versions listed in `tox.ini`, that version will be skipped.

If running `tox` locally does not work, one thing to try is to remove the auto-generated output directories such as
`output-py27`, `output-py35`, and `.tox`.
There is an included `clean.sh` shell script that helps with removing auto-generated files.

If you write a new feature for Statick or are fixing a bug, you are strongly encouraged to add unit tests for your contribution.
In particular, it is much easier to test whether a bug is fixed (and identify future regressions) if you can add a small
unit test which replicates the bug.

For _tool_ plugins that are not available via pip it is recommended to skip tests that fail when the tool is not installed.

Before submitting a change, please run tox to check that you have not introduced any regressions or violated any code
style guidelines.

### Mypy

Statick uses [mypy](http://mypy-lang.org/) to check that type hints are being followed properly.
Type hints are described in [PEP 484](https://www.python.org/dev/peps/pep-0484/) and allow for static typing in Python.
To determine if proper types are being used in Statick the following command will show any errors, and create several
types of reports that can be viewed with a text editor or web browser.

```shell
python3 -m pip install mypy
mkdir report
mypy --ignore-missing-imports --html-report report/ --txt-report report statick statick_tool/
```

It is hoped that in the future we will generate coverage reports from mypy and use those to check for regressions.

### Formatting

Statick code is formatted using [black](https://github.com/psf/black).
To fix locally use

```shell
python3 -m pip install black
black statick statick_ws statick_tool tests
```

## Original Author

A special note should be made that the original primary author was Mark Tjersland (@Prognarok).
His commits were scrubbed from git history upon the initial public release.
