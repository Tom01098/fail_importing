"""Import utilities for unittest.
"""
import builtins
import importlib
import inspect
import re
from functools import wraps
from typing import Tuple, Optional, Callable, Any, Generator
from types import ModuleType
from unittest.mock import patch

# Ensure that the pure Python import implementation is used so we can patch it.
# Comes with a small performance hit but hey, these are unit tests.
builtins.__import__ = importlib.__import__

# _gcd_import is the shared implementation between importlib.__import__ and importlib.get_module.
_unpatched_import = importlib._bootstrap._gcd_import


class _ImportMock:

    def __init__(self, paths: Tuple[str]) -> None:
        self.paths = paths

    def __call__(self, name: str, package: Optional[str] = None, level: int = 0) -> ModuleType:
        for path in self.paths:
            if re.fullmatch(path, name):
                raise ImportError()
        return _unpatched_import(name, package, level)


def _patch_import(paths: Tuple[str]):
    return patch('importlib._bootstrap._gcd_import', _ImportMock(paths))


# Generators are a little more involved. The generator function needs to be mocked over with an iterable, and the
# iterator can be called multiple times. We care about patching over each call to the iterator, which is what we do in
# __next__.
# TODO Can introspectability be preserved here? _GeneratorMock isn't the 'expected' result of calling a generator,
#  but these are tests and no one should care... right?
class _IteratorMock:

    def __init__(self, gen: Generator, paths: Tuple[str]) -> None:
        self.gen = gen
        self.paths = paths

    def __next__(self) -> Any:
        with _patch_import(self.paths):
            return next(self.gen)


class _GeneratorMock:

    def __init__(self, gen: Generator, paths: Tuple[str]) -> None:
        self.gen = gen
        self.paths = paths

    def __iter__(self) -> _IteratorMock:
        return _IteratorMock(self.gen, self.paths)


def fail_importing(*paths: str):
    """Patch Python's import mechanism to fail with an ImportError for the
    given paths.
    """

    def decorator(func):
        if not inspect.isfunction(func):
            raise RuntimeError(f"Can't decorate {func.__name__} with {fail_importing.__name__} as it is not a function")

        @wraps(func)
        def inner(*args, **kwargs):
            nonlocal paths

            # Account for nested patching.
            gcd = importlib._bootstrap._gcd_import

            if isinstance(gcd, _ImportMock):
                paths += gcd.paths

            # Do the patching!
            if inspect.isgeneratorfunction(func):
                return _GeneratorMock(func(*args, **kwargs), paths)
            else:
                with _patch_import(paths):
                    return func(*args, **kwargs)

        return inner

    return decorator
