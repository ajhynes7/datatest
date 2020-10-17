
.. currentmodule:: datatest

.. meta::
    :description: An overview of the "datatest" Python package, describing
                  its features and basic operation with examples.
    :keywords: introduction, datatest, examples


##################
A Tour of Datatest
##################

This document introduces :doc:`datatest </index>`'s support for
validation, error reporting, and acceptance declarations.


**********
Validation
**********

The validation process works by comparing some *data* to a given
*requirement*. If the requirement is satisfied, the data is considered
valid. But if the requirement is not satisfied, a :exc:`ValidationError`
is raised.

The :func:`validate` function checks that the *data* under test
satisfies a given *requirement*:

.. code-block:: python
    :linenos:
    :emphasize-lines: 5

    from datatest import validate

    data = ...
    requirement = ...
    validate(data, requirement)


Smart Comparisons
-----------------

The :func:`validate` function implements smart comparisons and will
use different validation methods for different *requirement* types.


For example, when *requirement* is a :py:class:`set`, validation
checks that elements in *data* are members of the required set:

.. code-block:: python
    :linenos:
    :emphasize-lines: 4

    from datatest import validate

    data = ['A', 'B', 'A']
    requirement = {'A', 'B'}
    validate(data, requirement)


When *requirement* is a **function**, validation checks that
the function returns True when applied to each element in *data*:

.. code-block:: python
    :linenos:
    :emphasize-lines: 5-6

    from datatest import validate

    data = [2, 4, 6, 8]

    def iseven(x):
        return x % 2 == 0

    validate(data, requirement=iseven)


When *requirement* is a **type**, validation checks that the
elements in *data* are an instances of that type:

.. code-block:: python
    :linenos:
    :emphasize-lines: 4

    from datatest import validate

    data = [2, 4, 6, 8]
    requirement = int
    validate(data, requirement)


And when *requirement* is a :py:class:`tuple`, validation
checks for tuple elements in *data* using multiple methods
at the same time---one method for each item in the required
tuple:

.. code-block:: python
    :linenos:
    :emphasize-lines: 8

    from datatest import validate

    data = [('a', 2), ('b', 4), ('c', 6)]

    def iseven(x):
        return x % 2 == 0

    requirement = (str, iseven)
    validate(data, requirement)

In addition to the examples above, several other validation
behaviors are available. For a complete listing with detailed
examples, see :ref:`validation-docs`.


Automatic Data Handling
-----------------------

Along with the smart comparison behavior, validation can apply
a given *requirement* to *data* objects of different formats.

The following examples perform type-checking to see if elements
are :py:class:`int` values. Switch between the different tabs
below and notice that the same *requirement* (``requirement = int``)
works for all of the different *data* formats:

.. tabs::

    .. group-tab:: Element

        An individual element:

        .. code-block:: python
            :linenos:
            :emphasize-lines: 3,4

            from datatest import validate

            data = 42
            requirement = int  # <- Same for all formats.
            validate(data, requirement)

        A *data* value is treated as single element if it's a string, tuple,
        or non-iterable object.

    .. group-tab:: Group

        A group of elements:

        .. code-block:: python
            :linenos:
            :emphasize-lines: 3,4

            from datatest import validate

            data = [1, 2, 3]
            requirement = int  # <- Same for all formats.
            validate(data, requirement)

        A *data* value is treated as a group of elements if it's any iterable
        other than a string, tuple, or mapping (e.g., in this case a
        :py:class:`list`).

    .. group-tab:: Mapping

        A mapping of elements:

        .. code-block:: python
            :linenos:
            :emphasize-lines: 3,4

            from datatest import validate

            data = {'A': 1, 'B': 2, 'C': 3}
            requirement = int  # <- Same for all formats.
            validate(data, requirement)

        When *data* is a mapping, its values are checked as individual
        elements if they are strings, tuples, non-iterable objects, or
        nested mappings.

    .. group-tab:: Mapping of Groups

        A mapping of groups of elements:

        .. code-block:: python
            :linenos:
            :emphasize-lines: 3,4

            from datatest import validate

            data = {'X': [1, 2, 3], 'Y': [4, 5, 6], 'Z': [7, 8, 9]}
            requirement = int  # <- Same for all formats.
            validate(data, requirement)

        A mapping's values are treated as a group of individual elements
        when they are any iterable other than a string, tuple, or another
        nested mapping.

Of course, not all formats are comparable. When *requirement* is itself
a mapping, there's no clear way to handle validation if *data* is a
single element or a non-mapping container. In cases like this, the
validation process will error-out before the data elements can be
checked.

