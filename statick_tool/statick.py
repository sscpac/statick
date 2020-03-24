"""Code analysis front-end."""
import argparse
import copy
import logging
import os
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

        self.discovery_plugins = {}  # type: Dict
        for plugin_info in self.manager.getPluginsOfCategory("Discovery"):
            self.discovery_plugins[
                plugin_info.plugin_object.get_name()
            ] = plugin_info.plugin_object

        self.tool_plugins = {}  # type: Dict
        for plugin_info in self.manager.getPluginsOfCategory("Tool"):
            self.tool_plugins[
                plugin_info.plugin_object.get_name()
            ] = plugin_info.plugin_object

        self.reporting_plugins = {}  # type: Dict
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
        self.config = Config(self.resources.get_file(config_filename))

    def get_exceptions(self, args: argparse.Namespace) -> None:
        """Get Statick exceptions."""
        exceptions_filename = "exceptions.yaml"
        if args.exceptions is not None:
            exceptions_filename = args.exceptions
        self.exceptions = Exceptions(self.resources.get_file(exceptions_filename))

    def get_ignore_packages(self) -> List[str]:
        """Get packages to ignore during scan process."""
        assert self.exceptions
        return self.exceptions.get_ignore_packages()

    def gather_args(self, args: argparse.Namespace) -> None:
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
    ) -> Tuple[Optional[Dict], bool]:
        """Run scan tools against targets on path."""
        success = True

        path = os.path.abspath(path)
        if not os.path.exists(path):
            print("No package found at {}!".format(path))
            return None, False

        package = Package(os.path.basename(path), path)
        level = self.get_level(path, args)  # type: Optional[str]

        assert level
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
                os.mkdir(output_dir)
            if not os.path.isdir(output_dir):
                print("Unable to create output directory at {}!".format(output_dir))
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
        for plugin_name in discovery_plugins:
            if plugin_name not in self.discovery_plugins:
                print("Can't find specified discovery plugin {}!".format(plugin_name))
                return None, False

            plugin = self.discovery_plugins[plugin_name]
            plugin.set_plugin_context(plugin_context)
            print("Running {} discovery plugin...".format(plugin.get_name()))
            plugin.scan(package, level, self.exceptions)
            print("{} discovery plugin done.".format(plugin.get_name()))
        print("---Discovery---")

        print("---Tools---")
        enabled_plugins = self.config.get_enabled_tool_plugins(level)
        plugins_to_run = copy.copy(enabled_plugins)
        plugins_ran = []  # type: List[Any]
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
