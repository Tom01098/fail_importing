import builtins
import importlib
import inspect
import re
from functools import wraps
from types import ModuleType
from typing import Tuple, Optional, Any, Generator
from unittest.mock import patch

# Ensure that the pure Python import implementation is used so we can patch it.
# Comes with a small performance hit but hey, these are unit tests.
builtins.__import__ = importlib.__import__

# _gcd_import is the shared implementation between importlib.__import__ and importlib.get_module.
_unpatched_import = importlib._bootstrap._gcd_import


class _ImportMock:

    def __init__(self, patterns: Tuple[str]) -> None:
        self.patterns = patterns

    def __call__(self, name: str, package: Optional[str] = None, level: int = 0) -> ModuleType:
        # Resolve relative paths to absolute ones.
        if level > 0:
            module_path = importlib._bootstrap._resolve_name(name, package, level)
        else:
            module_path = name

        # Raise if the path matches any of the patterns.
        for pattern in self.patterns:
            if re.fullmatch(pattern, module_path):
                raise ImportError

        # Import using the normal import mechanism.
        # It's safe to use level 0 because we've already resolved the module path
        # (this is exactly what the implementation of _gcd_import does!).
        return _unpatched_import(module_path, None, 0)


def _patch_import(patterns: Tuple[str]):
    # Account for nested patching.
    possibly_patched_import = importlib._bootstrap._gcd_import

    if isinstance(possibly_patched_import, _ImportMock):
        patterns += possibly_patched_import.patterns

    return patch('importlib._bootstrap._gcd_import', _ImportMock(patterns))


# Generators are a little more involved. The generator function needs to be mocked over with an iterable, and the
# iterator can be called multiple times. We care about patching over each call to the iterator, which is what we do in
# __next__.
# TODO Can introspectability be preserved here? _GeneratorMock isn't the 'expected' result of calling a generator,
#  but these are tests and no one should care... right?
class _GeneratorMock:

    def __init__(self, gen: Generator, patterns: Tuple[str]) -> None:
        self.gen = gen
        self.patterns = patterns

    def __iter__(self) -> '_GeneratorMock':
        return self

    def __next__(self) -> Any:
        with _patch_import(self.patterns):
            return next(self.gen)


def fail_importing(*patterns: str):
    """Patch Python's import mechanism to fail with an ImportError for the
    given paths.
    """

    def decorator(func):
        if not inspect.isfunction(func):
            raise RuntimeError(f"Can't decorate {func.__name__} with {fail_importing.__name__} as it is not a function")

        @wraps(func)
        def inner(*args, **kwargs):
            if inspect.isgeneratorfunction(func):
                return _GeneratorMock(func(*args, **kwargs), patterns)
            else:
                with _patch_import(patterns):
                    return func(*args, **kwargs)

        return inner

    return decorator
