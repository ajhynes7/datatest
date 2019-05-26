# -*- coding: utf-8 -*-
from __future__ import absolute_import
import textwrap
from . import _unittest as unittest

import datatest
from datatest.__past__ import api08  # <- MONKEY PATCH!!!

from datatest.differences import NOVALUE
from datatest.validation import _require_sequence


class TestColumns(unittest.TestCase):
    def test_columns(self):
        source = datatest.DataSource([[1, 2]], ('A', 'B'))
        self.assertEqual(source.columns(), ['A', 'B'])


class TestDataSourceConstructors(unittest.TestCase):
    @staticmethod
    def get_table_contents(source):
        connection = source._connection
        table = source._table
        cursor = connection.cursor()
        cursor.execute('SELECT * FROM ' + table)
        return list(cursor)

    def test_from_sequence_rows(self):
        data = [('x', 1),
                ('y', 2),
                ('z', 3)]

        source = datatest.DataSource(data, fieldnames=('A', 'B'))
        table_contents = self.get_table_contents(source)
        self.assertEqual(set(table_contents), set(data))

    def test_duplicate_fieldnames(self):
        regex = 'duplicate column name: A'
        with self.assertRaisesRegex(Exception, regex):
            records = [
                ('A', 'A'),
                ('1', '2'),
                ('1', '2'),
            ]
            source = datatest.DataSource(records)

        regex = 'contains multiple columns where names are empty strings or whitespace'
        with self.assertRaisesRegex(Exception, regex):
            records = [
                ('', ''),
                ('1', '2'),
                ('1', '2'),
            ]
            source = datatest.DataSource(records, fieldnames=['', ''])

    def test_from_dict_rows(self):
        data = [{'A': 'x', 'B': 1},
                {'A': 'y', 'B': 2},
                {'A': 'z', 'B': 3}]

        source = datatest.DataSource(data, fieldnames=['B', 'A'])  # <- Set field order.
        table_contents = self.get_table_contents(source)
        expected = [(1, 'x'), (2, 'y'), (3, 'z')]
        self.assertEqual(set(table_contents), set(expected))

    @staticmethod
    def _get_filelike(string, encoding):
        """Return file-like stream object."""
        import io
        import sys
        filelike = io.BytesIO(string)
        if encoding and sys.version >= '3':
            filelike = io.TextIOWrapper(filelike, encoding=encoding)
        return filelike

    def test_from_csv_file(self):
        csv_file = self._get_filelike(b'A,B\n'
                                      b'x,1\n'
                                      b'y,2\n'
                                      b'z,3\n', encoding='utf-8')
        source = datatest.DataSource.from_csv(csv_file)
        table_contents = self.get_table_contents(source)
        expected = [('x', '1'), ('y', '2'), ('z', '3')]
        self.assertEqual(set(table_contents), set(expected))

    def test_from_multiple_csv_files(self):
        file1 = self._get_filelike(b'A,B\n'
                                   b'x,1\n'
                                   b'y,2\n'
                                   b'z,3\n', encoding='utf-8')

        file2 = self._get_filelike(b'B,C\n'
                                   b'4,j\n'
                                   b'5,k\n'
                                   b'6,l\n', encoding='ascii')

        source = datatest.DataSource.from_csv([file1, file2])
        table_contents = self.get_table_contents(source)

        expected = [('x', '1', ''), ('y', '2', ''), ('z', '3', ''),
                    ('', '4', 'j'), ('', '5', 'k'), ('', '6', 'l')]
        self.assertEqual(set(table_contents), set(expected))


class TestDataQuery(unittest.TestCase):
    def test_callable(self):
        """In 0.9, __call__() was changed to execute()."""
        query = datatest.DataQuery('foo')
        self.assertTrue(hasattr(query, '__call__'), 'should be callable')


