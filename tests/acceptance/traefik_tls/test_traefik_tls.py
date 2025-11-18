# -*- coding: utf-8 -*-
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

"""Module validating the mkinstance + ce_services TLS feature"""

import shlex
import subprocess
import sys
import time
from pathlib import Path
from typing import Callable

import pytest
import requests


@pytest.mark.acceptance()
def test_traefik_tls(execute_spin: Callable, short_tmp_path: str) -> None:
    """
    Test if an instance can be built with enabled TLS and services being
    started properly.
    """
    yaml = "spinfile.yaml"
    test_path = "tests/acceptance/traefik_tls"
    instance_location = f"{short_tmp_path}/sqlite"
    opts = f"-p mkinstance.base.instance_location={instance_location}"
    execute_spin(yaml, short_tmp_path, path=test_path, cmd="cleanup")
    execute_spin(yaml, short_tmp_path, path=test_path, cmd="provision")
    execute_spin(yaml, short_tmp_path, path=test_path, cmd=f"{opts} mkinstance")

    ce_services_cmd = (
        f"spin -p spin.data={short_tmp_path} -C {test_path} "
        f"--env {str(short_tmp_path)} -f {yaml} {opts} ce-services"
    )

    instance_url = "https://localhost:8443"
    max_retries = 60
    retry_interval = 2
    instance_available = False

    with subprocess.Popen(
        shlex.split(ce_services_cmd, posix=sys.platform != "win32"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
    ) as ce_services_process:
        try:
            for _ in range(max_retries):
                try:
                    response = requests.get(
                        instance_url,
                        verify=Path(instance_location) / "certs" / "localhost.crt",
                        timeout=10,
                    )
                    if response.ok:
                        instance_available = True
                        break
                except requests.exceptions.RequestException:
                    pass
                time.sleep(retry_interval)
        finally:
            ce_services_process.terminate()
            try:
                ce_services_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                ce_services_process.kill()
                ce_services_process.wait()

        assert (
            instance_available
        ), f"Instance at {instance_url} did not become available within {max_retries * retry_interval} seconds"  # noqa: E501
