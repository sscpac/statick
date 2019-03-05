"""Discovery plugin to find CMake-based projects."""

from __future__ import print_function

import os
import re
import shutil
import subprocess

from statick_tool.discovery_plugin import DiscoveryPlugin


class CMakeDiscoveryPlugin(DiscoveryPlugin):
    """Discovery plugin to find CMake-based projects."""

    def get_name(self):
        """Get name of discovery type."""
        return "cmake"

    def scan(self, package, level, exceptions=None):
        """Scan package looking for CMake files."""
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
        shutil.copyfile(cmake_template, "CMakeLists.txt")

        extra_gcc_flags = self.plugin_context.config.get_tool_config("make", level, "flags", "")

        subproc_args = ["cmake", ".", "-DCMAKE_BUILD_TYPE=RelWithDebInfo",
                        "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON",
                        "-DINPUT_DIR=" + package.path,
                        "-DSTATICK_EXTRA_GCC_FLAGS=" + extra_gcc_flags]

        try:
            output = subprocess.check_output(subproc_args,
                                             stderr=subprocess.STDOUT,
                                             universal_newlines=True)
            if self.plugin_context.args.show_tool_output:
                print("{}".format(output))
        except subprocess.CalledProcessError as ex:
            output = ex.output
            print("Problem running CMake! Returncode = {}".
                  format(str(ex.returncode)))
            print("{}".format(ex.output))

        except OSError:
            print("Couldn't find cmake executable!")
            return

        with open("cmake.log", "w") as fname:
            fname.write(output)

        self.process_output(output, package)

        print("  {} make targets found.".format(len(package["make_targets"])))

    @classmethod
    def process_output(cls, output, package):  # pylint: disable=too-many-locals
        """Parse the tool output."""
# pylint: disable=anomalous-backslash-in-string
        cmake_target_re = r"-- TARGET: \[NAME:(.+)\]\[SRC_DIR:(.+)\]\[INCLUDE_DIRS:(.+)\]\[SRC:(.+)\]"  # NOQA: W605 # NOLINT
        target_p = re.compile(cmake_target_re)
        cmake_headers_re = r"-- HEADERS: (.+)"
        headers_p = re.compile(cmake_headers_re)
        cmake_roslint_re = r"-- ROSLINT: (.+)"
        roslint_p = re.compile(cmake_roslint_re)
        cmake_project_re = r"-- PROJECT: \[NAME:(.+)\]\[SRC_DIR:(.+)\]\[BIN_DIR:(.+)\]"  # NOQA: W605 # NOLINT
        project_p = re.compile(cmake_project_re)
# pylint: enable=anomalous-backslash-in-string

        qt_re = r".*build/.*(ui_|moc_|).*\.(h|cxx)"
        qt_p = re.compile(qt_re)

        for line in output.splitlines():
            match = target_p.match(line)
            if match:
                name = match.group(1)
                src_dir = match.group(2)
                include_dirs = match.group(3).split(";")
                src = [src for src in match.group(4).split(";")
                       if not qt_p.match(src)]
                src = [src if os.path.isabs(src)  # noqa F812
                       else os.path.join(src_dir, src) for src in src]  # NOLINT  # noqa F812

                target = {"name": name, "src_dir": src_dir,
                          "include_dirs": include_dirs, "src": src}
                package["make_targets"].append(target)

            match = headers_p.match(line)
            if match:
                headers = match.group(1).split(";")
                headers = [header for header in headers
                           if not qt_p.match(header)]
                package["headers"] += headers

            match = roslint_p.match(line)
            if match:
                roslint = os.path.normpath(match.group(1))
                cpplint = os.path.join(roslint, "cpplint")
                if os.path.isfile(cpplint):
                    print("  cpplint script from roslint found at {}".
                          format(cpplint))
                    package["cpplint"] = cpplint

            match = project_p.match(line)
            if match:
                package["src_dir"] = match.group(2)
                package["bin_dir"] = match.group(3)
