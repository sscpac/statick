# Statick User Guide

For basic usage information, see the [README.md](README.md) file provided with Statick.

## Terminology

`package` - A package is the basic unit of software scanned by Statick.
When running the standalone `statick` command, it is the path passed as the first argument.
When running the tree scanning `statick_ws`, it is any package under the path passed as the first argument that meets
certain criteria (currently this criteria is that it contains a `CMakeLists.txt` and `package.xml`)

`discovery plugin` - Discovery plugins are used to find files to scan under a package.
This may involve running a program such as `cmake` or looking for certain file extensions.

`tool plugin` - Tool plugins run code scanning tools against files discovered by a discovery plugin.

`reporting plugin` - Reporting plugins output the results of the tool plugin to a location and in a method defined by
the plugin.
This could be anything from writing a file to uploading to a website.

`user paths` - User paths are a list of directories passed to the `--user-paths` argument.
This is used to pass custom configuration and plugin files to Statick.

`level` - A level is a set of tools and flags to be run against a package.
These allow you to scan different packages at different strictness levels.

## User Paths

The basic structure of a user path directory is

    user_path_root
     |- plugins
     |- rsc

User-defined plugins are stored in the `plugins` directory.
Configuration files used by the plugins are stored in the `rsc` directory.

It is possible to use a comma-separated chain of user paths with Statick.
Statick will look up files in the order of the paths passed to it.
Files from paths earlier in the list will override files from paths later in the list.

    my_org_config
     |- rsc
         |- config.yaml
         |- exceptions.yaml

    my_project_config
     |- rsc
         | - exceptions.yaml

To run Statick with this set of configurations, you would do `statick src/my_pkg statick_output --user-paths my_project_config,my_org_config`.
In this example, Statick would use the `config.yaml` from `my_org_config` and the `exceptions.yaml` from `my_project_config`.

## Customization

Statick allows for customization in two primary ways.

1. Configuration files
2. User-defined plugins

It is encouraged to keep these files in version control either alongside your project or in a repository dedicated to
build configuration.

### Configuration files

#### config.yaml

`config.yaml` is used to defined which plugins are run at certain levels, and what flags to use for those tools.

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

      objective_with_format:
        inherits_from: "objective"
        tool:
          clang-format:
            flags: ""

      ultimate:
        inherits_from: "objective_with_format"
        tool:
          lizard:
            flags: ""

Levels are defined by a dictionary with the name of the level as the key underneath a root `levels` key.

Tools are listed under the `tool` key.
The name of the keys under `tool` key should match either a default Statick tool plugin or a user defined tool plugin.

The `inherits_from` key can be used to inherit tools and flags from a different level.
Flags from the inherited level can be overridden by listing the same tool under the level's `tools` key with a new set
of flags.

#### profile.yaml

`profile.yaml` defines what levels to run for packages.
The levels listed in the profile must exist in the `config.yaml`.
Multiple profiles can exist, and you can specify which one to use with the `--profile` argument.
For example, you can have a `profile_objective.yaml` with stricter levels to run for packages.
Pass this profile to Statick.

    default: threshold

    packages:
      my_package: objective

      my_really_good_package: ultimate

The `default` key lists the level to be run if there is no specific level listed for a package.

The `packages` key lists packages and override levels to run for those packages.

#### exceptions.yaml

`exceptions.yaml` is used to ignore false positive warnings or warnings that will not be corrected.

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

There are two types of exceptions.

`file` exceptions ignore all warnings generated by a pattern of files.
The `tools` key can either be `all` to suppress warnings from all tools or a list of specific tools.
The `globs` key is a list of globs of files to ignore.
The glob could also be a specific filename.
For an exception to be applied to a specific issue, it is required that the issue contain an absolute path to the filename.
The path for the issue is set in the tool plugin that generates the issues.

