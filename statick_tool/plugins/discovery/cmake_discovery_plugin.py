"""Discovery plugin to find CMake-based projects."""
import os
import re
import shutil
import subprocess
from typing import List, Match, Optional, Pattern

from statick_tool.discovery_plugin import DiscoveryPlugin
from statick_tool.exceptions import Exceptions
from statick_tool.package import Package


class CMakeDiscoveryPlugin(DiscoveryPlugin):
    """Discovery plugin to find CMake-based projects."""

    def get_name(self) -> str:
        """Get name of discovery type."""
        return "cmake"

    def scan(self, package: Package, level: str, exceptions: Exceptions = None) -> None:
        """Scan package looking for CMake files."""
        if self.plugin_context is None:
            return

        cmake_file = os.path.join(package.path, "CMakeLists.txt")

        package["cmake"] = True
        package["make_targets"] = []
        package["headers"] = []

        if not os.path.isfile(cmake_file):
            print("  Package is not cmake.")
            package["cmake"] = False
            return

        print("  Found cmake package {}".format(cmake_file))

        cmake_template = self.plugin_context.resources.get_file("CMakeLists.txt.in")
        shutil.copyfile(cmake_template, "CMakeLists.txt")  # type: ignore

        extra_gcc_flags = self.plugin_context.config.get_tool_config(
            "make", level, "flags", ""
        )  # type: str

        subproc_args = [
            "cmake",
            ".",
            "-DCMAKE_BUILD_TYPE=RelWithDebInfo",
            "-DBUILD_GTEST=OFF",
            "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON",
            "-DCATKIN_ENABLE_TESTING=OFF",
            "-DCATKIN_SKIP_TESTING=ON",
            "-DINPUT_DIR=" + package.path,
            "-DSTATICK_EXTRA_GCC_FLAGS=" + extra_gcc_flags,
        ]  # type: List[str]

        try:
            output = subprocess.check_output(
                subproc_args, stderr=subprocess.STDOUT, universal_newlines=True
            )  # type: str
            if self.plugin_context.args.show_tool_output:
                print("{}".format(output))
        except subprocess.CalledProcessError as ex:
            output = ex.output
            print("Problem running CMake! Returncode = {}".format(str(ex.returncode)))
            print("{}".format(ex.output))

        except OSError:
            print("Couldn't find cmake executable!")
            return

        if self.plugin_context.args.output_directory:
            with open("cmake.log", "w") as fname:
                fname.write(output)

        self.process_output(output, package)

        print("  {} make targets found.".format(len(package["make_targets"])))

    @classmethod
    def process_output(  # pylint: disable=too-many-locals
        cls, output: str, package: Package
    ) -> None:
        """Parse the tool output."""
        # pylint: disable=anomalous-backslash-in-string
        cmake_target_re = r"-- TARGET: \[NAME:(.+)\]\[SRC_DIR:(.+)\]\[INCLUDE_DIRS:(.+)\]\[SRC:(.+)\]"  # NOQA: W605 # NOLINT
        target_p = re.compile(cmake_target_re)  # type: Pattern[str]
        cmake_headers_re = r"-- HEADERS: (.+)"
        headers_p = re.compile(cmake_headers_re)  # type: Pattern[str]
        cmake_roslint_re = r"-- ROSLINT: (.+)"
        roslint_p = re.compile(cmake_roslint_re)  # type: Pattern[str]
        cmake_project_re = r"-- PROJECT: \[NAME:(.+)\]\[SRC_DIR:(.+)\]\[BIN_DIR:(.+)\]"  # NOQA: W605 # NOLINT
        project_p = re.compile(cmake_project_re)  # type: Pattern[str]
        # pylint: enable=anomalous-backslash-in-string

        qt_re = r".*build/.*(ui_|moc_|).*\.(h|cxx)"
        qt_p = re.compile(qt_re)  # type: Pattern[str]

        for line in output.splitlines():
            match_target = target_p.match(line)  # type: Optional[Match[str]]
            if match_target:
                name = match_target.group(1)
                src_dir = match_target.group(2)
                include_dirs = match_target.group(3).split(";")
                src = [
                    src
                    for src in match_target.group(4).split(";")
                    if not qt_p.match(src)
                ]
                src = [
                    src
                    if os.path.isabs(src)  # noqa F812
                    else os.path.join(src_dir, src)
                    for src in src
                ]  # NOLINT  # noqa F812

                target = {
                    "name": name,
                    "src_dir": src_dir,
                    "include_dirs": include_dirs,
                    "src": src,
                }
                package["make_targets"].append(target)

            match_headers = headers_p.match(line)  # type: Optional[Match[str]]
            if match_headers:
                headers = match_headers.group(1).split(";")
                headers = [header for header in headers if not qt_p.match(header)]
                package["headers"] += headers

            match_lint = roslint_p.match(line)  # type: Optional[Match[str]]
            if match_lint:
                roslint = os.path.normpath(match_lint.group(1))
                cpplint = os.path.join(roslint, "cpplint")
                if os.path.isfile(cpplint):
                    print("  cpplint script from roslint found at {}".format(cpplint))
                    package["cpplint"] = cpplint

            match_project = project_p.match(line)  # type: Optional[Match[str]]
            if match_project:
                package["src_dir"] = match_project.group(2)
                package["bin_dir"] = match_project.group(3)
