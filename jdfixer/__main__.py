#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Console script for jd-fixer."""

import click
from os import PathLike
from .jdfixer import JDFixer


@click.command()
@click.argument("target_dir")
def main(target_dir: PathLike):
    """Console script for jd-fixer."""
    fixer = JDFixer(target_dir)
    for context in fixer.iterfix():
        pass


if __name__ == "__main__":
    main()
