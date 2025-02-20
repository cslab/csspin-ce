# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2025 CONTACT Software GmbH
# All rights reserved.
# http://www.contact-software.com/
"""
Spin plugin which wrapps the "cdbpkg" command
"""

from spin import config, option, sh, task

defaults = config(
    requires=config(
        spin=[
            "spin_ce.mkinstance",
        ]
    ),
)


@task()
def cdbpkg(
    cfg,
    instance_dir: option("-D", "--instancedir", required=False, type=str),  # noqa: F821
    help: option("--help", is_flag=True),  # pylint: disable=redefined-builtin
    args,
):
    """
    A wrapper for the cdbpkg command
    """
    if help:
        args = (*args, "--help")
    if instance_dir is None:
        instance_dir = cfg.mkinstance.base.instance_location
    sh("cdbpkg", "-D", instance_dir, *args)
