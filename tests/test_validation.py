"""Tests for validation and comparison functions."""
import re
import sys
import textwrap
from . import _unittest as unittest
from datatest.differences import (
    BaseDifference,
    Missing,
    Extra,
    Invalid,
    Deviation,
)
from datatest._utils import IterItems

from datatest.validation import ValidationError
from datatest.validation import validate
from datatest.validation import valid


# Remove for datatest version 0.9.8.
import warnings
warnings.filterwarnings('ignore', message='subset and superset warning')


# FOR TESTING: A minimal subclass of BaseDifference.
# BaseDifference itself should not be instantiated
# directly.
class MinimalDifference(BaseDifference):
    def __init__(self, *args):
        self._args = args

    @property
    def args(self):
        return self._args


def dedent_and_strip(text):
    """A helper function to dedent and strip strings."""
    return textwrap.dedent(text).strip()


class TestValidationError(unittest.TestCase):
    def test_single_diff(self):
        single_diff = MinimalDifference('A')
        err = ValidationError(single_diff)
        self.assertEqual(err.differences, [single_diff])

    def test_list_of_diffs(self):
        diff_list = [MinimalDifference('A'), MinimalDifference('B')]

        err = ValidationError(diff_list)
        self.assertEqual(err.differences, diff_list)

    def test_iter_of_diffs(self):
        diff_list = [MinimalDifference('A'), MinimalDifference('B')]
        diff_iter = iter(diff_list)

        err = ValidationError(diff_iter)
        self.assertEqual(err.differences, diff_list, 'iterable should be converted to list')

    def test_dict_of_diffs(self):
        diff_dict = {'a': MinimalDifference('A'), 'b': MinimalDifference('B')}

        err = ValidationError(diff_dict)
        self.assertEqual(err.differences, diff_dict)

    def test_dict_of_lists(self):
        diff_dict = {'a': [MinimalDifference('A')], 'b': [MinimalDifference('B')]}

        err = ValidationError(diff_dict)
        self.assertEqual(err.differences, diff_dict)

    def test_iteritems_of_diffs(self):
        diff_dict = {'a': MinimalDifference('A'), 'b': MinimalDifference('B')}
        diff_items = ((k, v) for k, v in diff_dict.items())

        err = ValidationError(diff_items)
        self.assertEqual(err.differences, diff_dict)

    def test_dict_of_iters(self):
        dict_of_lists = {'a': [MinimalDifference('A')], 'b': [MinimalDifference('B')]}
        dict_of_iters = dict((k, iter(v)) for k, v in dict_of_lists.items())

        err = ValidationError(dict_of_iters)
        self.assertEqual(err.differences, dict_of_lists)

    def test_iteritems_of_iters(self):
        dict_of_lists = {'a': [MinimalDifference('A')], 'b': [MinimalDifference('B')]}
        iteritems_of_iters = ((k, iter(v)) for k, v in dict_of_lists.items())

        err = ValidationError(iteritems_of_iters)
        self.assertEqual(err.differences, dict_of_lists)

    def test_bad_args(self):
        with self.assertRaises(TypeError, msg='must be iterable'):
            bad_arg = object()
            ValidationError(bad_arg, 'invalid data')

    def test_str_method(self):
        # Assert basic format and trailing comma.
        err = ValidationError([MinimalDifference('A')], 'invalid data')
        expected = dedent_and_strip("""
            invalid data (1 difference): [
                MinimalDifference('A'),
            ]
        """)
        self.assertEqual(str(err), expected)

        # Assert without description.
        err = ValidationError([MinimalDifference('A')])  # <- No description!
        expected = dedent_and_strip("""
            1 difference: [
                MinimalDifference('A'),
            ]
        """)
        self.assertEqual(str(err), expected)

        # Assert "no cacheing"--objects that inhereit from some
        # Exceptions can cache their str--but ValidationError should
        # not do this.
        err._differences = [MinimalDifference('B')]
        err._description = 'changed'
        updated = dedent_and_strip("""
            changed (1 difference): [
                MinimalDifference('B'),
            ]
        """)
        self.assertEqual(str(err), updated)

        # Assert dict format and trailing comma.
        err = ValidationError({'x': MinimalDifference('A'),
                               'y': MinimalDifference('B')},
                              'invalid data')
        regex = dedent_and_strip(r"""
            invalid data \(2 differences\): \{
                '[xy]': MinimalDifference\('[AB]'\),
                '[xy]': MinimalDifference\('[AB]'\),
            \}
        """)
        self.assertRegex(str(err), regex)  # <- Using regex because dict order
                                           #    can not be assumed for Python
                                           #    versions 3.5 and earlier.

    def test_str_sorting(self):
        """Check that string shows differences sorted by arguments."""
        self.maxDiff = None

        # Check sorting of non-mapping container.
        err = ValidationError([MinimalDifference('Z', 'Z'),
                               MinimalDifference('Z'),
                               MinimalDifference(1, 'C'),
                               MinimalDifference('B', 'C'),
                               MinimalDifference('A'),
                               MinimalDifference(1.5),
                               MinimalDifference(True),
                               MinimalDifference(0),
                               MinimalDifference(None)])
        expected = dedent_and_strip("""
            9 differences: [
                MinimalDifference(None),
                MinimalDifference(0),
                MinimalDifference(True),
                MinimalDifference(1, 'C'),
                MinimalDifference(1.5),
                MinimalDifference('A'),
                MinimalDifference('B', 'C'),
                MinimalDifference('Z'),
                MinimalDifference('Z', 'Z'),
            ]
        """)
        self.assertEqual(str(err), expected)

        # Make sure that all differences are being sorted (not just
        # those being displayed).
        err._should_truncate = lambda lines, chars: lines > 4
        expected = dedent_and_strip("""
            9 differences: [
                MinimalDifference(None),
                MinimalDifference(0),
                MinimalDifference(True),
                MinimalDifference(1, 'C'),
                ...
        """)
        self.assertEqual(str(err), expected)

        # Check sorting of non-mapping container.
        err = ValidationError(
            {
                ('C', 3): [MinimalDifference('Z', 3), MinimalDifference(1, 2)],
                ('A', 'C'): MinimalDifference('A'),
                'A': [MinimalDifference('C'), MinimalDifference(1)],
                2: [MinimalDifference('B'), MinimalDifference('A')],
                1: MinimalDifference('A'),
                (None, 4): MinimalDifference('A'),
            },
            'description string'
        )
        expected = dedent_and_strip("""
            description string (6 differences): {
                1: MinimalDifference('A'),
                2: [MinimalDifference('A'), MinimalDifference('B')],
                'A': [MinimalDifference(1), MinimalDifference('C')],
                (None, 4): MinimalDifference('A'),
                ('A', 'C'): MinimalDifference('A'),
                ('C', 3): [MinimalDifference(1, 2), MinimalDifference('Z', 3)],
            }
        """)
        self.assertEqual(str(err), expected)

    def test_str_no_sorting(self):
        """Check that string does not sort when _sorted_str is False."""
        self.maxDiff = None

        # Check no sorting of non-mapping container.
        err = ValidationError([MinimalDifference('Z', 'Z'),
                               MinimalDifference('Z'),
                               MinimalDifference(1, 'C'),
                               MinimalDifference('B', 'C'),
                               MinimalDifference('A'),
                               MinimalDifference(1.5),
                               MinimalDifference(True),
                               MinimalDifference(0),
                               MinimalDifference(None)])

        err._sorted_str = False  # <- Turn-off sorting!

        expected = dedent_and_strip("""
            9 differences: [
                MinimalDifference('Z', 'Z'),
                MinimalDifference('Z'),
                MinimalDifference(1, 'C'),
                MinimalDifference('B', 'C'),
                MinimalDifference('A'),
                MinimalDifference(1.5),
                MinimalDifference(True),
                MinimalDifference(0),
                MinimalDifference(None),
            ]
        """)
        self.assertEqual(str(err), expected)

        # Check sorted dict keys but unsorted value containers.
        err = ValidationError(
            {
                ('C', 3): [MinimalDifference('Z', 3), MinimalDifference(1, 2)],
                ('A', 'C'): MinimalDifference('A'),
                'A': [MinimalDifference('C'), MinimalDifference(1)],
                2: [MinimalDifference('B'), MinimalDifference('A')],
                1: MinimalDifference('A'),
                (None, 4): MinimalDifference('A'),
            },
            'description string'
        )

        err._sorted_str = False  # <- Turn-off sorting!

        expected = dedent_and_strip("""
            description string (6 differences): {
                1: MinimalDifference('A'),
                2: [MinimalDifference('B'), MinimalDifference('A')],
                'A': [MinimalDifference('C'), MinimalDifference(1)],
                (None, 4): MinimalDifference('A'),
                ('A', 'C'): MinimalDifference('A'),
                ('C', 3): [MinimalDifference('Z', 3), MinimalDifference(1, 2)],
            }
        """)
        self.assertEqual(str(err), expected)

    def test_str_truncation(self):
        # Assert optional truncation behavior.
        err = ValidationError([MinimalDifference('A'),
                               MinimalDifference('B'),
                               MinimalDifference('C'),],
                              'invalid data')
        self.assertIsNone(err._should_truncate)
        self.assertIsNone(err._truncation_notice)
        no_truncation = dedent_and_strip("""
            invalid data (3 differences): [
                MinimalDifference('A'),
                MinimalDifference('B'),
                MinimalDifference('C'),
            ]
        """)
        self.assertEqual(str(err), no_truncation)

        # Truncate without notice.
        err._should_truncate = lambda line_count, char_count: char_count > 35
        err._truncation_notice = None
        truncation_witout_notice = dedent_and_strip("""
            invalid data (3 differences): [
                MinimalDifference('A'),
                ...
        """)
        self.assertEqual(str(err), truncation_witout_notice)

        # Truncate and use truncation notice.
        err._should_truncate = lambda line_count, char_count: char_count > 35
        err._truncation_notice = 'Message truncated.'
        truncation_plus_notice = dedent_and_strip("""
            invalid data (3 differences): [
                MinimalDifference('A'),
                ...

            Message truncated.
        """)
        self.assertEqual(str(err), truncation_plus_notice)

    def test_repr(self):
        err = ValidationError([MinimalDifference('A')])  # <- No description.
        expected = "ValidationError([MinimalDifference('A')])"
        self.assertEqual(repr(err), expected)

        err = ValidationError([MinimalDifference('A')], 'description string')
        expected = "ValidationError([MinimalDifference('A')], 'description string')"
        self.assertEqual(repr(err), expected)

        # Objects that inhereit from some Exceptions can cache their
        # repr--but ValidationError should not do this.
        err._differences = [MinimalDifference('B')]
        err._description = 'changed'
        self.assertNotEqual(repr(err), expected, 'exception should not cache repr')

        updated = "ValidationError([MinimalDifference('B')], 'changed')"
        self.assertEqual(repr(err), updated)

    def test_module_property(self):
        """Module property should be 'datatest' so that testing
        frameworks display the error as 'datatest.ValidationError'.

        By default, instances would be displayed as
        'datatest.validation.ValidationError' but this awkwardly
        long and the submodule name--'validation'--is not needed
        because the class is imported into datatest's root namespace.
        """
        import datatest
        msg = "should be in datatest's root namespace"
        self.assertIs(ValidationError, datatest.ValidationError)

        msg = "should be set to 'datatest' to shorten display name"
        self.assertEqual('datatest', ValidationError.__module__)

    def test_args(self):
        err = ValidationError([MinimalDifference('A')], 'invalid data')
        self.assertEqual(err.args, ([MinimalDifference('A')], 'invalid data'))

        err = ValidationError([MinimalDifference('A')])
        self.assertEqual(err.args, ([MinimalDifference('A')], None))


