# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2025 CONTACT Software GmbH
# All rights reserved.
# https://www.contact-software.com/

"""
Spin plugin for the ce_support_tools.
"""

import os

from path import Path
from spin import config, die, option, setenv, sh, task

defaults = config(
    requires=config(
        python=["ce-support-tools"],
        spin=[
            "spin_ce.mkinstance",
        ],
    ),
)


@task()
def pyperf(
    cfg,  # pylint: disable=unused-argument
    instancedir: option("-D", "--instancedir", required=False, type=str),  # noqa: F821
    help: option("--help", is_flag=True),  # pylint: disable=redefined-builtin
    args,
):
    """
    Run the pyperf tool with the given arguments.
    """
    if help:
        args = (*args, "--help")
    if (
        not Path(os.getenv("CADDOK_BASE", "")).is_dir()
        and not (instancedir := Path(instancedir).absolute()).is_dir()
    ):
        die("Can't find the CE instance.")
    if instancedir:
        setenv(CADDOK_BASE=instancedir)
    if args is None or len(args) == 0:
        args = ("--help",)
    sh("powerscript", "-m", "ce.support.pyperf", *args)
