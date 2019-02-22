"""
Main file for statick gauntlet tool.

This is used to find dependency issues in catkin_workspaces.
This file is a huge mess right now since it's ported pretty directly
from the old version of the tool.
"""

from __future__ import print_function

import fnmatch
import os
import re
import subprocess
import sys

import yaml

from statick_tool.args import Args
from statick_tool.resources import Resources


def main():  # pylint: disable=too-many-locals, too-many-branches, too-many-statements
    """Run gauntlet tool."""
    args = Args("Statick gauntlet tool")
    args.parser.add_argument("src_path", help="Path of catkin src directory")
    args.parser.add_argument("out_path", help="Output path")
    args.parser.add_argument("--force-cmake", dest="force_cmake",
                             action="store_true", help="Force CMake")
    args.parser.add_argument("--failed-only", dest="failed_only",
                             action="store_true",
                             help="Only build targets from last failed run")
    args.parser.add_argument("--targets-file", dest="targets_file", type=str,
                             help="File listing targets to run")

    resources = Resources(args.get_user_paths())
    parsed_args = args.get_args()

    src_path = os.path.abspath(parsed_args.src_path)
    out_path = os.path.abspath(parsed_args.out_path)
    if not os.path.exists(src_path) or not os.path.isdir(src_path):
        print("Source path " + src_path + " not found!")
        sys.exit(1)
    if not os.path.exists(out_path) or not os.path.isdir(out_path):
        print("Output path " + out_path + " not found!")
        sys.exit(1)

    src_files = os.listdir(src_path)
    out_files = os.listdir(out_path)
    fail_file = os.path.join(out_path, "failed.txt")

    if "CMakeLists.txt" not in src_files:
        print("No CMakeLists.txt found in src directory. Is your catkin workspace initialized?")
        sys.exit(1)

    if "CMakeCache.txt" not in out_files or parsed_args.force_cmake:
        print("Running CMake...")
        try:
            subprocess.check_output(["cmake", src_path, "-B" + out_path])
        except subprocess.CalledProcessError as exc:
            print("CMake FAILED!")
            print(exc.output)
            print("CMake FAILED!")
            sys.exit(1)
        print("CMake complete")
    else:
        print("CMake cache found. Skipping CMake step.")

    raw_targets = []
    print("Gathering make targets...")
    if not parsed_args.failed_only:
        if parsed_args.targets_file is None:
            target_re = r"^([a-zA-Z0-9][^$#\/\t=]*):([^=]|$)"
            target_rec = re.compile(target_re)
            try:
                subprocess.check_output(["make", "-qp"], cwd=out_path)  # NOLINT
            except subprocess.CalledProcessError as exc:
                for line in exc.output.split("\n"):
                    match = target_rec.match(line)
                    if match:
                        target = match.group(1)
                        raw_targets.append(target)
        else:
            try:
                targets_file = os.path.abspath(parsed_args.targets_file)
                with open(targets_file, "r") as fname:
                    raw_targets = [target.strip() for target in fname.readlines()
                                   if target.strip() and target[0] != "#"]
            except IOError:
                print("Targets file not found")
                sys.exit(1)
    else:
        try:
            with open(fail_file, "r") as fname:
                raw_targets = [target.strip() for target in fname.readlines()
                               if target.strip() and target[0] != "#"]
        except IOError:
            print("Failed file from previous run not found. "
                  "Did you actually run the gauntlet once before?")
            sys.exit(1)
    print("Gathering make targets complete.")

    ignore_targets = []
    try:
        with open(resources.get_file("gauntlet_ignore.yaml")) as fname:
            ignore_targets = yaml.safe_load(fname)
    except IOError:
        print("Gauntlet ignore yaml file not found.")

    targets = []
    for raw_target in raw_targets:
        add = True
        for ignore_target in ignore_targets:
            if fnmatch.fnmatch(raw_target, ignore_target):
                add = False
                break
        if add:
            targets.append(raw_target)

    targets_file = os.path.join(out_path, "targets.txt")
    with open(targets_file, "w") as fname:
        for target in targets:
            fname.write(target + "\n")

    failed = []

    with open(fail_file, "w") as fname:
        i = 0
        print("BEGIN GAUNTLET")
        for target in targets:
            i += 1
            print("------------")
            print(" start " + target)
            print("", i, "of", len(targets))
            print("------------")

            print("@@clean@@")
            proc = subprocess.Popen(["make", "clean"], cwd=out_path)
            proc.wait()
            print("@@get rid of headers@@")
            proc = subprocess.Popen(["find", "devel", "-name", "*.h", "-type", "f", "-delete"],
                                    cwd=out_path)
            proc.wait()
            print("@@make@@")
            proc = subprocess.Popen(["make", target, "-j8"], cwd=out_path)
            proc.wait()
            result = proc.returncode
            if result != 0:
                print("*** FAILURE ***")
                print("  target", target)
                print("*** FAILURE ***")
                failed.append(target)
                fname.write(target + "\n")
                fname.flush()
            print("@@done@@")

            print("------------")
            print(" end " + target)
            print("", i, "of", len(targets))
            print("------------")
            if failed:
                print("*** FAILED *** ")
                for fail in failed:
                    print("  " + fail)
                print("*** FAILED *** ")
        print("END GAUNTLET")
        if failed:
            print("Build failures found")
            sys.exit(1)
        else:
            print("No errors")
            sys.exit(0)