In addition to built-in generic types, Datatest also provides automatic
handling for several third-party data types.

.. tabs::

    .. group-tab:: Pandas

        Datatest can work with :mod:`pandas` DataFrame, Series, Index,
        and MultiIndex objects:

        .. code-block:: python
            :linenos:
            :emphasize-lines: 9

            import pandas as pd
            import datatest as dt

            df = pd.DataFrame([('x', 1, 12.25),
                               ('y', 2, 33.75),
                               ('z', 3, 101.5)],
                              columns=['A', 'B', 'C'])

            dt.validate(df[['A', 'B']], (str, int))

    .. group-tab:: Pandas (integrated API)

        For users who prefer a more tightly integrated API, Datatest
        provides pandas `accessor extensions
        <https://pandas.pydata.org/pandas-docs/stable/reference/extensions.html>`_:

        .. code-block:: python
            :linenos:
            :emphasize-lines: 4, 11

            import pandas as pd
            import datatest as dt

            dt.register_accessors()

            df = pd.DataFrame([('x', 1, 12.25),
                               ('y', 2, 33.75),
                               ('z', 3, 101.5)],
                              columns=['A', 'B', 'C'])

            df[['A', 'B']].validate((str, int))

        After calling the :func:`register_accessors` function, you
        can use :func:`validate` as a *method* of your existing
        DataFrame, Series, Index, and MultiIndex objects.

    .. group-tab:: NumPy

        Handling is also supported for :mod:`numpy` objects including one-
        or two-dimentional array, recarray, and structured array objects.

        .. code-block:: python
            :linenos:
            :emphasize-lines: 9

            import numpy as np
            import datatest as dt

            a = np.array([('x', 1, 12.25),
                          ('y', 2, 33.75),
                          ('z', 3, 101.5)],
                         dtype='U10, int32, float32')

            dt.validate(a[['f0', 'f1']], (str, int))

    .. group-tab:: Squint

        Datatest also works well with :mod:`squint` Select, Query, and Result
        objects:

        .. code-block:: python
            :linenos:
            :emphasize-lines: 9

            from squint import Select
            from datatest import validate

            select = Select([('A', 'B', 'C'),
                             ('x', 1, 12.25),
                             ('y', 2, 33.75),
                             ('z', 3, 101.5)])

            validate(select(('A', 'B')), (str, int))

        .. admonition:: Origins
            :class: note

            Squint was originally part of Datatest itself---it grew out
            of Datatest's old validation API. But as Datatest matured,
            the need for a built-in query interface stoped making sense.
            This *simple query interface* was named "Squint" and the
            code was moved into its own project.

    .. group-tab:: Databases

        Database queries can also be validated directly:

        .. code-block:: python
            :linenos:
            :emphasize-lines: 13-14

            import sqlite3
            from datatest import validate

            conn = sqlite3.connect(':memory:')
            conn.executescript('''
                CREATE TABLE mydata(A, B, C);
                INSERT INTO mydata VALUES('x', 1, 12.25);
                INSERT INTO mydata VALUES('y', 2, 33.75);
                INSERT INTO mydata VALUES('z', 3, 101.5);
            ''')
            cursor = conn.cursor()

            cursor.execute('SELECT A, B FROM mydata;')
            validate(cursor, (str, int))

        This requires a ``cursor`` object to conform to Python's DBAPI2
        specification (see :pep:`249`). Most of Python's database packages
        support this interface.


******
Errors
******

When validation fails, a :class:`ValidationError` is raised. A ValidationError
contains a collection of difference objects---one difference for each element
in *data* that fails to satisfy the *requirement*.

Difference objects can be one of of four types: :class:`Missing`,
:class:`Extra`, :class:`Deviation` or :class:`Invalid`.


"Missing" Differences
---------------------

In this example, we check that the list ``['A', 'B']`` contains members
of the set ``{'A', 'B', 'C', 'D'}``:

.. code-block:: python
    :linenos:

    from datatest import validate

    data = ['A', 'B']
    requirement = {'A', 'B', 'C', 'D'}
    validate(data, requirement)

This fails because the elements ``'C'`` and ``'D'`` are not present in
*data*. They appear below as :class:`Missing` differences:

.. code-block:: none
    :emphasize-lines: 4-7

    Traceback (most recent call last):
      File "example.py", line 5, in <module>
        validate(data, requirement)
    datatest.ValidationError: does not satisfy set membership (2 differences): [
        Missing('C'),
        Missing('D'),
    ]


"Extra" Differences
-------------------

In this next example, we will reverse the previous situation by checking
that elements in the list ``['A', 'B', 'C', 'D']`` are members of the set
``{'A', 'B'}``:

