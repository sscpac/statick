try:
    import json
except ImportError:
    from django.utils import simplejson as json  # NOQA

some_long_variable = "make this string go past the allowed length of 88 characters by adding ridiculous redundancy"
