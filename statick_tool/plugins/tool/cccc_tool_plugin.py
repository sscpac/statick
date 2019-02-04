r"""
Apply CCCC tool and gather results.

To run the CCCC tool locally (without Statick) one way to do so is:

    find . -name \*.h -print -o -name \*.cpp -print | xargs cccc

That will generate several reports, including HTML. The results can be viewd
in a web browser.
"""

from __future__ import print_function

import csv
import subprocess

import xmltodict

from statick_tool.issue import Issue
from statick_tool.tool_plugin import ToolPlugin


class CCCCToolPlugin(ToolPlugin):
    """Apply CCCC tool and gather results."""

    def get_name(self):
        """Get name of tool."""
        return "cccc"

    def scan(self, package, level):
        """Run tool and gather output."""
        output = None

        if "c_src" not in package.keys():
            return []

        config_file = self.plugin_context.resources.get_file("cccc.opt")
        if config_file is not None:
            opts = "--opt_infile=" + config_file

        for src in package["c_src"]:
            try:
                subproc_args = ["cccc"] + [opts] + [src]
                output = subprocess.check_output(subproc_args,
                                                 stderr=subprocess.STDOUT)
            except subprocess.CalledProcessError as ex:
                if ex.returncode == 1:
                    output = ex.output
                else:
                    print("Problem {}".format(ex.returncode))
                    print("{}".format(ex.output))
                    return None

            except OSError as ex:
                print("Couldn't find cccc executable! (%s)" % (ex))
                return None

            if self.plugin_context.args.show_tool_output:
                print("{}".format(output))

        with open(self.get_name() + ".log", "w") as f:
            f.write(output)

        issues = self.parse_output(package, config_file)
        return issues

    def parse_output(self, package, config_file):
        """Parse tool output and report issues."""
        with open('.cccc/cccc.xml') as f:
            doc = xmltodict.parse(f.read())

        config = self.parse_config(config_file)

        results = {}
        for module in doc['CCCC_Project']['structural_summary']['module']:
            results[module['name']] = {}
            metrics = {}
            for field in module:
                if '@value' in  module[field]:  # noqa: E271
                    metrics[field] = {"value": module[field]['@value']}
            results[module['name']] = metrics

        for module in doc['CCCC_Project']['procedural_summary']['module']:
            metrics = results[module['name']]
            for field in module:
                if '@value' in  module[field]:  # noqa: E271
                    metrics[field] = {"value": module[field]['@value']}
            results[module['name']] = metrics

        for module in doc['CCCC_Project']['oo_design']['module']:
            metrics = results[module['name']]
            for field in module:
                if '@value' in  module[field]:  # noqa: E271
                    metrics[field] = {"value": module[field]['@value']}
            results[module['name']] = metrics

        issues = self.find_issues(config, results, package)

        return issues

    @classmethod
    def parse_config(cls, config_file):
        """
        Parse CCCC configuration file.

        Gets warning and error thresholds for all the metrics.
        An explanation to dump default values to a configuration file is at:
        http://sarnold.github.io/cccc/CCCC_User_Guide.html#config

        `cccc --opt_outfile=cccc.opt`
        """
        config = {}

        if config_file is None:
            return config

        with open(config_file, "r") as csvfile:
            reader = csv.DictReader(csvfile, delimiter="@")
            for row in reader:
                if row['CCCC_FileExt'] == 'CCCC_MetTmnt':
                    config[row[".ADA"]] = {"warn": row['ada.95'],
                                           "error": row[''],
                                           "name": row[None][3],
                                           "key": row[".ADA"]}

        return config

    def find_issues(self, config, results, package):
        """Identify issues by comparing tool results with tool configuration."""
        issues = []

        for key, val in results.items():
            for item in val.keys():
                val_id = self.convert_name_to_id(item)
                if val_id != '' and val_id in config.keys():
                    if val[item]["value"] == '------':
                        continue
                    result = float(val[item]["value"])
                    thresh_error = float(config[val_id]["error"])
                    thresh_warn = float(config[val_id]["warn"])
                    msg = key + ' - ' + config[val_id]['name']
                    if result > thresh_error:
                        msg += ' - value: {}, theshold: {}'.format(result,
                                                                   thresh_error)
                        issues.append(Issue(package['c_src'][0], 0,
                                            self.get_name(), 'error', 5,
                                            msg, None))
                    elif result > thresh_warn:
                        msg += ' - value: {}, theshold: {}'.format(result,
                                                                   thresh_warn)
                        issues.append(Issue(package['c_src'][0], 0,
                                            self.get_name(), 'warn', 3,
                                            msg, None))

        return issues

    @classmethod
    def convert_name_to_id(cls, name):  # pylint: disable=too-many-branches
        """
        Convert result name to configuration name.

        The name given in CCCC results is different than the name given in CCCC
        configuration. This will map the name in the configuration file to the
        name given in the results.
        """
        name_id = ''

        if name == 'IF4':
            name_id = "IF4"
        elif name == 'fan_out_concrete':
            name_id = "FOc"
        elif name == 'IF4_visible':
            name_id = "IF4v"
        elif name == 'coupling_between_objects':
            name_id = "CBO"
        elif name == 'fan_in_visible':
            name_id = "FIv"
        elif name == 'weighted_methods_per_class_unity':
            name_id = "WMC1"
        elif name == 'fan_out':
            name_id = "FO"
        elif name == 'weighted_methods_per_class_visibility':
            name_id = "WMCv"
        elif name == 'fan_out_visible':
            name_id = "FOv"
        elif name == 'IF4_concrete':
            name_id = "IF4c"
        elif name == 'depth_of_inheritance_tree':
            name_id = "DIT"
        elif name == 'number_of_children':
            name_id = "NOC"
        elif name == 'fan_in_concrete':
            name_id = "FIc"
        elif name == 'fan_in':
            name_id = "FI"
        elif name == 'lines_of_comment':
            name_id = "COM"
        elif name == 'lines_of_code_per_line_of_comment':
            name_id = "L_C"
        elif name == 'McCabes_cyclomatic_complexity':
            name_id = "MVGper"
        elif name == 'lines_of_code':
            name_id = "LOCp"
        elif name == 'McCabes_cyclomatic_complexity_per_line_of_comment':
            name_id = "M_C"

        return name_id
