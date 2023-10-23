try:
    import json
except ImportError:
    from django.utils import simplejson as json  # NOQA

# Need to create an unused import to generate a ruff error.
import os

# Line too long does not trigger going from ruff v0.0.278 to v0.1.1.
some_long_variable = "make this string go past the allowed length of 88 characters by adding ridiculous redundancy"
