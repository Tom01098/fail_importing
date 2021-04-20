import importlib
import sys
from copy import copy
from unittest import TestCase, skip
from unittest.mock import patch, MagicMock

from patch_import import fail_importing


class FailImportingTestCase(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.original_modules = copy(sys.modules)

    def tearDown(self):
        sys.modules = self.original_modules

    @fail_importing("modules")
    def test_single_match(self):
        with self.assertRaises(ImportError):
            from modules import example
            assert example

    @fail_importing("modules.other")
    def test_single_no_match(self):
        from modules import example
        assert example

    @fail_importing("modules")
    def test_import_only(self):
        with self.assertRaises(ImportError):
            import modules
            assert modules

    @fail_importing("modules.example", "modules.other")
    def test_multiple_match(self):
        with self.assertRaises(ImportError):
            from modules import example
            assert example

    @fail_importing("modules.other", "modules.something")
    def test_multiple_no_match(self):
        from modules import example
        assert example

    @patch("typing.List")
    @fail_importing("modules.example")
    @patch("typing.Dict")
    def test_with_patches(self, dict_mock, list_mock):
        self.assertIsInstance(dict_mock, MagicMock)
        self.assertIsInstance(list_mock, MagicMock)
        with self.assertRaises(ImportError):
            import modules.example

    @fail_importing("modules.example")
    def inner_func(self):
        with self.assertRaises(ImportError):
            import modules.example

        with self.assertRaises(ImportError):
            import modules.other

    @fail_importing("modules.other")
    def test_nested_patching(self):
        self.inner_func()

        with self.assertRaises(ImportError):
            import modules.other

        import modules.example

    class SomeClass:

        @fail_importing("modules")
        def some_method(self):
            import modules

    def test_method(self):
        with self.assertRaises(ImportError):
            self.SomeClass().some_method()

    @fail_importing("modules.example")
    def test_importlib(self):
        with self.assertRaises(ImportError):
            importlib.import_module("modules.example")

    @fail_importing(".*.other")
    def test_regex(self):
        import modules.example
        with self.assertRaises(ImportError):
            import modules.other

    @fail_importing("modules.example")
    def test_indirect(self):
        with self.assertRaises(ImportError):
            import modules.redirect

    @fail_importing("modules.example")
    def generator(self):
        yield 0
        import modules.example

    def test_generator(self):
        with self.assertRaises(ImportError):
            list(self.generator())

    def test_non_function_raises(self):
        with self.assertRaises(RuntimeError):
            @fail_importing()
            class MyClass:
                pass
            assert MyClass