class TestRenderTraceback(unittest.TestCase):
    """The ValidationError._render_traceback_() method returns a list
    of strings for Jupyter/IPython to display a syntax-highlighted
    tracebacks that omits stack frames that originate from within
    datatest itself. This method is only defined in Python 3.7 and
    newer.
    """

    def test_not_current_error(self):
        """When a ValidationError is not the currently-handled error,
        _render_traceback_() should display "No traceback available"
        in place of a traceback.
        """
        if sys.version_info[:2] < (3, 7):
            return  # <- EXIT!

        err = ValidationError(Invalid('abc'))
        list_of_strings = err._render_traceback_()
        self.assertIsInstance(list_of_strings, list)
        actual_text = '\n'.join(list_of_strings)

        expected_text = dedent_and_strip("""
            No traceback available

            datatest.ValidationError: 1 difference: [
                Invalid('abc'),
            ]
        """)
        self.assertEqual(actual_text.strip(), expected_text)

    def test_current_error(self):
        """When a ValidationError is currently being handled,
        _render_traceback_() should return a rich IPython-style
        traceback if IPython is installed. If IPython is not
        installed, a normal Python traceback should be returned.
        """
        if sys.version_info[:2] < (3, 7):
            return  # <- EXIT!

        # Get traceback lines of currently handled error.
        try:
            raise ValidationError(Invalid('abc'))
        except ValidationError as err:
            list_of_strings = err._render_traceback_()

        self.assertIsInstance(list_of_strings, list)
        actual_text = '\n'.join(list_of_strings)

        # Strip ANSI color escape codes from output.
        ansi_escape_code_regex = r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])'
        actual_text = re.sub(ansi_escape_code_regex, '', actual_text)

        # Get regex pattern to use for matching.
        try:
            import IPython
            expected_regex = dedent_and_strip(r"""
                ---------------------------------------------------------------------------
                ValidationError                           Traceback \(most recent call last\)
                [^\n]+
                    \d+[^\n]*
                    \d+         try:
                --> \d+             raise ValidationError\(Invalid\('abc'\)\)
                    \d+         except ValidationError as err:
                    \d+             list_of_strings = err._render_traceback_\(\)

                ValidationError: 1 difference: \[
                    Invalid\('abc'\),
                \]
            """)
        except ImportError:
            expected_regex = dedent_and_strip(r"""
                Traceback \(most recent call last\):
                  File "[^"]+", line \d+, in test_\w+
                    raise ValidationError\(Invalid\('abc'\)\)
                datatest.ValidationError: 1 difference: \[
                    Invalid\('abc'\),
                \]
            """)

        msg = '\nText does not match pattern:\n{0}'.format(actual_text)
        self.assertRegex(actual_text, expected_regex, msg=msg)


