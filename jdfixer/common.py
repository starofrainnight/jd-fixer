# -*- coding: utf-8 -*-


class Issue(object):
    def __init__(self, line_no: int = -1, msg: str = "") -> None:
        self.line_no: int = line_no
        self.msg: str = msg
