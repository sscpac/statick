"""
Custom argument handling.

Enable usage of user-paths argument before parsing other arguments.
"""
from __future__ import print_function

import argparse
import os


class Args(object):
    """
    Custom argument handling.

    Enable usage of user-paths argument before parsing other arguments.
    """

    def __init__(self, name):
        """Initialize arguments."""
        self.pre_parser = argparse.ArgumentParser(description=name,
                                                  add_help=False)
        user_path_args = {"dest": "user_paths", "type": str,
                          "help": "Comma separated list of paths containing "
                                  "configuration or plugins"}
        self.pre_parser.add_argument("--user-paths", **user_path_args)

        self.parser = argparse.ArgumentParser(description=name)
        self.parser.add_argument("--user-paths", **user_path_args)

    def get_user_paths(self, args=None):
        """Get a list of user paths containing config or plugins."""
        user_paths = []
        args = self.pre_parser.parse_known_args(args)[0]
        if args.user_paths is not None:
            paths = args.user_paths.split(",")
            for path in paths:
                if os.path.exists(path) and os.path.isdir(path):
                    user_paths.append(path)
                else:
                    print("Could not find user path {}!".format(path))
        return user_paths

    def get_args(self, args=None):
        """Get parsed command-line arguments."""
        return self.parser.parse_args(args)
