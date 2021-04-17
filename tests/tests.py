from unittest import TestCase
from unittest.mock import patch, MagicMock

from patch_import import fail_importing


class FailImportingTestCase(TestCase):

    @fail_importing("modules.example")
    def test_single_match(self):
        with self.assertRaises(ImportError):
            from modules import example
            assert example

    @fail_importing("modules.other")
    def test_single_no_match(self):
        from modules import example
        assert example

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
            from modules import example
            assert example

    @fail_importing("modules.example")
    def inner_func(self):
        with self.assertRaises(ImportError):
            from modules import example
            assert example

        with self.assertRaises(ImportError):
            from modules import other
            assert other

    @fail_importing("modules.other")
    def test_nested_patching(self):
        self.inner_func()

        with self.assertRaises(ImportError):
            from modules import other
            assert other

        from modules import example
        assert example

    class SomeClass:

        @fail_importing("modules.example")
        def some_method(self):
            from modules import example
            assert example

    def test_method(self):
        with self.assertRaises(ImportError):
            self.SomeClass().some_method()
