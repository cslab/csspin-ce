# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2025 CONTACT Software GmbH
# https://www.contact-software.com/
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Spin plugin for the ce_support_tools.
"""

import os

from csspin import config, die, option, setenv, sh, task
from path import Path

defaults = config(
    requires=config(
        python=["ce-support-tools"],
        spin=["csspin_ce.contact_elements", "csspin_ce.mkinstance"],
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
