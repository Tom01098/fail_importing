"""Import utilities for unittest.
"""
import importlib
from functools import wraps
from typing import Tuple, Optional
from unittest.mock import patch

# TODO I've tried to patch over _gcd_import with little success - is there a better way than this?
_real_dunder_import = __import__
_real_import_module = importlib.import_module


def _raise_if_should_fail(path: str, paths: Tuple[str]) -> None:
    if path in paths:
        raise ImportError()


class _DunderImportMock:

    def __init__(self, paths: Tuple[str]):
        self.paths = paths

    def __call__(self, name, globals=None, locals=None, fromlist=(), level=0):
        if fromlist is None:
            full_import_path = name
        else:
            full_import_path = f"{name}.{'.'.join(fromlist)}"
        _raise_if_should_fail(full_import_path, self.paths)
        return _real_dunder_import(name, globals, locals, fromlist, level)


class _ImportlibMock:

    def __init__(self, paths: Tuple[str]):
        self.paths = paths

    def __call__(self, name: str, package: Optional[str] = None):
        _raise_if_should_fail(name, self.paths)
        return _real_import_module(name, package)


def fail_importing(*paths: str):
    """Patch Python's import mechanism to fail with an ImportError for the
    given paths. The paths must match exactly.
    """

    def decorator(func):
        @wraps(func)
        def inner(*args, **kwargs):
            nonlocal paths

            # Account for nested patching.
            if isinstance(__import__, _DunderImportMock):
                paths += __import__.paths

            with (
                patch('builtins.__import__', _DunderImportMock(paths)),
                patch('importlib.import_module', _ImportlibMock(paths))
            ):
                return func(*args, **kwargs)

        return inner

    return decorator
