"""Import utilities for unittest.
"""

from unittest.mock import patch

_real_import = __import__


def fail_importing(*paths: str):
    """Patch Python's import mechanism to fail with an ImportError for the
    given paths. The paths must match exactly.
    """

    class FailImportingMock:

        def __call__(self, name, globals=None, locals=None, fromlist=(), level=0):
            full_import_path = f"{name}.{'.'.join(fromlist)}"
            if full_import_path in paths:
                raise ImportError()
            return _real_import(name, globals, locals, fromlist, level)

    def decorator(func):
        return patch('builtins.__import__', FailImportingMock())(func)

    return decorator
