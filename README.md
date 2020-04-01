# Statick

| Service | Status |
| ------- | ------ |
| Build   | [![Travis-CI](https://api.travis-ci.org/sscpac/statick.svg?branch=master)](https://travis-ci.org/sscpac/statick/branches) |
| PyPI    | [![PyPI version](https://badge.fury.io/py/statick.svg)](https://badge.fury.io/py/statick) |
| Codecov | [![Codecov](https://codecov.io/gh/sscpac/statick/branch/master/graphs/badge.svg)](https://codecov.io/gh/sscpac/statick/) |

![Python Versions](https://img.shields.io/pypi/pyversions/statick.svg)
![License](https://img.shields.io/pypi/l/statick.svg)
[![Doc](https://readthedocs.org/projects/statick/badge/?version=latest)](https://statick.readthedocs.io/en/latest/?badge=latest)
[![Checked with mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/)
![Daily Downloads](https://img.shields.io/pypi/dd/statick.svg)
![Weekly Downloads](https://img.shields.io/pypi/dw/statick.svg)
![Monthly Downloads](https://img.shields.io/pypi/dm/statick.svg)

Statick is a set of tools to analyze software packages.

This README only covers basic usage of Statick.
For more detailed information, see the [Statick User Guide](GUIDE.md).
The User Guide is especially important for tips on creating and using your own testing levels and exceptions.

Statick uses a plugin system to load plugins from both a default resource location and also
user-definable locations to run against software.

The plugins for the statick scans are divided into three categories:

* Discovery plugins that find files to scan inside of a code package.
* Tool plugins to run analysis programs against the files discovered by the discovery plugins.
* Reporting plugins to output the analysis results in various formats.

## Install Required Tools

The below commands are for Ubuntu 16.04.
The exact package names may vary for other systems.

These packages are for the tools used by the default configuration of Statick.
Depending on your usage and configuration, you may not need these packages.

    $ cat install.txt  | xargs sudo apt-get install -y
    $ pip install -r requirements.txt

To run against ROS packages there are a few more system packages to get.
This command assumes you have setup the [ROS apt repository](http://wiki.ros.org/ROS/Installation) for your system.

    $ cat ros-deps.txt  | xargs sudo apt-get install

## Setup cppcheck

cppcheck is a static analysis tool for C++.
It is possible to set a required version of the tool to ensure consistency of output.
The required version of the tool can be passed in as part of the tool flags in the `config.yaml` file.
If a flag is not set for the version then any installed version of the tool will run.
If a required version is set but not found then the tool will not run.
An example of how to install a specific version of cppcheck is below.

In some spot on your filesystem (for example `~/src`)

    $ git clone --branch 1.81 https://github.com/danmar/cppcheck.git
    $ cd cppcheck
    $ make SRCDIR=build CFGDIR=/usr/share/cppcheck/ HAVE_RULES=yes
    $ sudo make install SRCDIR=build CFGDIR=/usr/share/cppcheck/ HAVE_RULES=yes

## Statick Installation (Optional)

To install Statick on your system and make it part of your `$PATH`:

    $ sudo python setup.py install

## Running

If you are running from an installed version, you will use the `statick` or `statick_ws` command.
If you are running job from a local version in your workspace, you can run it like
`~/src/my_ws/src/ssc/statick/statick` or `~/src/my_ws/src/ssc/statick/statick_ws`.

For a description of all available arguments, pass the `--help` option to either program.

### For single packages

    $ statick <path of package> --output-directory <output path>

"Path of package" is the path of the package to be scanned.

"Output path" is optional and is the path where build and output files are stored.
This should initially be an empty directory separate from your regular source and build directories.
This directory must already exist before running the program.

If you are using this with a ROS Ament/Catkin workspace, you must have your workspace `setup.bash` sourced before
running the tool.

### For a whole or partial ament/catkin workspace

    $ statick_ws <path of src tree> --output-directory <output path>

"path of src tree" is the src directory underneath your ament/catkin workspace root or any directory under that.

"Output path" is optional and is the path where build and output files are stored.
This should initially be an empty directory separate from your regular source and build directories.
This directory must already exist before running the program.

## Example Usage

Here are some example use cases for the level of compliance we are enforcing for now.

### For a single package

    $ cd ~/src/my_ws
    $ . devel/setup.bash
    $ mkdir statick_output
    $ statick src/my_org/my_pkg statick_output

### For a part of a workspace

    $ cd ~/src/my_ws
    $ . devel/setup.bash
    $ mkdir statick_output
    $ statick_ws src/my_org statick_output

### For a whole workspace

    $ cd ~/src/my_ws
    $ . devel/setup.bash
    $ mkdir statick_output
    $ statick_ws src statick_output

## Troubleshooting

### Make plugin

If you are running statick against a ROS package and get an error that there is no rule to make target `clean`,
and that the package is not CMake, it usually means that you did not specify a single package.
Instead, this is what happens when you tell statick to analyze a ROS workspace and do not use `statick_ws`.

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
