# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 CONTACT Software GmbH
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

"""Module validating the graphviz provisioning"""

import sys
from typing import Callable

import pytest


@pytest.mark.acceptance()
@pytest.mark.wip()
def test_graphviz_provisioning(execute_spin: Callable, short_tmp_path: str) -> None:
    """
    Test if the provisioning of graphviz was successful.
    """
    if sys.platform == "win32":
        # pylint: disable=duplicate-code
        yaml = "spinfile.yaml"
        test_path = "tests/acceptance/graphviz"
        instance_location = f"{short_tmp_path}/sqlite"
        opts = f"-p mkinstance.base.instance_location={instance_location}"
        execute_spin(yaml, short_tmp_path, path=test_path, cmd="cleanup")
        execute_spin(yaml, short_tmp_path, path=test_path, cmd="provision")
        execute_spin(yaml, short_tmp_path, path=test_path, cmd=f"{opts} mkinstance")
        # pylint: enable=duplicate-code

        execute_spin(
            yaml=yaml,
            env=short_tmp_path,
            path=test_path,
            cmd=f"{opts} run powerscript _graphviz.py",
        )
