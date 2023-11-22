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

import logging
from typing import Any, Dict, List
from xml.etree import ElementTree


class ClangFormatXMLParser:
    """Parse XML output from the clang-format tool."""

    def parse_xml_output(self, output: str, filename: str) -> List[Dict[Any, Any]]:
        """Parse XML output from the clang-format tool."""
        report: List[Dict[Any, Any]] = []
        xmls = output.split("<?xml version='1.0'?>")[1:]
        for xml in xmls:
            try:
                root = ElementTree.fromstring(xml)
            except ElementTree.ParseError as exc:
                logging.error("Invalid XML in clang format output: %s", str(exc))
                return report

            replacements = root.findall("replacement")

            with open(filename, "r", encoding="utf8") as fid:
                content = fid.read()

            return self.generate_report(content, replacements)

        return report

    def generate_report(  # pylint: disable=too-many-locals
        self, content: str, replacements: List[ElementTree.Element]
    ) -> List[Dict[Any, Any]]:
        """Go through content and generate report of issues discovered."""
        report: List[Dict[Any, Any]] = []
        for replacement in replacements:
            offset = int(replacement.get("offset", 0))
            length = int(replacement.get("length", 0))
            replace_text = replacement.text or ""
            data: Dict[Any, Any] = {
                "line_no": 0,
                "deletion": "",
                "addition": "",
            }
            # to-be-replaced snippet
            original = content[offset : offset + length]
            # map global offset to line number and offset in line
            index_of_line_start = self.find_index_of_line_start(content, offset)
            index_of_line_end = self.find_index_of_line_end(content, offset + length)
            data["line_no"] = self.get_line_number(content, index_of_line_start)
            offset_in_line = offset - index_of_line_start

            # generate diff like changes
            subcontent = content[index_of_line_start:index_of_line_end]
            data["deletion"] = subcontent
            data["addition"] = (
                subcontent[0:offset_in_line]
                + replace_text
                + subcontent[offset_in_line + length :]
            )

            # make common control characters visible
            mapping = {"\n": "\\n", "\r": "\\r", "\t": "\\t"}
            for old, new in mapping.items():
                replace_text = replace_text.replace(old, new)
                original = original.replace(old, new)

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
    def find_index_of_line_start(cls, data: str, offset: int) -> int:
        """Find where line starts."""
        index_1 = data.rfind("\n", 0, offset) + 1
        index_2 = data.rfind("\r", 0, offset) + 1
        return max(index_1, index_2)

    @classmethod
    def find_index_of_line_end(cls, data: str, offset: int) -> int:
        """Find where line ends."""
        index_1 = data.find("\n", offset)
        if index_1 == -1:
            index_1 = len(data)
        index_2 = data.find("\r", offset)
        if index_2 == -1:
            index_2 = len(data)
        return min(index_1, index_2)

    @classmethod
    def get_line_number(cls, data: str, offset: int) -> int:
        """Get line number where violation occurs."""
        return data[0:offset].count("\n") + data[0:offset].count("\r") + 1
