"""Package interface."""

from typing import Dict


class Package(dict):  # type: ignore
    """Default implementation of package interface."""

    def __init__(  # pylint:disable=super-init-not-called
        self, name: str, path: str
    ) -> None:
        """Initialize package interface."""
        self.name = name
        self.path = path
        self.files: Dict[str, Dict[str, str]] = {}
        self._walked = False
