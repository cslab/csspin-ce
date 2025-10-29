# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2021 CONTACT Software GmbH
# All rights reserved.
# https://www.contact-software.com/

"""Module implementing the integration tests for csspin-ce"""

import shlex
import shutil
import subprocess
import sys

import pytest


def execute_spin(yaml, env, path="tests/integration/yamls", cmd=""):
    """Helper function to execute spin and return the output"""
    cmd = f"spin -p spin.data={env} -C {path} --env {str(env)} -f {yaml} " + cmd
    try:
        return subprocess.check_output(
            shlex.split(cmd, posix=sys.platform != "win32"),
            encoding="utf-8",
            stderr=subprocess.PIPE,
        ).strip()
    except subprocess.CalledProcessError as ex:
        print(ex.stdout)
        print(ex.stderr)
        raise


@pytest.mark.integration()
@pytest.mark.parametrize("umbrella", ("16.0", "2026.2"))
@pytest.mark.parametrize("plugin", ("ce_services", "mkinstance", "pkgtest", "localize"))
def test_plugin_provision(short_tmp_path: str, umbrella: str, plugin: str) -> None:
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