.. code-block:: python
    :linenos:

    from datatest import validate

    data = ['A', 'B', 'C', 'D']
    requirement = {'A', 'B'}
    validate(data, requirement)

Of course, this validation fails because the elements ``'C'`` and ``'D'``
are not members of the *requirement* set. They appear below as :class:`Extra`
differences:

.. code-block:: none
    :emphasize-lines: 4-7

    Traceback (most recent call last):
      File "example.py", line 5, in <module>
        validate(data, requirement)
    datatest.ValidationError: does not satisfy set membership (2 differences): [
        Extra('C'),
        Extra('D'),
    ]


"Invalid" Differences
---------------------

In this next example, the *requirement* is a tuple, ``(str, iseven)``.
It checks for tuple elements where the first value is a string and the
second value is an even number:

.. code-block:: python
    :linenos:

    from datatest import validate

    data = [('a', 2), ('b', 4), ('c', 6), (1.25, 8), ('e', 9)]

    def iseven(x):
        return x % 2 == 0

    requirement = (str, iseven)
    validate(data, requirement)

Two of the elements in *data* fail to satisfy the *requirement*: ``(1.25, 8)``
fails because 1.25 is not a string and ``('e', 9)`` fails because 9 is
not an even number. These are represented in the error as :class:`Invalid`
differences:

.. code-block:: none
    :emphasize-lines: 4-8

    Traceback (most recent call last):
      File "example.py", line 9, in <module>
        validate(data, requirement)
    datatest.ValidationError: does not satisfy (<class 'str'>, <function iseven
    at 0x3f75ca26>) (2 differences): [
        Invalid((1.25, 8)),
        Invalid(('e', 9)),
    ]


"Deviation" Differences
-----------------------

In the following example, the *requirement* is a dictionary of numbers.
The *data* elements are checked against *reqirement* elements of the
same key:

.. code-block:: python
    :linenos:

    from datatest import validate

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


This validation fails because some of the values don't match (C: ``299``
≠ ``300`` and D: ``405`` ≠ ``400``). Failed quantitative comparisons raise
:class:`Deviation` differences:

.. code-block:: none
    :emphasize-lines: 4-7

    Traceback (most recent call last):
      File "example.py", line 17, in <module>
        validate(data, requirement)
    datatest.ValidationError: does not satisfy mapping requirements (2 differences): {
        'C': Deviation(-1, 300),
        'D': Deviation(+5, 400),
    }


***********
Acceptances
***********

Sometimes a failing test cannot be addressed by changing the data
itself. Perhaps two equally-authoritative sources disagree, perhaps
it's important to keep the original data unchanged, or perhaps a lack
of information makes correction impossible. For cases like these,
datatest can accept certain discrepancies when users judge that doing
so is appropriate.

The :func:`accepted` function returns a context manager that operates
on a ValidationError's collection of differences.


Accepted Type
-------------

Without an acceptance, the following validation would fail because the
values ``'C'`` and ``'D'`` are not members of the set (see the following
example). But if we decide that :class:`Extra` differences are acceptible,
we can use ``accepted(Extra)``:

.. tabs::

    .. group-tab:: Using Acceptance

        .. code-block:: python
            :linenos:
            :emphasize-lines: 9

            from datatest import (
                validate,
                accepted,
                Extra,
            )

            data = ['A', 'B', 'C', 'D']
            requirement = {'A', 'B'}
            with accepted(Extra):
                validate(data, requirement)

    .. group-tab:: No Acceptance

        .. code-block:: python
            :linenos:

            from datatest import (
                validate,
                accepted,
                Extra,
            )

            data = ['A', 'B', 'C', 'D']
            requirement = {'A', 'B'}
            validate(data, requirement)

        .. code-block:: none
            :emphasize-lines: 5-6

            Traceback (most recent call last):
              File "example.py", line 9, in <module>
                validate(data, requirement)
            datatest.ValidationError: does not satisfy set membership (2 differences): [
                Extra('C'),
                Extra('D'),
            ]

Using the acceptance, we suppress the error caused by all of
the :class:`Extra` differences. But without the acceptance, the
ValidationError is raised.


Accepted Instance
-----------------

If we want more precision, we can accept a specific difference---rather
than all differences of a given type. For example, if the difference
:class:`Extra('C') <Extra>` is acceptible, we can use
``accepted(Extra('C'))``:

