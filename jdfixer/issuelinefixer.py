# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod
from .fixer import Fixer


class IssueLineFixer(Fixer):
    """The issue line fixer for fix line that report issue by java compiler"""

    @abstractmethod
    def fix(self, line: str, issue: str):
        """Return fixed line string if we have a fix, otherwise exception
        raised
        """
        pass

