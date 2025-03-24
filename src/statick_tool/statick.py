#!/usr/bin/env python3
"""Executable script for running Statick against one or more packages."""

import argparse
import sys
import time

from tabulate import tabulate

from statick_tool.args import Args
from statick_tool.statick_tool import Statick


def run(
    statick: Statick, parsed_args: argparse.Namespace, start_time: float
) -> bool:  # pragma: no cover
    """Run Statick on a single package.

    Args:
        statick: Statick object.
        parsed_args: Arguments from the command line.
        start_time: Start time of the scan.

    Returns:
        True if the scan was successful, False otherwise.
    """
    path = parsed_args.path
    issues, success = statick.run(path, parsed_args, start_time)
    if issues is None:
        statick.print_no_issues()
        return False
    for tool in issues:
        if issues[tool]:
            success = False
    return success


def main() -> None:  # pragma: no cover
    """Run Statick."""
    start_time: float = time.time()
    args = Args("Statick tool")
    args.parser.add_argument("path", help="Path of package or workspace to scan")

    statick = Statick(args.get_user_paths())
    statick.gather_args(args.parser)
    parsed_args = args.get_args()
    statick.set_logging_level(parsed_args)
    statick.get_config(parsed_args)
    statick.get_exceptions(parsed_args)

    if parsed_args.show_all_tool_versions:
        success = statick.collect_tool_versions(parsed_args)
    elif parsed_args.workspace:
        _, success = statick.run_workspace(parsed_args, start_time)
    else:
        success = run(statick, parsed_args, start_time)

    timings = statick.get_timings()
    if parsed_args.timings:
        print(tabulate(timings, headers="keys", tablefmt="pretty"))

    if parsed_args.show_all_tool_versions or parsed_args.show_run_tool_versions:
        tool_versions = statick.get_tool_versions()
        print(tabulate(tool_versions, headers="keys", tablefmt="grid"))

    if parsed_args.check and not success:
        statick.print_exit_status(False)
        sys.exit(1)
    else:
        statick.print_exit_status(True)
        sys.exit(0)


if __name__ == "__main__":  # pragma: no cover
    main()
