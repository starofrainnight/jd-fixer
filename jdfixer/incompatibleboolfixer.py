# -*- coding: utf-8 -*-

import re
from abc import ABC, abstractmethod
from .issuelinefixer import IssueLineFixer
from .exceptions import NotMatchedConditionError


class IncompatibleBoolFixer(IssueLineFixer):
    """Fix java compiler reports incompatible bool for int variable

    Fix error: incompatible types: boolean cannot be converted to int.

    For example :

    b.java:170: error: incompatible types: boolean cannot be converted to int
        int count = false;
                    ^
    """

    BOOL_CANNOT_CONVERT_TO_INT_PATTERN = r".*boolean.*cannot.*converted.*int.*"

    def fix(self, line: str, issue: str):

        matched = re.match(self.BOOL_CANNOT_CONVERT_TO_INT_PATTERN, issue)
        if not matched:
            raise NotMatchedConditionError("Issue not matched with pattern")

        # Changed value type to boolean
        matched = re.match(
            r"(.*int\s+[a-zA-Z0-9_\$\[\]\s]+\=\s*)(false|true)(\;.*)", line
        )
        if not matched:
            raise NotMatchedConditionError("The line not matched with pattern")

        if matched.group(2) == "false":
            changed_value = "0"
        else:
            changed_value = "1"

        return matched.group(1) + changed_value + matched.group(3)

