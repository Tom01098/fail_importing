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

    # Basic imports.
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

    def test_method(self):
        class SomeClass:

            @fail_importing("modules")
            def some_method(self):
                import modules

        with self.assertRaises(ImportError):
            SomeClass().some_method()

    @fail_importing("modules.example")
    def test_importlib(self):
        with self.assertRaises(ImportError):
            importlib.import_module("modules.example")

    @fail_importing("modules.example")
    def test_relative(self):
        with self.assertRaises(ImportError):
            import modules.inner.inner

    # Interactions with other decorators.
    @patch("typing.List")
    @fail_importing("modules.example")
    @patch("typing.Dict")
    def test_with_patches(self, dict_mock, list_mock):
        self.assertIsInstance(dict_mock, MagicMock)
        self.assertIsInstance(list_mock, MagicMock)
        with self.assertRaises(ImportError):
            import modules.example

    # More complex control flow.
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

    @fail_importing("modules.example")
    def test_indirect(self):
        with self.assertRaises(ImportError):
            import modules.redirect

    # Regexes.
    @fail_importing(".*.other")
    def test_regex(self):
        import modules.example
        with self.assertRaises(ImportError):
            import modules.other

    # Generators.
    def test_generator(self):
        @fail_importing("modules.example")
        def generator():
            yield
            import modules.example

        with self.assertRaises(ImportError):
            list(generator())

    def test_generator_called_from_decorated_function_after_creation(self):
        def generator(a):
            yield a
            import modules.other

        gen = iter(generator(1))
        self.assertEqual(1, next(gen))

        @fail_importing("modules.other")
        def inner():
            with self.assertRaises(ImportError):
                next(gen)

        inner()

    # Errors.
    def test_non_function_raises(self):
        with self.assertRaises(RuntimeError):
            @fail_importing()
            class MyClass:
                pass
            assert MyClass
