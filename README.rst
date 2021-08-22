fail_importing
==============
A decorator designed to make testing optional dependencies painless.

It's common for libraries to have optional dependencies where the code has to detect if they are installed, using a
pattern like this:

.. code-block:: python

    try:
        import something
    else:
        import something_else as something

That way ``something`` is always defined and the rest of the codebase does not need to care. But how do we test both
branches under tests?

With ``fail_importing``, you can just slap a decorator onto your test and the code being tested will act as if
the dependency isn't installed.

.. code-block:: python

    @fail_importing("something")
    def test_something_else():
        ...

When the test finishes executing, the name can be imported as normal. It can be applied to normal functions, nested
functions, relative imports, and even generators!

`full_match`_ is used to determine if the path matches or not, so you can use any regex matching you need. Note that
relative imports are resolved to absolute imports before the check is made.

.. _full_match: https://docs.python.org/3/library/re.html#re.fullmatch
