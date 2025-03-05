# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2025 CONTACT Software GmbH
# All rights reserved.
# https://www.contact-software.com/

"""
Spin plugin for the ce_support_tools.
"""

from spin import (
    config,
    option,
    sh,
    task,
)

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
    cfg,
    instancedir: option("-D", "--instancedir", required=False, type=str),  # noqa: F821
    help: option("--help", is_flag=True),  # pylint: disable=redefined-builtin
    args,
):
    """
    Run the pyperf tool with the given arguments.
    """
    if help:
        args = (*args, "--help")
    if instancedir is None:
        instancedir = cfg.mkinstance.base.instance_location
    if args is None or len(args) == 0:
        args = ("--help",)
    sh("powerscript", "-D", instancedir, "-m", "ce.support.pyperf", *args)
