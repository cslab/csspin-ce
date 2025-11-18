# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CONTACT Software GmbH
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

"""Module implementing the integration tests for csspin-ce"""

import shutil
import sys
from typing import Callable

import pytest


@pytest.mark.integration()
@pytest.mark.parametrize("umbrella", ("16.0", "2026.2"))
@pytest.mark.parametrize(
    "plugin", ("ce_services", "mkinstance", "pkgtest", "localize-ce")
)
def test_plugin_provision(
    short_tmp_path: str,
    umbrella: str,
    plugin: str,
    execute_spin: Callable,
) -> None:
    """Provision plugins and run their help command"""
    if (
        plugin == "ce_services"
        and sys.platform != "win32"
        and shutil.which("redis-server") is None
    ):
        pytest.skip(
            "ce_services needs redis-server, which must be preinstalled on Linux"
        )

    yaml = f"{plugin}.yaml"
    opts = " ".join(
        [
            f"-p contact_elements.umbrella={umbrella}",
            f"-p python.index_url=https://packages.contact.de/apps/{umbrella}/+simple/",
        ]
    )
    execute_spin(yaml=yaml, env=short_tmp_path, cmd=f"{opts} cleanup")
    execute_spin(yaml=yaml, env=short_tmp_path, cmd=f"{opts} provision")
    execute_spin(yaml=yaml, env=short_tmp_path, cmd=f"{opts} {plugin} --help")
