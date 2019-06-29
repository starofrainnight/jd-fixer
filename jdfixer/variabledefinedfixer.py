# -*- coding: utf-8 -*-

import re
from abc import ABC, abstractmethod
from .issuelinefixer import IssueLineFixer
from .exceptions import NotMatchedConditionError


class VariableDefinedFixer(IssueLineFixer):
    """Fix java compiler reports variale defined issue

    Fix error: variable count is already defined.
    For example :

    a.java:139: error: variable count is already defined in method checkError()
           int count = element.getAlarmState().getNewAlarmCount();
               ^
    """

    VAR_DEFINED_PATTERN = (
        r".*variable\s+([a-zA-Z0-9_\$]+).*is.*already.*defined"
    )

    def fix(self, line: str, issue: str):
        matched = re.match(self.VAR_DEFINED_PATTERN, issue)
        if not matched:
            raise NotMatchedConditionError("Issue not matched with pattern")

        var_name = matched.group(1)
        # int top = false;
        # final int top = Integer.valueOf(this.txtCountQty.getText());
        # for(int i$ = 0; i$ < len$; ++i$) {
        scope_pat = r"[a-zA-Z0-9_\$\[\]\s]"
        not_scope_pat = r"[^a-zA-Z0-9_\$\[\]\s]"
        pattern = r"(\s*)(?:{scope_pat}+|([^\=]*{not_scope_pat}+){scope_pat}+)\s+({var_name}\s*(?:\=|\;).*)".format(
            scope_pat=scope_pat,
            not_scope_pat=not_scope_pat,
            var_name=re.escape(var_name),
        )

        matched = re.match(pattern, line)
        if not matched:
            raise NotMatchedConditionError("The line not matched with pattern")

        if matched.group(2):
            combined_text = (
                matched.group(1) + matched.group(2) + matched.group(3)
            )
        else:
            combined_text = matched.group(1) + matched.group(3)

        matched = re.match(
            r"{scope_pat}+\;".format(scope_pat=scope_pat), combined_text
        )
        if matched:
            # Remove the line if only have one line variable without
            # value defined.
            return ""
        else:
            return combined_text

