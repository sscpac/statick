"""Apply CCCC tool and gather results."""

from __future__ import print_function
import subprocess
import csv
from os.path import expanduser
import xmltodict

from statick_tool.tool_plugin import ToolPlugin
from statick_tool.issue import Issue


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

        config_file = expanduser("~") + "/.cccc_config"
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

    def parse_output(self, package, config_file):  # pylint: disable=too-many-branches, too-many-statements
        """Parse tool output and report issues."""
        with open('.cccc/cccc.xml') as f:
            doc = xmltodict.parse(f.read())

        thresh = self.parse_config(config_file)
        print("cbo warning: {}".format(thresh["CBO"]["warn"]))

        issues = []

        for module in doc['CCCC_Project']['procedural_summary']['module']:  # pylint: disable=too-many-nested-blocks
            for key, value in module.items():
                # if key == 'name':
                #     name = value
                if key == 'lines_of_code':
                    for k, val in value.items():
                        threshold = 500
                        if k == '@value' and int(val) > threshold:
                            issue = self.add_issue(key, package, int(val),
                                                   threshold)
                            if issue not in issues:
                                issues.append(issue)
                if key == 'McCabes_cyclomatic_complexity':
                    for k, val in value.items():
                        threshold = 200
                        if k == '@value' and int(val) > threshold:
                            issue = self.add_issue(key, package, int(val),
                                                   threshold)
                            if issue not in issues:
                                issues.append(issue)
                if key == 'lines_of_comment':
                    for k, val in value.items():
                        threshold = 10000
                        if k == '@value' and int(val) > threshold:
                            issue = self.add_issue(key, package, int(val),
                                                   threshold)
                            if issue not in issues:
                                issues.append(issue)
                if key == 'lines_of_code_per_line_of_comment':
                    for k, val in value.items():
                        threshold = 7
                        if k == '@value' and val != '------' and \
                                int(val) > threshold:
                            issue = self.add_issue(key, package, int(val),
                                                   threshold)
                            if issue not in issues:
                                issues.append(issue)
                if key == 'McCabes_cyclomatic_complexity_per_line_of_comment':
                    for k, val in value.items():
                        threshold = 5
                        if k == '@value' and val != '------' and \
                                int(val) > threshold:
                            issue = self.add_issue(key, package, int(val),
                                                   threshold)
                            if issue not in issues:
                                issues.append(issue)

        for module in doc['CCCC_Project']['oo_design']['module']:  # pylint: disable=too-many-nested-blocks
            for key, value in module.items():
                # if key == 'name':
                #     name = value
                if key == 'coupling_between_objects':
                    for k, val in value.items():
                        threshold = 14
                        if k == '@value' and int(val) > threshold:
                            issue = self.add_issue(key, package, int(val),
                                                   threshold)
                            if issue not in issues:
                                issues.append(issue)
                if key == 'depth_of_inheritance_tree':
                    for k, val in value.items():
                        threshold = 5
                        if k == '@value' and int(val) > threshold:
                            issue = self.add_issue(key, package, int(val),
                                                   threshold)
                            if issue not in issues:
                                issues.append(issue)
                if key == 'number_of_children':
                    for k, val in value.items():
                        threshold = 20
                        if k == '@value' and int(val) > threshold:
                            issue = self.add_issue(key, package, int(val),
                                                   threshold)
                            if issue not in issues:
                                issues.append(issue)
                if key == 'weighted_methods_per_class_unity':
                    for k, val in value.items():
                        threshold = 30
                        if k == '@value' and int(val) > threshold:
                            issue = self.add_issue(key, package, int(val),
                                                   threshold)
                            if issue not in issues:
                                issues.append(issue)
                if key == 'weighted_methods_per_class_visibility':
                    for k, val in value.items():
                        threshold = 10
                        if k == '@value' and int(val) > threshold:
                            issue = self.add_issue(key, package, int(val),
                                                   threshold)
                            if issue not in issues:
                                issues.append(issue)

        for module in doc['CCCC_Project']['structural_summary']['module']:  # pylint: disable=too-many-nested-blocks
            for key, value in module.items():
                # if key == 'name':
                #     name = value
                if key == 'fan_out_visible':
                    for k, val in value.items():
                        threshold = 6
                        if k == '@value' and int(val) > threshold:
                            issue = self.add_issue(key, package, int(val),
                                                   threshold)
                            if issue not in issues:
                                issues.append(issue)
                if key == 'fan_out_concrete':
                    for k, val in value.items():
                        threshold = 6
                        if k == '@value' and int(val) > threshold:
                            issue = self.add_issue(key, package, int(val),
                                                   threshold)
                            if issue not in issues:
                                issues.append(issue)
                if key == 'fan_out':
                    for k, val in value.items():
                        threshold = 12
                        if k == '@value' and int(val) > threshold:
                            issue = self.add_issue(key, package, int(val),
                                                   threshold)
                            if issue not in issues:
                                issues.append(issue)
                if key == 'fan_in_visible':
                    for k, val in value.items():
                        threshold = 6
                        if k == '@value' and int(val) > threshold:
                            issue = self.add_issue(key, package, int(val),
                                                   threshold)
                            if issue not in issues:
                                issues.append(issue)
                if key == 'fan_in_concrete':
                    for k, val in value.items():
                        threshold = 6
                        if k == '@value' and int(val) > threshold:
                            issue = self.add_issue(key, package, int(val),
                                                   threshold)
                            if issue not in issues:
                                issues.append(issue)
                if key == 'fan_in':
                    for k, val in value.items():
                        threshold = 12
                        if k == '@value' and int(val) > threshold:
                            issue = self.add_issue(key, package, int(val),
                                                   threshold)
                            if issue not in issues:
                                issues.append(issue)
                if key == 'IF4_visible':
                    for k, val in value.items():
                        threshold = 30
                        if k == '@value' and int(val) > threshold:
                            issue = self.add_issue(key, package, int(val),
                                                   threshold)
                            if issue not in issues:
                                issues.append(issue)
                if key == 'IF4_concrete':
                    for k, val in value.items():
                        threshold = 30
                        if k == '@value' and int(val) > threshold:
                            issue = self.add_issue(key, package, int(val),
                                                   threshold)
                            if issue not in issues:
                                issues.append(issue)
                if key == 'IF4':
                    for k, val in value.items():
                        threshold = 100
                        if k == '@value' and int(val) > threshold:
                            issue = self.add_issue(key, package, int(val),
                                                   threshold)
                            if issue not in issues:
                                issues.append(issue)

        return issues

    def add_issue(self, issue_type, package, num, thresh):
        """Add issue to list of issues returned by tool."""
        message = 'Amount ({}) exceeds threshold ({})'.format(num, thresh)
        return Issue(package["c_src"][0], 0, self.get_name(), issue_type,
                     "5", message, None)

    @classmethod
    def parse_config(cls, config_file):
        """
        Parse CCCC configuration file.

        Gets warning and error thresholds for all the metrics.
        Default values are from version 3.pre57.
        """
        thresh = {}
        thresh["CBO"] = {"warn": 12.0, "error": 30.0}
        thresh["COM"] = {"warn": 999999.0, "error": 9999999.0}
        thresh["COMper"] = {"warn": 999999.0, "error": 9999999.0}
        thresh["DIT"] = {"warn": 3.0, "error": 6.0}
        thresh["FI"] = {"warn": 12.0, "error": 20.0}
        thresh["FIc"] = {"warn": 6.0, "error": 12.0}
        thresh["FIv"] = {"warn": 6.0, "error": 12.0}
        thresh["FO"] = {"warn": 12.0, "error": 20.0}
        thresh["FOc"] = {"warn": 6.0, "error": 12.0}
        thresh["FOv"] = {"warn": 6.0, "error": 12.0}
        thresh["IF4"] = {"warn": 100.0, "error": 1000.0}
        thresh["IF4c"] = {"warn": 30.0, "error": 100.0}
        thresh["IF4v"] = {"warn": 30.0, "error": 100.0}
        thresh["LOCf"] = {"warn": 30.0, "error": 100.0}
        thresh["LOCm"] = {"warn": 500.0, "error": 2000.0}
        thresh["LOCp"] = {"warn": 999999.0, "error": 9999999.0}
        thresh["LOCper"] = {"warn": 500.0, "error": 2000.0}
        thresh["L_C"] = {"warn": 7.0, "error": 30.0}
        thresh["MVGf"] = {"warn": 10.0, "error": 30.0}
        thresh["MVGm"] = {"warn": 200.0, "error": 1000.0}
        thresh["MVGp"] = {"warn": 999999.0, "error": 9999999.0}
        thresh["MVGper"] = {"warn": 200.0, "error": 1000.0}
        thresh["M_C"] = {"warn": 5.0, "error": 10.0}
        thresh["NOC"] = {"warn": 4.0, "error": 15.0}
        thresh["WMC1"] = {"warn": 30.0, "error": 100.0}
        thresh["WMCv"] = {"warn": 10.0, "error": 30.0}

        print("configuration file: {}".format(config_file))
        if config_file is None:
            return thresh

        with open(config_file, "r") as csvfile:
            csvreader = csv.DictReader(csvfile, delimiter="@")
            for line in csvreader:
                print("{}".format(line))
                if line["CCCC_FileExt"] is "CCCC_MetTmnt":
                    # print 'found line with {}'.format(thresh[line["ada.95"]])
                    thresh[line[".ADA"]["warn"]] = thresh[line["ada.95"]]
                    print 'thresh = ', thresh[line["ada.95"]]

        print("cbo warning: {}".format(thresh["CBO"]["warn"]))
        return thresh
