"""Code analysis front-end."""
import argparse
import copy
import io
import logging
import multiprocessing
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

from yapsy.PluginManager import PluginManager

from statick_tool import __version__
from statick_tool.config import Config
from statick_tool.discovery_plugin import DiscoveryPlugin
from statick_tool.exceptions import Exceptions
from statick_tool.issue import Issue
from statick_tool.package import Package
from statick_tool.plugin_context import PluginContext
from statick_tool.profile import Profile
from statick_tool.reporting_plugin import ReportingPlugin
from statick_tool.resources import Resources
from statick_tool.tool_plugin import ToolPlugin

logging.basicConfig()


class Statick:
    """Code analysis front-end."""

    def __init__(self, user_paths: List[str]) -> None:
        """Initialize Statick."""
        self.resources = Resources(user_paths)

        self.manager = PluginManager()
        self.manager.setPluginPlaces(self.resources.get_plugin_paths())
        self.manager.setCategoriesFilter(
            {
                "Discovery": DiscoveryPlugin,
                "Tool": ToolPlugin,
                "Reporting": ReportingPlugin,
            }
        )
        self.manager.collectPlugins()

        self.discovery_plugins = {}  # type: Dict[str, Any]
        for plugin_info in self.manager.getPluginsOfCategory("Discovery"):
            self.discovery_plugins[
                plugin_info.plugin_object.get_name()
            ] = plugin_info.plugin_object

        self.tool_plugins = {}  # type: Dict[str, Any]
        for plugin_info in self.manager.getPluginsOfCategory("Tool"):
            self.tool_plugins[
                plugin_info.plugin_object.get_name()
            ] = plugin_info.plugin_object

        self.reporting_plugins = {}  # type: Dict[str, Any]
        for plugin_info in self.manager.getPluginsOfCategory("Reporting"):
            self.reporting_plugins[
                plugin_info.plugin_object.get_name()
            ] = plugin_info.plugin_object

        self.config = None  # type: Optional[Config]
        self.exceptions = None  # type: Optional[Exceptions]

    def get_config(self, args: argparse.Namespace) -> None:
        """Get Statick configuration."""
        config_filename = "config.yaml"
        if args.config is not None:
            config_filename = args.config
        try:
            self.config = Config(self.resources.get_file(config_filename))
        except OSError as ex:
            print("Failed to access config file {}: {}".format(config_filename, ex))
        except ValueError as ex:
            print("Config file {} has errors: {}".format(config_filename, ex))

    def get_exceptions(self, args: argparse.Namespace) -> None:
        """Get Statick exceptions."""
        exceptions_filename = "exceptions.yaml"
        if args.exceptions is not None:
            exceptions_filename = args.exceptions
        try:
            self.exceptions = Exceptions(self.resources.get_file(exceptions_filename))
        except OSError as ex:
            print(
                "Failed to access exceptions file {}: {}".format(
                    exceptions_filename, ex
                )
            )
        except ValueError as ex:
            print("Exceptions file {} has errors: {}".format(exceptions_filename, ex))

    def get_ignore_packages(self) -> List[str]:
        """Get packages to ignore during scan process."""
        if self.exceptions is None:
            return []
        return self.exceptions.get_ignore_packages()

    def gather_args(self, args: argparse.ArgumentParser) -> None:
        """Gather arguments."""
        args.add_argument(
            "--output-directory",
            dest="output_directory",
            type=str,
            help="Directory to write output files to",
        )
        args.add_argument(
            "--show-tool-output",
            dest="show_tool_output",
            action="store_true",
            help="Show tool output",
        )
        args.add_argument(
            "--check",
            dest="check",
            action="store_true",
            help="Return the status. Return code 0 means there were no issues. \
                  Return code 1 means there were issues.",
        )
        args.add_argument(
            "--config", dest="config", type=str, help="Name of config yaml file"
        )
        args.add_argument(
            "--profile", dest="profile", type=str, help="Name of profile yaml file"
        )
        args.add_argument(
            "--exceptions",
            dest="exceptions",
            type=str,
            help="Name of exceptions yaml file",
        )
        args.add_argument(
            "--force-tool-list",
            dest="force_tool_list",
            type=str,
            help="Force only the given list of tools to run",
        )
        args.add_argument(
            "--version",
            action="version",
            version="%(prog)s {version}".format(version=__version__),
        )
        args.add_argument(
            "--mapping-file-suffix",
            dest="mapping_file_suffix",
            type=str,
            help="Suffix to use when searching for CERT mapping files",
        )

        # statick workspace arguments
        args.add_argument(
            "-ws",
            dest="workspace",
            action="store_true",
            help="Treat the path argument as a workspace of multiple packages",
        )
        args.add_argument(
            "--max-procs",
            dest="max_procs",
            type=int,
            default=int(multiprocessing.cpu_count() / 2),
            help="Maximum number of CPU cores to use, only used when running on a workspace",
        )
        args.add_argument(
            "--packages-file",
            dest="packages_file",
            type=str,
            help="File listing packages to scan, only used when running on a workspace",
        )
        args.add_argument(
            "--list-packages",
            dest="list_packages",
            action="store_true",
            help="List packages and levels, only used when running on a workspace",
        )

        for _, plugin in list(self.discovery_plugins.items()):
            plugin.gather_args(args)

        for _, plugin in list(self.tool_plugins.items()):
            plugin.gather_args(args)

        for _, plugin in list(self.reporting_plugins.items()):
            plugin.gather_args(args)

    def get_level(self, path: str, args: argparse.Namespace) -> Optional[str]:
        """Get level to scan package at."""
        path = os.path.abspath(path)

        profile_filename = "profile.yaml"
        if args.profile is not None:
            profile_filename = args.profile
        profile_resource = self.resources.get_file(profile_filename)
        if profile_resource is None:
            print("Could not find profile file {}!".format(profile_filename))
            return None
        try:
            profile = Profile(profile_resource)
        except OSError as ex:
            # This isn't quite redundant with the profile_resource check: it's possible
            # that something else triggers an OSError, like permissions.
            print("Failed to access profile file {}: {}".format(profile_filename, ex))
            return None
        except ValueError as ex:
            print("Profile file {} has errors: {}".format(profile_filename, ex))
            return None

        package = Package(os.path.basename(path), path)
        level = profile.get_package_level(package)

        return level

    def run(  # pylint: disable=too-many-locals, too-many-return-statements, too-many-branches, too-many-statements
        self, path: str, args: argparse.Namespace
    ) -> Tuple[Optional[Dict[str, List[Issue]]], bool]:
        """Run scan tools against targets on path."""
        success = True

        path = os.path.abspath(path)
        if not os.path.exists(path):
            print("No package found at {}!".format(path))
            return None, False

        package = Package(os.path.basename(path), path)
        level = self.get_level(path, args)  # type: Optional[str]
        print("level: {}".format(level))
        if level is None:
            print("Level is not valid.")
            return None, False

        if not self.config or not self.config.has_level(level):
            print("Can't find specified level {} in config!".format(level))
            return None, False

        orig_path = os.getcwd()
        if args.output_directory:
            if not os.path.isdir(args.output_directory):
                print("Output directory not found at {}!".format(args.output_directory))
                return None, False

            output_dir = os.path.join(args.output_directory, package.name + "-" + level)

            if not os.path.isdir(output_dir):
                try:
                    os.mkdir(output_dir)
                except OSError as ex:
                    print(
                        "Unable to create output directory at {}: {}".format(
                            output_dir, ex
                        )
                    )
                    return None, False
            print("Writing output to: {}".format(output_dir))

            os.chdir(output_dir)

        print("------")
        print(
            "Scanning package {} ({}) at level {}".format(
                package.name, package.path, level
            )
        )

        issues = {}  # type: Dict[str, List[Issue]]

        ignore_packages = self.get_ignore_packages()
        if package.name in ignore_packages:
            print(
                "Package {} is configured to be ignored by Statick.".format(
                    package.name
                )
            )
            return issues, True

        plugin_context = PluginContext(args, self.resources, self.config)

        print("---Discovery---")
        if not DiscoveryPlugin.file_command_exists():
            print(
                "file command isn't available, discovery plugins will be less effective"
            )

        discovery_plugins = self.config.get_enabled_discovery_plugins(level)
        if not discovery_plugins:
            discovery_plugins = list(self.discovery_plugins.keys())
        plugins_ran = []  # type: List[Any]
        for plugin_name in discovery_plugins:
            if plugin_name not in self.discovery_plugins:
                print("Can't find specified discovery plugin {}!".format(plugin_name))
                return None, False

            plugin = self.discovery_plugins[plugin_name]
            dependencies = plugin.get_discovery_dependencies()
            for dependency_name in dependencies:
                dependency_plugin = self.discovery_plugins[dependency_name]
                if dependency_plugin.get_name() in plugins_ran:
                    continue
                dependency_plugin.set_plugin_context(plugin_context)
                print(
                    "Running {} discovery plugin...".format(
                        dependency_plugin.get_name()
                    )
                )
                dependency_plugin.scan(package, level, self.exceptions)
                print("{} discovery plugin done.".format(dependency_plugin.get_name()))
                plugins_ran.append(dependency_plugin.get_name())

            if plugin.get_name() not in plugins_ran:
                plugin.set_plugin_context(plugin_context)
                print("Running {} discovery plugin...".format(plugin.get_name()))
                plugin.scan(package, level, self.exceptions)
                print("{} discovery plugin done.".format(plugin.get_name()))
                plugins_ran.append(plugin.get_name())
        print("---Discovery---")

        print("---Tools---")
        enabled_plugins = self.config.get_enabled_tool_plugins(level)
        plugins_to_run = copy.copy(enabled_plugins)
        plugins_ran = []
        plugin_dependencies = []  # type: List[str]
        while plugins_to_run:
            plugin_name = plugins_to_run[0]

            if plugin_name not in self.tool_plugins:
                print("Can't find specified tool plugin {}!".format(plugin_name))
                return None, False

            if args.force_tool_list is not None:
                force_tool_list = args.force_tool_list.split(",")
                if (
                    plugin_name not in force_tool_list
                    and plugin_name not in plugin_dependencies
                ):
                    print("Skipping plugin not in force list {}!".format(plugin_name))
                    plugins_to_run.remove(plugin_name)
                    continue

            plugin = self.tool_plugins[plugin_name]
            plugin.set_plugin_context(plugin_context)

            dependencies = plugin.get_tool_dependencies()
            dependencies_met = True
            for dependency_name in dependencies:
                if dependency_name not in plugins_ran:
                    if dependency_name not in enabled_plugins:
                        print(
                            "Plugin {} depends on plugin {} which isn't "
                            "enabled!".format(plugin_name, dependency_name)
                        )
                        return None, False
                    plugin_dependencies.append(dependency_name)
                    if dependency_name in plugins_to_run:
                        plugins_to_run.remove(dependency_name)
                    plugins_to_run.insert(0, dependency_name)
                    dependencies_met = False

            if not dependencies_met:
                continue

            print("Running {} tool plugin...".format(plugin.get_name()))
            tool_issues = plugin.scan(package, level)
            if tool_issues is not None:
                issues[plugin_name] = tool_issues
                print("{} tool plugin done.".format(plugin.get_name()))
            else:
                print("{} tool plugin failed".format(plugin.get_name()))
                success = False

            plugins_to_run.remove(plugin_name)
            plugins_ran.append(plugin_name)
        print("---Tools---")

        if self.exceptions is not None:
            issues = self.exceptions.filter_issues(package, issues)

        os.chdir(orig_path)

        print("---Reporting---")
        reporting_plugins = self.config.get_enabled_reporting_plugins(level)
        if not reporting_plugins:
            reporting_plugins = self.reporting_plugins.keys()  # type: ignore
        for plugin_name in reporting_plugins:
            if plugin_name not in self.reporting_plugins.keys():
                print("Can't find specified reporting plugin {}!".format(plugin_name))
                return None, False

            plugin = self.reporting_plugins[plugin_name]
            plugin.set_plugin_context(plugin_context)
            print("Running {} reporting plugin...".format(plugin.get_name()))
            plugin.report(package, issues, level)
            print("{} reporting plugin done.".format(plugin.get_name()))
        print("---Reporting---")
        print("Done!")

        return issues, success

    # , args: argparse.Namespace

    def run_workspace(
        self, parsed_args: argparse.Namespace
    ) -> Tuple[
        Optional[Dict[str, List[Issue]]], bool
    ]:  # pylint: disable=too-many-locals, too-many-branches, too-many-statements
        """Run statick on a workspace.

        --max-procs can be set to the desired number of CPUs to use for processing a workspace.
        This defaults to half the available CPUs.
        Setting this to -1 will cause statick.run_workspace to use all available CPUs.
        """
        max_cpus = multiprocessing.cpu_count()
        if parsed_args.max_procs > max_cpus or parsed_args.max_procs == -1:
            parsed_args.max_procs = max_cpus
        elif parsed_args.max_procs <= 0:
            parsed_args.max_procs = 1

        if parsed_args.output_directory:
            out_dir = parsed_args.output_directory
            if not os.path.isdir(out_dir):
                print("Output directory not found at " + out_dir + "!")
                return None, False

        ignore_packages = self.get_ignore_packages()
        ignore_files = ["AMENT_IGNORE", "CATKIN_IGNORE", "COLCON_IGNORE"]

        packages = []
        for root, dirs, files in os.walk(parsed_args.path):
            if any(item in files for item in ignore_files):
                dirs.clear()
                continue
            for sub_dir in dirs:
                full_dir = os.path.join(root, sub_dir)
                files = os.listdir(full_dir)
                if "package.xml" in files and not any(
                    item in files for item in ignore_files
                ):
                    if ignore_packages and sub_dir in ignore_packages:
                        continue
                    packages.append((sub_dir, full_dir))

        if parsed_args.packages_file is not None:
            packages_file_list = []
            try:
                packages_file = os.path.abspath(parsed_args.packages_file)
                with open(packages_file, "r") as fname:
                    packages_file_list = [
                        package.strip()
                        for package in fname.readlines()
                        if package.strip() and package[0] != "#"
                    ]
            except OSError:
                print("Packages file not found")
                return None, False
            packages = [
                package for package in packages if package[0] in packages_file_list
            ]

        if parsed_args.list_packages:
            for package in packages:
                print(
                    "{:40}: {}".format(
                        package[0], self.get_level(package[1], parsed_args)
                    )
                )
            return None, True

        count = 0
        total_issues = []
        num_packages = len(packages)
        mp_args = []
        if multiprocessing.get_start_method() == "fork":
            print("-- Scanning {} packages --".format(num_packages), flush=True)
            for package in packages:
                count += 1
                mp_args.append((parsed_args, count, package, num_packages))

            with multiprocessing.Pool(parsed_args.max_procs) as pool:
                total_issues = pool.starmap(self.scan_package, mp_args)
        else:
            print(
                "Statick's plugin manager does not currently support multiprocessing without"
                " UNIX's fork function. Falling back to a single process."
            )
            print("-- Scanning {} packages --".format(num_packages), flush=True)
            for package in packages:
                count += 1
                pkg_issues = self.scan_package(
                    parsed_args, count, package, num_packages
                )
                total_issues.append(pkg_issues)

        print("-- All packages run --")
        print("-- overall report --")

        success = True
        issues = {}  # type: Dict[str, List[Issue]]
        for issue in total_issues:
            if issue is not None:
                for key, value in list(issue.items()):
                    if key in issues:
                        issues[key] += value
                        if value:
                            success = False
                    else:
                        issues[key] = value
                        if value:
                            success = False

        enabled_reporting_plugins = []  # type: List[str]
        available_reporting_plugins = {}
        for plugin_info in self.manager.getPluginsOfCategory("Reporting"):
            available_reporting_plugins[
                plugin_info.plugin_object.get_name()
            ] = plugin_info.plugin_object

        # Make a fake 'all' package for reporting
        dummy_all_package = Package("all_packages", parsed_args.path)
        level = self.get_level(dummy_all_package.path, parsed_args)
        if level is not None and self.config is not None:
            if not self.config or not self.config.has_level(level):
                print("Can't find specified level {} in config!".format(level))
                enabled_reporting_plugins = list(available_reporting_plugins)
            else:
                enabled_reporting_plugins = self.config.get_enabled_reporting_plugins(
                    level
                )

        if not enabled_reporting_plugins:
            enabled_reporting_plugins = list(available_reporting_plugins)

        # Make a dummy plugincontext as well
        plugin_context = PluginContext(parsed_args, None, None)  # type: ignore
        plugin_context.args.output_directory = parsed_args.output_directory

        for plugin_name in enabled_reporting_plugins:
            if plugin_name not in available_reporting_plugins:
                print("Can't find specified reporting plugin {}!".format(plugin_name))
                continue
            plugin = self.reporting_plugins[plugin_name]
            plugin.set_plugin_context(plugin_context)
            print("Running {} reporting plugin...".format(plugin.get_name()))
            plugin.report(dummy_all_package, issues, level)
            print("{} reporting plugin done.".format(plugin.get_name()))

        return issues, success

    def scan_package(
        self,
        parsed_args: argparse.Namespace,
        count: int,
        package: Package,
        num_packages: int,
    ) -> Optional[Dict[str, List[Issue]]]:
        """Scan each package in a separate process while buffering output."""
        sio = io.StringIO()
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = sio
        sys.stderr = sio
        print(
            "-- Scanning package "
            + package[0]
            + " ("
            + str(count)
            + " of "
            + str(num_packages)
            + ") --"
        )
        issues, dummy = self.run(package[1], parsed_args)
        if issues is not None:
            print(
                "-- Done scanning package "
                + package[0]
                + " ("
                + str(count)
                + " of "
                + str(num_packages)
                + ") --"
            )
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            print(sio.getvalue(), flush=True)
        else:
            print("Failed to run statick on package " + package[0] + "!")
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            print(sio.getvalue(), flush=True)
        return issues
