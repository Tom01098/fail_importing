"""Import utilities for unittest.
"""
from functools import wraps
from typing import Tuple
from unittest.mock import patch

_real_import = __import__


class _FailImportingMock:

    def __init__(self, paths: Tuple[str]):
        self.paths = paths

    def __call__(self, name, globals=None, locals=None, fromlist=(), level=0):
        full_import_path = f"{name}.{'.'.join(fromlist)}"
        if full_import_path in self.paths:
            raise ImportError()
        return _real_import(name, globals, locals, fromlist, level)


def fail_importing(*paths: str):
    """Patch Python's import mechanism to fail with an ImportError for the
    given paths. The paths must match exactly.
    """

    def decorator(func):
        @wraps(func)
        def inner(*args, **kwargs):
            nonlocal paths

            # Account for nested patching.
            if isinstance(__import__, _FailImportingMock):
                paths += __import__.paths

            with patch('builtins.__import__', _FailImportingMock(paths)):
                return func(*args, **kwargs)

        return inner

    return decorator