.. tabs::

    .. group-tab:: Using Acceptance

        .. code-block:: python
            :linenos:
            :emphasize-lines: 9

            from datatest import (
                validate,
                accepted,
                Extra,
            )

            data = ['A', 'B', 'C', 'D']
            requirement = {'A', 'B'}
            with accepted(Extra('C')):
                validate(data, requirement)

        .. code-block:: none

            Traceback (most recent call last):
              File "example.py", line 10, in <module>
                validate(data, requirement)
            datatest.ValidationError: does not satisfy set membership (1 difference): [
                Extra('D'),
            ]

        This acceptance suppresses the extra ``'C'`` but does not address
        the extra ``'D'`` so the ValidationError is still raised. This
        remaining error can be addressed by correcting the data, altering
        the acceptance, or modifying the requirement.

    .. group-tab:: No Acceptance

        .. code-block:: python
            :linenos:

            from datatest import (
                validate,
                accepted,
                Extra,
            )

            data = ['A', 'B', 'C', 'D']
            requirement = {'A', 'B'}
            validate(data, requirement)

        .. code-block:: none
            :emphasize-lines: 5

            Traceback (most recent call last):
              File "example.py", line 9, in <module>
                validate(data, requirement)
            datatest.ValidationError: does not satisfy set membership (2 differences): [
                Extra('C'),
                Extra('D'),
            ]


Accepted Container of Instances
-------------------------------

We can also accept multiple specific differences by defining a
container of difference objects. To build on the previous example,
we can use ``accepted([Extra('C'), Extra('D')])`` to accept the
two differences explicitly:

.. tabs::

    .. group-tab:: Using Acceptance

        .. code-block:: python
            :linenos:
            :emphasize-lines: 9

            from datatest import (
                validate,
                accepted,
                Extra,
            )

            data = ['A', 'B', 'C', 'D']
            requirement = {'A', 'B'}
            with accepted([Extra('C'), Extra('D')]):
                validate(data, requirement)

    .. group-tab:: No Acceptance

        .. code-block:: python
            :linenos:

            from datatest import (
                validate,
                accepted,
                Extra,
            )

            data = ['A', 'B', 'C', 'D']
            requirement = {'A', 'B'}
            validate(data, requirement)

        .. code-block:: none
            :emphasize-lines: 5-6

            Traceback (most recent call last):
              File "example.py", line 9, in <module>
                validate(data, requirement)
            datatest.ValidationError: does not satisfy set membership (2 differences): [
                Extra('C'),
                Extra('D'),
            ]


Accepted Tolerance
------------------

When comparing quantative values, you may decide that
deviations of a certain magnitude are acceptible. Calling
:meth:`accepted.tolerance(5) <accepted.tolerance>` returns
a context manager that accepts differences within a tolerance
of plus-or-minus five without triggering a test failure:

.. tabs::

    .. group-tab:: Using Acceptance

        .. code-block:: python
            :linenos:
            :emphasize-lines: 16

            from datatest import validate
            from datatest import accepted

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
            with accepted.tolerance(5):  # accepts ±5
                validate(data, requirement)

    .. group-tab:: No Acceptance

        .. code-block:: python
            :linenos:

            from datatest import validate
            from datatest import accepted

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


        .. code-block:: none
            :emphasize-lines: 5-6

            Traceback (most recent call last):
              File "example.py", line 16, in <module>
                validate(data, requirement)
            datatest.ValidationError: does not satisfy mapping requirements (2 differences): {
                'C': Deviation(-1, 300),
                'D': Deviation(+5, 400),
            }


Other Acceptances
-----------------

In addtion to the previous examples, there are other acceptances
available for specific cases---:meth:`accepted.keys`, :meth:`accepted.args`,
:meth:`accepted.percent`, etc. For a list of all possible acceptances, see
:ref:`acceptance-docs`.


Combining Acceptances
---------------------

Acceptances can also be combined using the operators ``&`` and ``|``
to define more complex criteria:

.. code-block:: python
    :emphasize-lines: 7, 11

    from datatest import (
        validate,
        accepted,
    )

    # Accept up to five missing differences.
    with accepted(Missing) & accepted.count(5):
        validate(..., ...)

    # Accept differences of ±10 or ±5%.
    with accepted.tolerance(10) | accepted.percent(0.05):
        validate(..., ...)

To learn more about these features, see :ref:`composability-docs` and
:ref:`order-of-operations-docs`.


*******************
Data Handling Tools
*******************

Datatest also provides utilities for other kinds of data handling:

:class:`working_directory`
    Context manager and decorator to temporarily set a working
    directory.

:class:`RepeatingContainer`
    Operate on a group of objects together instead of repeating
    the same methods and operations on each individual object
    (useful when comparing one source of data against another).
