# -*- coding: utf-8 -*-

"""Main module."""

import os.path
from enum import Enum, auto
from fnmatch import fnmatch
from os import PathLike
from typing import List
from pathlib import Path
from subprocess import run
from .dirfixer import DirFixer
from .srcfixer import SrcFixer
from .issuelinefixer import IssueLineFixer
from .conflictpackagedirfixer import ConflictPackageDirFixer
from .variabledefinedfixer import VariableDefinedFixer
from .incompatibleboolfixer import IncompatibleBoolFixer
from .exceptions import NotMatchedConditionError
from .common import Issue
from .fixer import Fixer


class FixingStatus(Enum):
    BEFORE = auto()
    AFTER = auto()
    FAILED = auto()


class FixingContext(object):
    def __init__(
        self,
        status: FixingStatus = FixingStatus.BEFORE,
        fixer: Fixer = None,
        exc: Exception = None,
        target_dir: PathLike = None,
        content: str = "",
        line: str = "",
        issue: str = "",
    ) -> None:
        self._status = status
        self._fixer = fixer
        self._exc = exc
        self._content = content
        self._line = line
        self._issue = issue

    @property
    def fixer(self):
        return self._fixer

    @property
    def status(self):
        return self._status

    @property
    def exc(self):
        return exc

    @property
    def content(self):
        return self._content

    @property
    def line(self):
        return self._line

    @property
    def issue(self):
        return self._issue


class JDFixer(object):
    def __init__(self, target_dir: PathLike) -> None:
        self._dirfixers: List[DirFixer] = list()
        self._srcfixers: List[SrcFixer] = list()
        self._issuelinefixers: List[IssueLineFixer] = list()
        self._target_dir: PathLike = target_dir

        self.register_dirfixer(ConflictPackageDirFixer())
        self.register_issuelinefixer(VariableDefinedFixer())
        self.register_issuelinefixer(IncompatibleBoolFixer())

    @property
    def target_dir(self):
        return self._target_dir

    def register_dirfixer(self, fixer: DirFixer):
        self._dirfixers.append(fixer)

    def register_srcfixer(self, fixer: SrcFixer):
        self._srcfixers.append(fixer)

    def register_issuelinefixer(self, fixer: IssueLineFixer):
        self._issuelinefixers.append(fixer)

    def _get_issues(self, java_file_path):
        p = run(
            ["javac", "-nowarn", "-Xmaxerrs", "9999", java_file_path],
            encoding="utf-8",
            stderr=PIPE,
            stdout=DEVNULL,
        )
        issues = []
        for line in p.stderr.split("\n"):
            # *.java:3: error:*
            matched = re.match(r".*\.java\:(\d+):\s*error\:(.*)", line)
            if matched:
                issues.append(Issue(int(matched.group(1)), matched.group(2)))
        return issues

    def _iterfiles(self):
        for root, __, files in os.walk(self._target_dir, topdown=False):
            for filename in files:
                yield os.path.join(root, filename)

    def iterfix(self):
        for fixer in self._dirfixers:
            yield FixingContext(
                status=FixingStatus.BEFORE,
                fixer=fixer,
                target_dir=self._target_dir,
            )
            fixer.fix(self._target_dir)
            yield FixingContext(
                status=FixingStatus.AFTER,
                fixer=fixer,
                target_dir=self._target_dir,
            )

        for apath in self._iterfiles():
            if not fnmatch(apath, "*.java"):
                continue

            with open(apath, "r", encoding="utf-8") as f:
                content = f.read()

            orig_content = content

            for fixer in self._srcfixers:
                try:
                    yield FixingContext(
                        status=FixingStatus.BEFORE,
                        fixer=fixer,
                        content=content,
                    )
                    content = fixer.fix(context)
                    yield FixingContext(
                        status=FixingStatus.AFTER, fixer=fixer, content=content
                    )

                except NotMatchedConditionError as e:
                    yield FixingContext(
                        status=FixingStatus.FAILED, fixer=fixer, exc=e
                    )

            if content != orig_content:
                with open(apath, "w", encoding="utf-8") as f:
                    content = f.write(content)

        for apath in self._iterfiles():
            if not fnmatch(apath, "*.java"):
                continue

            while True:
                issues = self._get_issues(apath)

                with open(apath, "r", encoding="utf-8") as f:
                    content = f.read()

                orig_content = content
                lines = content.splitlines()
                for issue in issues:
                    line = lines[issue.line_no]
                    orig_line = line
                    for fixer in self._issuelinefixers:
                        try:
                            yield FixingContext(
                                status=FixingStatus.BEFORE,
                                fixer=fixer,
                                line=line,
                                issue=issue.msg,
                            )
                            line = fixer.fix(line, issue.msg)
                            yield FixingContext(
                                status=FixingStatus.AFTER,
                                fixer=fixer,
                                line=line,
                                issue=issue.msg,
                            )
                        except NotMatchedConditionError as e:
                            yield FixingContext(
                                status=FixingStatus.FAILED, fixer=fixer, exc=e
                            )
                            continue

                    if line != orig_line:
                        lines[issue.line_no] = line

                content = "\n".join(lines)

                if content != orig_content:
                    with open(apath, "w", encoding="utf-8") as f:
                        f.write(content)
                else:
                    # Loop until all issues are fixed
                    break

