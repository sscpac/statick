#!/usr/bin/env python3
"""Parse XML output from the clang-format tool."""

# Copyright 2014-2016 Open Source Robotics Foundation, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Modifications made for use with Statick.
# Original code from ament_lint.
# https://github.com/ament/ament_lint/blob/master/ament_clang_format/ament_clang_format/main.py

from xml.etree import ElementTree


class ClangFormatXMLParser:
    """Parse XML output from the clang-format tool."""

    def parse_xml_output(self, output, filename):
        """Parse XML output from the clang-format tool."""
        report = []
        xmls = output.split("<?xml version='1.0'?>")[1:]
        for xml in xmls:
            try:
                root = ElementTree.fromstring(xml)
            except ElementTree.ParseError as exc:
                print("Invalid XML in clang format output: %s" % str(exc))
                return None

            replacements = root.findall("replacement")
            if not replacements:
                return report

            with open(filename, "r") as fid:
                content = fid.read()

            return self.generate_report(content, replacements)

    def generate_report(self, content, replacements):
        """Go through content and generate report of issues discovered."""
        report = []
        for replacement in replacements:
            data = {
                "offset": int(replacement.get("offset")),
                "length": int(replacement.get("length")),
                "replacement": replacement.text or "",
            }
            # to-be-replaced snippet
            data["original"] = content[
                data["offset"]: data["offset"] + data["length"]
            ]
            # map global offset to line number and offset in line
            index_of_line_start = self.find_index_of_line_start(
                content, data["offset"]
            )
            index_of_line_end = self.find_index_of_line_end(
                content, data["offset"] + data["length"]
            )
            data["line_no"] = self.get_line_number(content, index_of_line_start)
            data["offset_in_line"] = data["offset"] - index_of_line_start

            # generate diff like changes
            subcontent = content[index_of_line_start:index_of_line_end]
            data["deletion"] = subcontent
            data["addition"] = (
                subcontent[0: data["offset_in_line"]]
                + data["replacement"]
                + subcontent[data["offset_in_line"] + data["length"]:]
            )

            # make common control characters visible
            mapping = {"\n": "\\n", "\r": "\\r", "\t": "\\t"}
            for old, new in mapping.items():
                data["replacement"] = data["replacement"].replace(old, new)
                data["original"] = data["original"].replace(old, new)

            mapping = {"\r": "\n"}
            for old, new in mapping.items():
                data["deletion"] = data["deletion"].replace(old, new)
                data["addition"] = data["addition"].replace(old, new)

            # format deletion / addition as unified diff
            data["deletion"] = "\n".join(
                ["- " + line for line in data["deletion"].split("\n")]
            )
            data["addition"] = "\n".join(
                ["+ " + line for line in data["addition"].split("\n")]
            )

            report.append(data)

        return report

    @classmethod
    def find_index_of_line_start(cls, data, offset):
        """Find where line starts."""
        index_1 = data.rfind("\n", 0, offset) + 1
        index_2 = data.rfind("\r", 0, offset) + 1
        return max(index_1, index_2)

    @classmethod
    def find_index_of_line_end(cls, data, offset):
        """Find where line ends."""
        index_1 = data.find("\n", offset)
        if index_1 == -1:
            index_1 = len(data)
        index_2 = data.find("\r", offset)
        if index_2 == -1:
            index_2 = len(data)
        return min(index_1, index_2)

    @classmethod
    def get_line_number(cls, data, offset):
        """Get line number where violation occurs."""
        return data[0:offset].count("\n") + data[0:offset].count("\r") + 1