class TestRequireSequence(unittest.TestCase):
    def test_return_object(self):
        first = ['aaa', 'bbb', 'ccc']
        second = ['aaa', 'bbb', 'ccc']
        error = _require_sequence(first, second)
        self.assertIsNone(error)  # No difference, returns None.

        first = ['aaa', 'XXX', 'ccc']
        second = ['aaa', 'bbb', 'ccc']
        error = _require_sequence(first, second)
        self.assertIsInstance(error, AssertionError)

    def test_differs(self):
        first = ['aaa', 'XXX', 'ccc']
        second = ['aaa', 'bbb', 'ccc']
        error = _require_sequence(first, second)

        message = """
            Data sequence differs starting at index 1:

              'aaa', 'XXX', 'ccc'
                     ^^^^^
            Found 'XXX', expected 'bbb'
        """
        message = textwrap.dedent(message).strip()
        self.assertEqual(str(error), message)

    def test_missing(self):
        first = ['aaa', 'bbb']
        second = ['aaa', 'bbb', 'ccc']
        error = _require_sequence(first, second)

        message = """
            Data sequence is missing elements starting with index 2:

              ..., 'bbb', ?????
                          ^^^^^
            Expected 'ccc'
        """
        message = textwrap.dedent(message).strip()
        self.assertEqual(str(error), message)

    def test_extra(self):
        first = ['aaa', 'bbb', 'ccc', 'ddd']
        second = ['aaa', 'bbb', 'ccc']
        error = _require_sequence(first, second)

        message = """
            Data sequence contains extra elements starting with index 3:

              ..., 'ccc', 'ddd'
                          ^^^^^
            Found 'ddd'
        """
        message = textwrap.dedent(message).strip()
        self.assertEqual(str(error), message)

    def test_novalue(self):
        with self.assertRaises(ValueError):
            _require_sequence(NOVALUE, [1, 2, 3])


Missing = datatest.Missing
Extra = datatest.Extra
Deviation = datatest.Deviation
ValidationError = datatest.ValidationError
class TestAllowedKey(unittest.TestCase):
    def test_allowed_key(self):
        # Test mapping of differences.
        differences = {'aaa': Missing(1), 'bbb': Missing(2)}
        def function(key):
            return key == 'aaa'

        with self.assertRaises(ValidationError) as cm:
            with datatest.allowed_key(function):  # <- Apply acceptance!
                raise ValidationError(differences, 'some message')

        remaining_diffs = cm.exception.differences
        self.assertEqual(dict(remaining_diffs), {'bbb': Missing(2)})

        # Test mapping of differences with composite keys.
        differences = {('a', 7): Missing(1), ('b', 7): Missing(2)}
        def function(letter, number):
            return letter == 'a' and number == 7

        with self.assertRaises(ValidationError) as cm:
            with datatest.allowed_key(function):  # <- Apply acceptance!
                raise ValidationError(differences, 'some message')

        remaining_diffs = cm.exception.differences
        self.assertEqual(dict(remaining_diffs), {('b', 7): Missing(2)})

        # Test non-mapping container of differences.
        differences = [Missing(1), Extra(2)]
        def function(key):
            if key is not None:
                raise ValueError('key should always be None for non-mapping differences')
            return False  # < Don't match any differences.

        with self.assertRaises(ValidationError) as cm:
            with datatest.allowed_key(function):  # <- Apply acceptance!
                raise ValidationError(differences, 'some message')

        remaining_diffs = cm.exception.differences
        self.assertEqual(list(remaining_diffs), [Missing(1), Extra(2)])


class TestAcceptedArgs(unittest.TestCase):
    def test_accepted_args(self):
        # Single argument.
        differences =  [Missing('aaa'), Missing('bbb'), Extra('bbb')]
        def function(arg):
            return arg == 'bbb'

        with self.assertRaises(ValidationError) as cm:
            with datatest.AcceptedArgs(function):  # <- Apply acceptance!
                raise ValidationError(differences, 'some message')

        remaining_diffs = cm.exception.differences
        self.assertEqual(list(remaining_diffs), [Missing('aaa')])

        # Multiple arguments.
        differences =  [Deviation(+1, 5), Deviation(+2, 5)]
        def function(diff, expected):
            return diff < 2 and expected == 5

        with self.assertRaises(ValidationError) as cm:
            with datatest.AcceptedArgs(function):  # <- Apply acceptance!
                raise ValidationError(differences, 'some message')

        remaining_diffs = cm.exception.differences
        self.assertEqual(list(remaining_diffs), [Deviation(+2, 5)])


if __name__ == '__main__':
    unittest.main()
else:
    raise Exception('This test must be run directly or as a subprocess.')