`message_regex` exceptions ignore warnings based on a regular expression match against an error message.
The `tools` key can either be `all` to suppress warnings from all tools or a list of specific tools.
The `regex` key is a regular expression to match against messages.
Information about the regex syntax used by Python can be found [here](https://docs.python.org/2/library/re.html).

Exceptions can either be global or package specific.
To make them global, place them under a key named `global` at the root of the yaml file.
To make them package spefific, place them in a key named after the package under a key named `packages` at the root
level of the yaml.

The `ignore_packages` key is a list of package names that should be skipped when running `static_ws`.

## Plugins

Plugins allow you to implement file discovery, use tools, or output in formats/to locations that aren't provided
builtin with Statick.

Plugins consist of both a Python file and a `yapsy` file.
For a description of how yapsy works, check out the [documentation](http://yapsy.sourceforge.net/).

A user path with some custom plugins may look like

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
Those plugins are both setup in such a way that they work when released on PyPI.

## Tests

Statick supports testing through the [tox](https://tox.readthedocs.io/en/latest) framework.
Tox is used to run tests against multiple versions of python and supports running other tools, such as flake8, as part
of the testing process.
To run tox, run the following commands from a git checkout of `statick`:

    `pip install tox`
    `tox`

This will run the test suites in Python virtual environments for each Python version.
If your system does not have one of the Python versions listed in `tox.ini`, that version will be skipped.

If running `tox` locally does not work, one thing to try is to remove the auto-generated output directories such as
`output-py27`, `output-py35`, and `.tox`.
There is an included `clean.sh` shell script that helps with removing auto-generated files.

### Tests and Contributing

If you write a new feature for Statick or are fixing a bug, you are strongly encouraged to add unit tests for your contribution.
In particular, it is much easier to test whether a bug is fixed (and identify future regressions) if you can add a small
unit test which replicates the bug.

For tool plugins that are not available via pip it is recommended to skip tests that fail when the tool is not installed.

Before submitting a change, please run tox to check that you have not introduced any regressions or violated any code
style guidelines.

### Mypy

Statick uses [mypy](http://mypy-lang.org/) to check that type hints are being followed properly.
Type hints are described in [PEP 484](https://www.python.org/dev/peps/pep-0484/) and allow for static typing in Python.
To determine if proper types are being used in Statick the following command will show any errors, and create several
types of reports that can be viewed with a text editor or web browser.

    pip install mypy
    mkdir report
    mypy --ignore-missing-imports --html-report report/ --txt-report report statick statick_tool/

It is hoped that in the future we will generate coverage reports from mypy and use those to check for regressions.

### Formatting

Statick code is formatted using [black](https://github.com/psf/black).
To fix locally use

    pip install black
    black statick statick_ws statick_tool tests

## Examples

A few examples are provided for some of the basic use cases of Statick.
See [examples/README.md](./examples/README.md) for more details.

## Statick Jenkins Integration

The preferred method is to install the `Warnings Next Generation Plug-In`
(<https://wiki.jenkins.io/display/JENKINS/Warnings+Next+Generation+Plugin>)
and use the provided [pipeline template](./templates/Jenkinsfile).

### Deprecated Method

The output of Statick can also be integrated with the Jenkins Warnings plug-in.
NOTE: This plugin has reached end-of-life and will be removed in the future.

  1. In Jenkins:
     Install `Warnings Plug-In` (<https://wiki.jenkins-ci.org/display/JENKINS/Warnings+Plugin>)

  1. Under `Jenkins > Manage Jenkins > Configure System`:

     Click `Add` under the `Compiler Warnings` section
     Fill in the following fields:

         Name:
           Statick
         Link name:
           Statick
         Trend report name:
           Statick
         Regular Expression:
           ^\s*\[(.*)\]\[(\d+)\]\[(.*):(.*)\]\[(.*)\]\[(\d+)\]$
         Mapping Script:
           import hudson.plugins.warnings.parser.Warning
           import hudson.plugins.analysis.util.model.Priority;
           String fileName = matcher.group(1)
           String lineNumber = matcher.group(2)
           String type = matcher.group(3)
           String category = matcher.group(4)
           String message = matcher.group(5)
           int level = Integer.parseInt(matcher.group(6))
           Priority priority = Priority.LOW;
           if(level >= 3) { priority = Priority.NORMAL; }
           if(level >= 5) { priority = Priority.HIGH; }
           return new Warning(fileName, Integer.parseInt(lineNumber), type, type + ":" + category, message, priority);
         Example Log Message:
           [/home/user/src/workspace/src/example_pkg/src/tools/converter.cpp][8][cppcheck:warning/uninitVar]
           [Member variable 'Tools::init_' is not initialized in the constructor.][1]

  1. Click save.

  1. Go to the job configuration.

  1. Add a build script:

     catkin_make
     source devel/setup.bash
     mkdir -p statick_output
     statick <path of package> statick_output

  1. Add post-build action `Scan for compiler warnings`

     Add a `Scan workspace files`

     Set file pattern to: `statick_output/*.statick`

     Set `Parser` type as `Statick`
