"""Code analysis front-end."""

from __future__ import print_function
import copy
import os
import logging

from yapsy.PluginManager import PluginManager
from statick_tool import __version__
from statick_tool.package import Package
from statick_tool.discovery_plugin import DiscoveryPlugin
from statick_tool.tool_plugin import ToolPlugin
from statick_tool.report import generate_report
from statick_tool.exceptions import Exceptions
from statick_tool.config import Config
from statick_tool.profile import Profile
from statick_tool.resources import Resources
from statick_tool.plugin_context import PluginContext

logging.basicConfig()


class Statick(object):
    """Code analysis front-end."""

    def __init__(self, user_paths):
        """Initialize Statick."""
        self.resources = Resources(user_paths)

        self.manager = PluginManager()
        self.manager.setPluginPlaces(self.resources.get_plugin_paths())
        self.manager.setCategoriesFilter({
            "Discovery": DiscoveryPlugin,
            "Tool": ToolPlugin
        })
        self.manager.collectPlugins()

        self.discovery_plugins = {}
        for plugin_info in self.manager.getPluginsOfCategory("Discovery"):
            self.discovery_plugins[plugin_info.plugin_object.get_name()] = \
                    plugin_info.plugin_object

        self.tool_plugins = {}
        for plugin_info in self.manager.getPluginsOfCategory("Tool"):
            self.tool_plugins[plugin_info.plugin_object.get_name()] = \
                    plugin_info.plugin_object

        self.config = Config(self.resources.get_file("config.yaml"))

        self.exceptions = Exceptions(self.resources.get_file("exceptions.yaml"))

    def get_ignore_packages(self):
        """Get packages to ignore during scan process."""
        return self.exceptions.get_ignore_packages()

    def gather_args(self, args):
        """Gather arguments."""
        args.add_argument("output_directory", help="Output directory")
        args.add_argument("--show-tool-output", dest="show_tool_output",
                          action="store_true", help="Show tool output")
        args.add_argument("--profile", dest="profile",
                          type=str, help="Name of profile yaml file")
        args.add_argument("--force-tool-list", dest="force_tool_list",
                          type=str, help="Force only the given list of tools to run")
        args.add_argument('--version', action='version',
                          version='%(prog)s {version}'.format(version=__version__))

        for _, plugin in self.discovery_plugins.iteritems():
            plugin.gather_args(args)

        for _, plugin in self.tool_plugins.iteritems():
            plugin.gather_args(args)

    def get_level(self, path, args):
        """Get level to scan package at."""
        path = os.path.abspath(path)

        profile_filename = "profile.yaml"
        if args.profile is not None:
            profile_filename = args.profile
        try:
            profile = Profile(self.resources.get_file(profile_filename))
        except TypeError:
            print("Could not find profile file {}!".format(profile_filename))
            return None

        package = Package(os.path.basename(path), path)
        level = profile.get_package_level(package)

        return level

    def run(self, path, args):  # pylint: disable=too-many-locals, too-many-return-statements, too-many-branches, too-many-statements
        """Run scan tools against targets on path."""
        success = True

        path = os.path.abspath(path)
        if not os.path.exists(path):
            print("No package found at {}!".format(path))
            return None

        package = Package(os.path.basename(path), path)
        level = self.get_level(path, args)

        if not self.config.has_level(level):
            print("Can't find specified level {} in config!".format(level))
            return None, False

        orig_path = os.getcwd()

        if not os.path.isdir(args.output_directory):
            print("Output directory not found at {}!".
                  format(args.output_directory))
            return None, False

        output_dir = os.path.join(args.output_directory,
                                  package.name + "-" + level)

        if not os.path.isdir(output_dir):
            os.mkdir(output_dir)
        if not os.path.isdir(output_dir):
            print("Unable to create output directory at {}!".format(
                output_dir))
            return None, False
        print("Writing output to: {}".format(output_dir))

        os.chdir(output_dir)

        print("------")
        print("Scanning package {} ({}) at level {}".format(package.name,
                                                            package.path,
                                                            level))

        issues = {}

        ignore_packages = self.get_ignore_packages()
        if package.name in ignore_packages:
            print("Package {} is configured to be ignored by Statick.".format(package.name))
            return issues, True

        plugin_context = PluginContext(args, self.resources, self.config)

        print("---Discovery---")
        discovery_plugins = self.config.get_enabled_discovery_plugins(level)
        if len(discovery_plugins) == 0:
            discovery_plugins = self.discovery_plugins.keys()
        for plugin_name in discovery_plugins:
            if plugin_name not in self.discovery_plugins.keys():
                print("Can't find specified discovery plugin {}!".format(plugin_name))
                return None, False

            plugin = self.discovery_plugins[plugin_name]
            plugin.set_plugin_context(plugin_context)
            print("Running {} discovery plugin...".format(plugin.get_name()))
            plugin.scan(package, level)
            print("{} discovery plugin done.".format(plugin.get_name()))
        print("---Discovery---")

        print("---Tools---")
        enabled_plugins = self.config.get_enabled_tool_plugins(level)
        plugins_to_run = copy.copy(enabled_plugins)
        plugins_ran = []
        plugin_dependencies = []
        while len(plugins_to_run) > 0:
            plugin_name = plugins_to_run[0]

            if plugin_name not in self.tool_plugins.keys():
                if plugin_name == "pep257":
                    plugin_name = "pydocstyle"
                    plugins_to_run.remove("pep257")
                    plugins_to_run.insert(0, plugin_name)
                    print("DEPRECATION WARNING: The pep257 tool has been renamed "
                          "as the pydocstyle tool. Please update your configuration.")
                elif plugin_name == "pep8":
                    plugin_name = "pycodestyle"
                    plugins_to_run.remove("pep8")
                    plugins_to_run.insert(0, plugin_name)
                    print("DEPRECATION WARNING: The pep8 tool has been renamed "
                          "as the pycodestyle tool. Please update your configuration.")
                else:
                    print("Can't find specified tool plugin {}!".format(plugin_name))
                    return None, False

            if args.force_tool_list is not None:
                force_tool_list = args.force_tool_list.split(",")
                if plugin_name not in force_tool_list and plugin_name not in plugin_dependencies:
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
                        print("Plugin {} depends on plugin {} which isn't "
                              "enabled!".format(plugin_name, dependency_name))
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

        issues = self.exceptions.filter_issues(package, issues)

        os.chdir(orig_path)

        output_file = os.path.join(args.output_directory,
                                   package.name + "-" + level + ".statick")
        generate_report(issues, output_file)
        print("Done!")

        return issues, success
