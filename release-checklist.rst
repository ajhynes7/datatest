
Release Checklist
=================

#. Make sure correct version number is set in the following files
   (remove the ".devN" suffix):

   * ``datatest/__init__.py``
   * ``docs/conf.py``

#. Make sure the *description* argument in ``setup.py`` matches the project
   description on GitHub (in the "About" section).

#. In the call to ``setup()``, check the versions defined by the
   *python_requires* argument (see the "Version specifiers" section of
   PEP-440 for details).

#. In the call to ``setup()``, check the trove classifiers in the
   *classifiers* argument (see https://pypi.org/classifiers/ for values).

#. Check that *packages* argument of ``setup()`` is correct. Check that the
   value matches what ``setuptools.find_packages()`` returns:

   .. code-block:: python

        >>> import setuptools
        >>> sorted(setuptools.find_packages('.', exclude=['tests']))

   Defining this list explicitly (rather than using ``find_packages()``
   directly in ``setup.py`` file) is needed when installing on systems
   where ``setuptools`` is not available.

#. Make sure ``__past__`` sub-package includes a stub module for the
   current API version.

#. Update ``README.rst`` (including "Backward Compatibility" section).

#. Commit and push final changes to upstream repository:

        Prepare version info, CHANGELOG, and README for version N.N.N release.

#. Perform final checks to make sure there are no CI test failures.

#. Make sure the packaging tools are up-to-date:

   .. code-block:: console

        pip install -U twine wheel setuptools check-manifest

#. Check the manifest against the project's root folder:

   .. code-block:: console

        check-manifest .

#. Remove all existing files in the ``dist/`` folder.

#. Build new distributions:

   .. code-block:: console

        python setup.py sdist bdist_wheel

#. Upload source and wheel distributions to PyPI:

   .. code-block:: console

        twine upload dist/*

#. Double check PyPI project page and test installation from PyPI:

   .. code-block:: console

        python -m pip install datatest

#. Add version tag to upstream repository (also used by readthedocs.org).

#. Iterate the version number in the development repository to the next
   anticipated release and add a "dev" suffix (e.g., N.N.N.dev1). This
   version number should conform to the "Version scheme" section of PEP-440.
   Make sure these changes are reflected in the following files:

   * ``datatest/__init__.py``
   * ``docs/conf.py``

   Commit these changes with a comment like the one below:

        Iterate version number to the next anticipated release.

   This is done so that installations made directly from the development
   repository and the "latest" docs are not confused with the just-published
   "stable" versions.

#. Make sure the documentation reflects the new versions:

   * https://datatest.readthedocs.io/ (stable)
   * https://datatest.readthedocs.io/en/latest/ (latest)

#. Publish update announcement to relevant mailing lists:

   * python-announce-list@python.org
   * testing-in-python@lists.idyll.org
