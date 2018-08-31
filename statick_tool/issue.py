"""Issue interface."""

from collections import namedtuple

Issue = namedtuple("Issue",
                   "filename line_number tool issue_type severity message "
                   "cert_reference")
