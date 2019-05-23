"""Example of failing tests using pytest-style conventions."""

import re
from datatest import validate
from datatest import accepted


def test_using_set():
    """Check for set membership."""
    data = ['A', 'B', 'C', 'D']

    requirement = {'A', 'B'}

    validate(data, requirement)


def test_using_function():
    """Check that function returns True."""
    data = [2, 4, 6, 9]

    def iseven(x):
        return x % 2 == 0

    validate(data, iseven)


def test_using_type():
    """Check that values are of the given type."""
    data = [0.0, 1.0, 2]

    validate(data, float)


def test_using_regex():
    """Check that values match the given pattern."""
    data = ['bake', 'cake', 'fake']

    regex = re.compile('[bc]ake')

    validate(data, regex)


def test_using_string():
    """Check that values equal the given string."""
    data = ['foo', 'foo', 'bar']

    validate(data, 'foo')


def test_using_tuple():
    """Check that tuples of values satisfy corresponding tuple of
    requirements.
    """
    data = [('A', 1.0), ('A', 2), ('B', 3.0)]

    requirement = ('A', float)

    validate(data, requirement)


def test_using_dict():
    """Check that values satisfy requirements of matching keys."""
    data = {
        'A': 100,
        'B': 200,
        'C': 299,
        'D': 405,
    }
    requirement = {
        'A': 100,
        'B': 200,
        'C': 300,
        'D': 400,
    }
    validate(data, requirement)


def test_using_list():
    """Check that the order of values match the required sequence."""
    data = ['A', 'D', 'XXX', 'YYY', 'E', 'ZZZ', 'G']

    requirement = ['A', 'B', 'C', 'D', 'E', 'F', 'G']

    validate(data, requirement)