class TestValidationIntegration(unittest.TestCase):
    def test_valid(self):
        a = set([1, 2, 3])
        b = set([2, 3, 4])

        self.assertTrue(valid(a, a))

        self.assertFalse(valid(a, b))

    def test_validate(self):
        a = set([1, 2, 3])
        b = set([2, 3, 4])

        self.assertIsNone(validate(a, a))

        with self.assertRaises(ValidationError):
            validate(a, b)


class TestValidate(unittest.TestCase):
    """An integration test to check behavior of validate() function."""
    def test_required_vs_data_passing(self):
        """Single requirement to BaseElement or non-mapping
        container of data.
        """
        data = ('abc', 1)  # A single base element.
        requirement = ('abc', int)
        self.assertIsNone(validate(data, requirement))

        data = [('abc', 1), ('abc', 2)]  # Non-mapping container of base elements.
        requirement = ('abc', int)
        self.assertIsNone(validate(data, requirement))

    def test_required_vs_data_failing(self):
        """Apply single requirement to BaseElement or non-mapping
        container of data.
        """
        with self.assertRaises(ValidationError) as cm:
            data = ('abc', 1.0)  # A single base element.
            requirement = ('abc', int)
            validate(data, requirement)
        differences = cm.exception.differences
        self.assertEqual(differences, [Invalid(('abc', 1.0))])

        with self.assertRaises(ValidationError) as cm:
            data = [('abc', 1.0), ('xyz', 2)]  # Non-mapping container of base elements.
            requirement = ('abc', int)
            validate(data, requirement)
        differences = cm.exception.differences
        self.assertEqual(differences, [Invalid(('abc', 1.0)), Invalid(('xyz', 2))])

    def test_required_vs_mapping_passing(self):
        data = {'a': ('abc', 1), 'b': ('abc', 2)}  # Mapping of base-elements.
        requirement = ('abc', int)
        self.assertIsNone(validate(data, requirement))

        data = {'a': [1, 2], 'b': [3, 4]}  # Mapping of containers.
        requirement = int
        self.assertIsNone(validate(data, requirement))

    def test_required_vs_mapping_failing(self):
        with self.assertRaises(ValidationError) as cm:
            data = {'a': ('abc', 1.0), 'b': ('xyz', 2)}  # Mapping of base-elements.
            requirement = ('abc', int)
            validate(data, requirement)
        differences = cm.exception.differences
        self.assertEqual(differences, {'a': Invalid(('abc', 1.0)), 'b': Invalid(('xyz', 2))})

        with self.assertRaises(ValidationError) as cm:
            data = {'a': [1, 2.0], 'b': [3.0, 4]}  # Mapping of containers.
            validate(data, int)
        differences = cm.exception.differences
        self.assertEqual(differences, {'a': [Invalid(2.0)], 'b': [Invalid(3.0)]})

    def test_mapping_vs_mapping_passing(self):
        data = {'a': ('abc', 1), 'b': ('abc', 2.0)}  # Mapping of base-elements.
        requirement = {'a': ('abc', int), 'b': ('abc', float)}  # Mapping of requirements.
        self.assertIsNone(validate(data, requirement))

        data = {'a': [('abc', 1), ('abc', 2)],
                'b': [('abc', 1.0), ('abc', 2.0)]}  # Mapping of containers.
        requirement = {'a': ('abc', int), 'b': ('abc', float)}  # Mapping of requirements.
        self.assertIsNone(validate(data, requirement))

    def test_mapping_vs_mapping_failing(self):
        with self.assertRaises(ValidationError) as cm:
            data = {'a': ('abc', 1.0), 'b': ('xyz', 2.0)}  # Mapping of base-elements.
            requirement = {'a': ('abc', int), 'b': ('abc', float)}  # Mapping of requirements.
            validate(data, requirement)
        actual = cm.exception.differences
        expected = {
            'a': Invalid(('abc', 1.0), ('abc', int)),
            'b': Invalid(('xyz', 2.0), ('abc', float)),
        }
        self.assertEqual(actual, expected)

        with self.assertRaises(ValidationError) as cm:
            data = {'a': [('abc', 1.0), ('abc', 2)],
                    'b': [('abc', 1.0), ('xyz', 2.0)]}  # Mapping of containers.
            requirement = {'a': ('abc', int), 'b': ('abc', float)}  # Mapping of requirements.
            validate(data, requirement)
        actual = cm.exception.differences
        expected = {
            'a': [Invalid(('abc', 1.0))],
            'b': [Invalid(('xyz', 2.0))],
        }
        self.assertEqual(actual, expected)

    def test_predicate_method(self):
        data = {'A': 'aaa', 'B': [1, 2, 3], 'C': ('a', 1)}
        requirement = {'A': set(['aaa', 'bbb']), 'B': int, 'C': ('a', 1)}
        validate.predicate(data, requirement)

        with self.assertRaises(ValidationError) as cm:
            data = {'A': 'aaa', 'B': [1, 2, 3.5], 'C': ('b', 2)}
            requirement = {'A': set(['aaa', 'bbb']), 'B': int, 'C': ('a', 1)}
            validate.predicate(data, requirement)
        actual = cm.exception.differences
        expected = {
            'B': [Invalid(3.5)],
            'C': Invalid(('b', 2), expected=('a', 1)),
        }
        self.assertEqual(actual, expected)

    def test_predicate_regex(self):
        data = {'A': 'Alpha', 'B': ['Beta', 'Gamma']}
        requirement = {'A': r'^[A-Z]', 'B': r'^[A-Z]'}
        validate.regex(data, requirement)

        with self.assertRaises(ValidationError) as cm:
            data = {'A': 'Alpha', 'B': ['Beta', 'gamma'], 'C': ('b', 2)}
            requirement = {'A': r'^[A-Z]', 'B': r'^[A-Z]', 'C': r'\d'}
            validate.regex(data, requirement)
        actual = cm.exception.differences
        expected = {
            'B': [Invalid('gamma')],
            'C': Invalid(('b', 2), expected=r'\d'),
        }
        self.assertEqual(actual, expected)

    def test_approx_method(self):
        data = {'A': 5.00000001, 'B': 10.00000001}
        requirement = {'A': 5, 'B': 10}
        validate.approx(data, requirement)

        data = [5.00000001, 10.00000001]
        requirement = [5, 10]
        validate.approx(data, requirement)

        data = {'A': [5.00000001, 10.00000001], 'B': [5.00000001, 10.00000001]}
        requirement = {'A': [5, 10], 'B': [5, 10]}
        validate.approx(data, requirement)

        with self.assertRaises(ValidationError) as cm:
            data = {'A': 3, 'B': 10.00000001}
            requirement = {'A': 5, 'B': 10}
            validate.approx(data, requirement)
        actual = cm.exception.differences
        expected = {'A': Deviation(-2, 5)}
        self.assertEqual(actual, expected)

    def test_fuzzy_method(self):
        data = {'A': 'aaa', 'B': 'bbx'}
        requirement = {'A': 'aaa', 'B': 'bbb'}
        validate.fuzzy(data, requirement)

        with self.assertRaises(ValidationError) as cm:
            data = {'A': 'axx', 'B': 'bbx'}
            requirement = {'A': 'aaa', 'B': 'bbb'}
            validate.fuzzy(data, requirement)
        actual = cm.exception.differences
        expected = {'A': Invalid('axx', expected='aaa')}
        self.assertEqual(actual, expected)

    def test_interval_method(self):
        data = {'A': 5, 'B': 7, 'C': 9}
        validate.interval(data, 5, 10)

        data = [5, 7, 9]
        validate.interval(data, 5, 10)

        data = {'A': [7, 8, 9], 'B': [5, 6]}
        validate.interval(data, 5, 10)

        with self.assertRaises(ValidationError) as cm:
            data = {'A': 3, 'B': 6, 'C': [6, 7], 'D': [9, 10]}
            validate.interval(data, 5, 9)
        actual = cm.exception.differences
        expected = {'A': Deviation(-2, 5), 'D': [Deviation(+1, 9)]}
        self.assertEqual(actual, expected)

    def test_set_method(self):
        data = [1, 2, 3, 4]
        requirement = [1, 2, 3, 4]
        validate.set(data, requirement)

        with self.assertRaises(ValidationError) as cm:
            data = [1, 2, 3, 5]
            requirement = set([1, 2, 3, 4])
            validate.set(data, requirement)
        actual = cm.exception.differences
        expected = [Missing(4), Extra(5)]
        self.assertEqual(actual, expected)

        with self.assertRaises(ValidationError) as cm:
            data ={'A': [1, 2, 3], 'B': [3]}
            requirement = {'A': iter([1, 2]), 'B': iter([3, 4])}
            validate.set(data, requirement)
        actual = cm.exception.differences
        expected = {'A': [Extra(3)], 'B': [Missing(4)]}
        self.assertEqual(actual, expected)

    def test_superset_method(self):
        data = [1, 2, 3, 4]
        requirement = [1, 2, 3]
        validate.superset(data, requirement)

        with self.assertRaises(ValidationError) as cm:
            data = [1, 2, 3]
            requirement = set([1, 2, 3, 4])
            validate.superset(data, requirement)
        actual = cm.exception.differences
        expected = [Missing(4)]
        self.assertEqual(actual, expected)

        with self.assertRaises(ValidationError) as cm:
            data ={'A': [1, 2, 3], 'B': [3, 4, 5]}
            requirement = {'A': iter([1, 2]), 'B': iter([2, 3])}
            validate.superset(data, requirement)
        actual = cm.exception.differences
        expected = {'B': [Missing(2)]}
        self.assertEqual(actual, expected)

    def test_subset_method(self):
        data = [1, 2, 3]
        requirement = [1, 2, 3, 4]
        validate.subset(data, requirement)

        with self.assertRaises(ValidationError) as cm:
            data = {'A': [1, 2, 3], 'B': [3, 4, 5]}
            requirement = {'A': set([1, 2, 3]), 'B': set([2, 3, 4])}
            validate.subset(data, requirement)
        actual = cm.exception.differences
        expected = {'B': [Extra(5)]}
        self.assertEqual(actual, expected)

    def test_unique_method(self):
        validate.unique([1, 2, 3, 4])

        with self.assertRaises(ValidationError) as cm:
            validate.unique([1, 2, 3, 3])
        actual = cm.exception.differences
        expected = [Extra(3)]
        self.assertEqual(actual, expected)

    def test_order_method(self):
        data = ['A', 'B', 'C', 'C']
        requirement = iter(['A', 'B', 'C', 'C'])
        validate.order(data, requirement)

        data = ['A', 'B', 'C', 'D']
        requirement = ['A', 'B', 'C', 'D']
        validate.order(data, requirement)

        with self.assertRaises(ValidationError) as cm:
            data = ['A', 'C', 'D', 'F']
            requirement = iter(['A', 'B', 'C', 'D'])
            validate.order(data, requirement)
        actual = cm.exception.differences
        expected = [Missing((1, 'B')), Extra((3, 'F'))]
        self.assertEqual(actual, expected)

        with self.assertRaises(ValidationError) as cm:
            data = {'x': ['A'], 'y': ['B', 'C', 'D']}
            requirement = {'x': ['A', 'B'], 'y': ['C', 'D']}
            validate.order(data, requirement)
        actual = cm.exception.differences
        expected = {'x': [Missing((1, 'B'))], 'y': [Extra((0, 'B'))]}
        self.assertEqual(actual, expected)
