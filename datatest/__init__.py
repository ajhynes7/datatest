# -*- coding: utf-8 -*-
"""test driven data-wrangling and validation

PYTEST_DONT_REWRITE
"""
from __future__ import absolute_import

# Datatest Core API (__all__ property defined in submodules)
from .validation import *   # Validation error and functions.
from .differences import *  # Difference classes.
from .acceptances import (  # Acceptance context manger API.
    accepted,
    allowed,  # <- Deprecated since 0.9.5
)

from ._vendor.predicate import Predicate

# Pandas extensions.
from ._pandas_integration import register_accessors

# Unittest-style API
from .case import DataTestCase
from .runner import mandatory
from .runner import DataTestRunner
from .main import DataTestProgram
from .main import main

# Data Handling API
from ._vendor.get_reader import get_reader
from ._working_directory import working_directory
from ._vendor.squint import Select
from ._vendor.squint import Query
from ._vendor.squint import Result
from ._vendor.repeatingcontainer import RepeatingContainer

# Set module explicitly to cleanup reprs and error reporting.
Select.__module__ = 'datatest'
Query.__module__ = 'datatest'
Result.__module__ = 'datatest'

__version__ = '0.10.0'


#############################################
# Register traceback formatting handler.
#############################################
from . import _excepthook
import sys as _sys
_sys.excepthook = _excepthook.excepthook
