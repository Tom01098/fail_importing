"""Import utilities for unittest.
"""
import builtins
import importlib
import re
from functools import wraps
from typing import Tuple
from unittest.mock import patch

# Ensure that the pure Python import implementation is used so we can patch it.
# Comes with a small performance hit but hey, these are unit tests.
builtins.__import__ = importlib.__import__

# _gcd_import is the shared implementation between importlib.__import__ and importlib.get_module.
_unpatched_import = importlib._bootstrap._gcd_import


class _FailImportingMock:

    def __init__(self, paths: Tuple[str]):
        self.paths = paths

    def __call__(self, name, package=None, level=0):
        for path in self.paths:
            if re.fullmatch(path, name):
                raise ImportError()
        return _unpatched_import(name, package, level)


def fail_importing(*paths: str):
    """Patch Python's import mechanism to fail with an ImportError for the
    given paths.
    """

    def decorator(func):
        @wraps(func)
        def inner(*args, **kwargs):
            nonlocal paths

            # Account for nested patching.
            gcd = importlib._bootstrap._gcd_import

            if isinstance(gcd, _FailImportingMock):
                paths += gcd.paths

            with patch('importlib._bootstrap._gcd_import', _FailImportingMock(paths)):
                return func(*args, **kwargs)

        return inner

    return decorator
