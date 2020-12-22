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
* [Existing Plugins](#existing-plugins)
  * [Discovery Plugins](#discovery-plugins)
  * [Tool Plugins](#tool-plugins)
* [Customization](#customization)
  * [User Paths](#user-paths)
  * [Custom Profile](#custom-profile)
  * [Custom Configuration](#custom-configuration)
  * [Custom Cppcheck Configuration](#custom-cppcheck-configuration)
  * [Custom CMake Flags](#custom-cmake-flags)
* [Custom Plugins](#custom-plugins)
* [ROS Workspaces](#ros-workspaces)
* [Examples](#examples)
* [Troubleshooting](#troubleshooting)
  * [Make Tool Plugin](#make-tool-plugin)
  * [CMake Discovery Plugin](#cmake-discovery-plugin)
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
The standard `statick` command treats the _package_ path as a single package.
Statick will explicitly look for ROS packages and treat each of them as an individual unit when running `statick_ws`.

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
_Levels_ are defined in the `config.yaml` file.
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

In the following `config.yaml` example the `objective` _level_ inherits from and modifies the `threshold` _level_.
The `pylint` flags from `threshold` are completely modified by the `objective` _level_, and the `clang-tidy` _tool_ is
new for the `objective` _level_.

```yaml
levels:
  threshold:
    tool:
      pylint:
        flags: "--disable=R,I,C0302,W0141,W0142,W0511,W0703
                --max-line-length=100
                --good-names=f,x,y,z,t,dx,dy,dz,dt,i,j,k,ex,Run,_
                --dummy-variables-rgx='(_+[a-zA-Z0-9]*?$$)|dummy*'"
      make:
        flags: "-Wall -Wextra -Wuninitialized -Woverloaded-virtual -Wnon-virtual-dtor -Wold-style-cast
                -Wno-unused-variable -Wno-unused-but-set-variable -Wno-unused-parameter"
      catkin_lint:
        flags: "-W2 --ignore DESCRIPTION_BOILERPLATE,DESCRIPTION_MEANINGLESS,GLOBAL_VAR_COLLISION,LINK_DIRECTORY,LITERAL_PROJECT_NAME,TARGET_NAME_COLLISION"
      cppcheck:
        flags: "-j 4 --suppress=unreadVariable --suppress=unusedPrivateFunction --suppress=unusedStructMember
                --enable=warning,style --config-exclude=/usr --template='[{file}:{line}]: ({severity} {id}) {message}'"
      cpplint:
        # These flags must remain on one line to not break the flag parsing
        flags: "--filter=-build/header_guard,-build/include,-build/include_order,-build/c++11,-readability/function,-readability/streams,-readability/todo,-readability/namespace,-readability/multiline_comment,-readability/fn_size,-readability/alt_tokens,-readability/braces,-readability/inheritance,-runtime/indentation_namespace,-runtime/int,-runtime/threadsafe_fn,-runtime/references,-runtime/array,-whitespace,-legal"

  objective:
    inherits_from: "threshold"
    tool:
      pylint:
        flags: "--disable=I0011,W0141,W0142,W0511
                --max-line-length=100
                --good-names=f,x,y,z,t,dx,dy,dz,dt,i,j,k,ex,Run,_
                --dummy-variables-rgx='(_+[a-zA-Z0-9]*?$$)|dummy*'"
      clang-tidy:
        # These flags must remain on one line to not break the flag parsing
        # cert-err58-cpp gives unwanted error for pluginlib code
        flags: "-checks='*,-cert-err58-cpp,-cert-err60-cpp,-clang-analyzer-deadcode.DeadStores,-clang-analyzer-alpha.deadcode.UnreachableCode,-clang-analyzer-optin.performance.Padding,-cppcoreguidelines-*,-google-readability-namespace-comments,-google-runtime-int,-llvm-include-order,-llvm-namespace-comment,-modernize-*,-misc-unused-parameters,-readability-else-after-return'"
      xmllint:
        flags: ""
      yamllint:
        flags: "-d '{extends: default,
                     rules: {
                       colons: {max-spaces-before: 0, max-spaces-after: -1},
                       commas: disable,
                       document-start: disable,
                       line-length: disable}}'"
      cmakelint:
        flags: "--spaces=2 --filter=-linelength,-whitespace/indent"
```

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

With the built-in configuration files the default _profile_ uses `sei_cert` as the default _level_.
This _level_ sets all available _tools_ to use flags that find issues listed in
Carnegie Mellon University Software Engineering Institute
"CERT C++ Coding Standard: Rules for Developing Safe, Reliable, and Secure Systems".
The rules and flags can be found in the
[SEI CERT C/C++ Analyzers](https://wiki.sei.cmu.edu/confluence/display/cplusplus/CC.+Analyzers) chapter.

### Exceptions

_Exceptions_ are used to ignore false positive warnings or warnings that will not be corrected.
This is a very important part of Statick, as many _tools_ are notorious for generating false positive warnings,
and sometimes source code in a project is not allowed to be modified for various reasons.
Statick allows _exceptions_ to be specified in three different ways:

* Placing a comment with `NOLINT` on the line of source code generating the warning.
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
The `globs` key is a list of globs of files to ignore.
The glob could also be a specific filename.
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

## Existing Plugins

### Discovery Plugins

Note that if a file exists without the extension listed it can still be discovered if the `file` command identifies it
as a specific file type.
This type of discovery must be supported by the discovery plugin and only works on operating systems where the `file`
command exists.

File Type | Extensions
:-------- | :---------
catkin    | `CMakeLists.txt` and `package.xml`
C         | `.c`, `.cc`, `.cpp`, `.cxx`, `.h`, `.hxx`, `.hpp`
CMake     | `CMakeLists.txt`
java      | `.class`, `.java`
Maven     | `pom.xml`
Perl      | `.pl`
Python    | `.py`
ROS       | `CMakeLists.txt` and `package.xml`
Shell     | `.sh`, `.bash`, `.zsh`, `.csh`, `.ksh`, `.dash`
XML       | `.xml`, `.launch`
Yaml      | `.yaml`

The `.launch` extension is mapped to XML files due to use with ROS launch files.

### Tool Plugins

Tool | About
:--- | :----
[bandit][bandit]             | Bandit is a tool designed to find common security issues in Python code.
[black][black]               | The uncompromising Python code formatter
[catkin_lint][catkin_lint]   | Check catkin packages for common errors
[cccc][cccc]                 | Source code counter and metrics tool for C++, C, and Java
[clang-format][clang-format] | Format C/C++/Java/JavaScript/Objective-C/Protobuf/C# code.
[clang-tidy][clang-tidy]     | Provide an extensible framework for diagnosing and fixing typical programming errors.
[cmakelint][cmakelint]       | The cmake-lint program will check your listfiles for style violations, common mistakes, and anti-patterns.
[cppcheck][cppcheck]         | static analysis of C/C++ code
[cpplint][cpplint]           | Static code checker for C++
[docformatter][docformatter] | Formats docstrings to follow PEP 257
[flawfinder][flawfinder]     | Examines C/C++ source code and reports possible security weaknesses ("flaws") sorted by risk level.
[lizard][lizard]             | A simple code complexity analyser without caring about the C/C++ header files or Java imports, supports most of the popular languages.
[make][make]                 | C++ compiler.
[mypy][mypy]                 | Optional static typing for Python 3 and 2 (PEP 484)
[perlcritic][perlcritic]     | Critique Perl source code for best-practices.
[pycodestyle][pycodestyle]   | Python style guide checker
[pydocstyle][pydocstyle]     | A static analysis tool for checking compliance with Python docstring conventions.
[pyflakes][pyflakes]         | A simple program which checks Python source files for errors
[pylint][pylint]             | It's not just a linter that annoys you!
[shellcheck][shellcheck]     | A static analysis tool for shell scripts
[spotbugs][spotbugs]         | A tool for static analysis to look for bugs in Java code.
[uncrustify][uncrustify]     | Code beautifier
[xmllint][xmllint]           | Lint XML files.
[yamllint][yamllint]         | A linter for YAML files.

## Customization

### User Paths

_User paths_ are passed into Statick with the `--user-paths` flag.
This is where you can place custom plugins or custom configurations.

The basic structure of a user path directory is

```shell
user_path_root
 |- plugins
 |- rsc
```

User-defined plugins are stored in the `plugins` directory.
Configuration files used by the plugins are stored in the `rsc` directory.

It is possible to use a comma-separated chain of _user paths_ with Statick.
Statick will look for plugins and configuaration files in the order of the paths passed to it.
Files from paths earlier in the list will override files from paths later in the list.
An example is provided below.

```shell
my_org_config
 |- rsc
     |- config.yaml
     |- exceptions.yaml

my_project_config
 |- rsc
     | - exceptions.yaml
```

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

### Custom CMake Flags

The default values for use when running CMake were hard-coded.
We have since added the ability to set arbitrary CMake flags, but left the default values alone for backwards compatibility.
In order to use custom CMake flags you can list them when invoking `statick`.
Due to the likely situation where a leading hyphen will be used in custom CMake flags the syntax is slightly
different than for other flags.
The equals sign and double quotes must be used when specifying `--cmake-flags`.

```shell
statick src/my_pkg --cmake-flags="-DFIRST_FLAG=x,-DSECOND_FLAG=y"
```

## Custom Plugins

If you have the need to support any type of _discovery_, _tool_, or _reporting_ plugin that does not come built-in
with Statick then you can write a custom plugin.

Plugins consist of both a Python file and a `yapsy` file.
For a description of how yapsy works, check out the [yapsy documentation](http://yapsy.sourceforge.net/).

A _user path_ with some custom plugins may look like

```shell
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
```

For the actual implementation of a plugin, it is recommended to copy a suitable default plugin provided by Statick and
modify as needed.

For the contents of `setup.py`, it is recommended to copy a working external plugin.
Some examples are [statick-fortify](https://github.com/soartech/statick-fortify) and [statick-tex](https://github.com/tdenewiler/statick-tex).
Those plugins are set up in such a way that they work with Statick when released on PyPI.

## Examples

Examples are provided in the [examples](examples) directory.
You can see how to run Statick against a [ROS package](examples/navigation), a pure [CMake package](examples/sbpl),
and a pure [Python package](examples/werkzeug).

## ROS Workspaces

Statick started by being used to scan [ROS][ros] workspaces for issues.
The `statick_ws` utility provides support for running against a ROS workspace and identifying individual ROS packages
within the workspace.
Each ROS package will then get a unique directory of results in the Statick output directory.
This can be helpful for presenting results using various reporting plugins.

For example, suppose you have the following directory layout for the ROS workspace.

* /home/user/ws
  * src
    * package1
    * package2
    * subdir
      * package3
      * package4
      * package5
  * build
  * devel

Statick should be run against the ROS workspace source directory.
Note that you can provide relative paths to the source directory.

```shell
statick_ws /home/user/ws/src --output-directory <output directory>
```

Statick can also run against a subset of the source directory in a ROS workspace.

```shell
statick_ws /home/user/ws/src/subdir --output-directory <output directory>
```

## Troubleshooting

### Make Tool Plugin

If you are running Statick against a ROS package and get an error that there is no rule to make target `clean`,
and that the package is not CMake, it usually means that you did not specify a single package.
For example, this is what happens when you tell Statick to analyze a ROS workspace and do not use `statick_ws`.

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

### CMake Discovery Plugin

If you are running Statick against a ROS package and get an error that no module named `ament_package` can be found,
it usually means that you did not source a ROS environment setup file.

```shell
Running cmake discovery plugin...
  Found cmake package /home/user/src/ws/src/repo/package/CMakeLists.txt
Problem running CMake! Returncode = 1
.
.
.
Traceback (most recent call last):
  File "/opt/ros/foxy/share/ament_cmake_core/cmake/package_templates/templates_2_cmake.py", line 21, in <module>
    from ament_package.templates import get_environment_hook_template_path
ModuleNotFoundError: No module named 'ament_package'
CMake Error at /opt/ros/foxy/share/ament_cmake_core/cmake/ament_cmake_package_templates-extras.cmake:41 (message):
  execute_process(/home/user/.pyenv/shims/python3
  /opt/ros/foxy/share/ament_cmake_core/cmake/package_templates/templates_2_cmake.py
  /home/user/src/ws/statick-output/package-sei_cert/build/ament_cmake_package_templates/templates.cmake)
  returned error code 1
.
.
.
-- Configuring incomplete, errors occurred!
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
mypy --ignore-missing-imports --strict --allow-untyped-decorators --html-report report/ --txt-report report statick statick_tool/
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

[bandit]: https://github.com/PyCQA/bandit
[black]: https://github.com/psf/black
[catkin_lint]: https://github.com/fkie/catkin_lint
[cccc]: https://github.com/sarnold/cccc
[clang-format]: https://clang.llvm.org/docs/ClangFormat.html
[clang-tidy]: http://clang.llvm.org/extra/clang-tidy/
[cmakelint]: https://cmake-format.readthedocs.io/en/latest/cmake-lint.html
[cppcheck]: https://github.com/danmar/cppcheck/
[cpplint]: https://github.com/cpplint/cpplint
[docformatter]: https://github.com/myint/docformatter
[flawfinder]: https://dwheeler.com/flawfinder/
[lizard]: https://github.com/terryyin/lizard
[make]: https://gcc.gnu.org/onlinedocs/libstdc++/index.html
[mypy]: https://github.com/python/mypy
[perlcritic]: http://perlcritic.com/
[pycodestyle]: https://pycodestyle.pycqa.org/en/latest/
[pydocstyle]: http://www.pydocstyle.org/en/stable/
[pyflakes]: https://github.com/PyCQA/pyflakes
[pylint]: https://pylint.org/
[ros]: https://www.ros.org/
[shellcheck]: https://github.com/koalaman/shellcheck
[spotbugs]: https://github.com/spotbugs/spotbugs
[uncrustify]: https://github.com/uncrustify/uncrustify
[xmllint]: http://xmlsoft.org/
[yamllint]: https://yamllint.readthedocs.io/en/stable/
